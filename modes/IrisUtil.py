"""
put public functions here

you should write functions in your class first, if you think they're really common one and should be share, put them here
the function should like this:
    def something(self, foo, bar):
        pass
this make sure that all classes can use these functions, just like their own class function
"""

# import parent folder's file
DEBUG_WITH_FAKESOAPYSDR = False
UseFakeSoapy = False

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import GUI
from HDF5Worker import HDF5Worker

try:
    if DEBUG_WITH_FAKESOAPYSDR: raise Exception("debug")
    import SoapySDR
    from SoapySDR import * #SOAPY_SDR_ constants
except:
    import FakeSoapySDR as SoapySDR  # for me to debug without SoapySDR :)
    from FakeSoapySDR import *
    UseFakeSoapy = True
    print("*** Warning ***: system will work with FakeSoapySDR")

import numpy as np
import time, threading, csv, os


# GUI.log('IrisUtil is loaded')

def Format_UserInputSerialAnts(self):
    if not hasattr(self, "IrisSerialNums"): self.IrisSerialNums = self.main.IrisSerialNums
    serials = self.IrisSerialNums
    self.rx_serials_ant = []
    self.tx_serials_ant = []
    self.trigger_serial = None
    for ele in serials:
        ret = Format_FromSerialAntTRtrigger(ele)
        if ret is None:
            GUI.error("unkown format: %s, ignored" % ele)
        serial, ant, TorR, trigger = ret
        if trigger:
            if self.trigger_serial is None: self.trigger_serial = serial
            else: raise Exception("more than one trigger is not allowed")
        if TorR == 'Rx':
            self.rx_serials_ant.append(serial + '-' + ant)
        elif TorR == 'Tx':
            self.tx_serials_ant.append(serial + '-' + ant)
        else:
            GUI.error("unkown TorR: %s, ignored" % TorR)
    if self.trigger_serial is None:
        raise Exception("must provide at least one trigger Iris")

def Format_FromSerialAntTRtrigger(ele):
    print(ele)
    a = ele.rfind('-')
    if a == -1: return None
    b = ele[:a].rfind('-')
    if b == -1: return None
    c = ele[:b].rfind('-')
    if c == -1: return None
    serial = ele[:c]
    ant = ele[c+1:b]
    TorR = ele[b+1:a]
    trigger = (ele[a+1:] == '1')
    return (serial, ant, TorR, trigger)

def Format_SplitSerialAnt(serial_ant):
    idx = serial_ant.rfind('-')
    if idx == -1: return None
    return (serial_ant[:idx], int(serial_ant[idx+1:]))

def Format_SplitGainKey(self, gainKey):
    a = gainKey.rfind('-')
    if a == -1: return None
    b = gainKey[:a].rfind('-')
    if b == -1: return None
    c = gainKey[:b].rfind('-')
    if c == -1: return None
    serial = gainKey[:c]
    ant = gainKey[c+1:b]
    txrx = gainKey[b+1:a]
    key = gainKey[a+1:]
    if ant != "1" and ant != "0": return None  # only for Iris, two antenna/channel
    if txrx != "rx" and txrx != "tx": return None
    serial_ant = serial + '-' + ant
    gk = key
    if txrx == "rx":
        if gk not in self.rx_gains[gainKey[:a]]: return None
    elif gk not in self.tx_gains[gainKey[:a]]: return None
    return serial_ant, txrx, key

def Format_CheckEndWithHDF5OrAddIt(filename):
    if len(filename) > 5 and filename[-5:] == ".hdf5":
        return filename
    return filename + ".hdf5"

def Format_CheckSerialAntInTx(self, new_serial_ant):
    new_ret = Format_SplitSerialAnt(new_serial_ant)
    if new_ret is None: raise Exception("must format as \"serial-ant\"")
    new_serial, new_ant = new_ret
    ifOK = False
    for serial_ant in self.tx_serials_ant:
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if new_serial == serial:
            if ant == 2:
                if new_ant == 0 or new_ant == 1: ifOK = True
            elif ant == new_ant: ifOK = True
    if ifOK:  # load zero to other tx, load data into specified tx
        self.txSelect = new_serial_ant
        Init_CreateRepeatorOnehotWaveformSequence(self)
        Process_WriteRepeatDataToTxRAM(self)
        return self.txSelect
    raise Exception("cannot find serial-ant pair, please check")

def Format_GetObjectClassName(self):
    s = str(type(self))[:-2]
    fd = s.rfind('.')
    if fd != -1:
        s = s[fd+1:]
    return s

def Format_AddSelfAttr(self, attrs, namelst):
    for name in namelst:
        if hasattr(self, name):
            attrs[name] = getattr(self, name)

def Format_cfloat2uint32(arr, order='IQ'):  # from https://github.com/skylarkwireless/sklk-demos/blob/master/python/SISO.py
    arr_i = (np.real(arr) * 32767).astype(np.uint16)
    arr_q = (np.imag(arr) * 32767).astype(np.uint16)
    if order == 'IQ':
        return np.bitwise_or(arr_q ,np.left_shift(arr_i.astype(np.uint32), 16))
    else:
        return np.bitwise_or(arr_i ,np.left_shift(arr_q.astype(np.uint32), 16))

def Format_LoadWaveFormFile(self, filename):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)) as f:
        reader = csv.reader(f)
        # print(list(reader))
        self.WaveFormData = np.array([[complex(a) for a in row] for row in list(reader)], dtype=np.complex64)
        shape = self.WaveFormData.shape
        GUI.log('load %s with %d×%d array' % (filename, shape[0], shape[1]))

def Assert_ZeroSerialNotAllowed(self):
    if len(self.main.IrisSerialNums) == 0:
        raise Exception("zero serial not allowed")

def Assert_Tx_Required(self):  # call after Format_UserInputSerialAnts
    if len(self.tx_serials_ant) == 0:
        raise Exception("tx serial required")

def Alert_SerialNumsIgnored(self):
    if len(self.main.IrisSerialNums) != 0:
        GUI.alert("serial numbers not allowed")

def Alert_OnlyTorR_OtherIgnored(self, TorR):  # TorR should be "Rx" or "Tx"
    self.IrisSerialNums = []
    for ele in self.main.IrisSerialNums:
        ret = Format_FromSerialAntTRtrigger(ele)
        if ret is None: continue  # leave it to Format_UserInputSerialAnts
        serial, ant, nTorR, trigger = ret
        if nTorR != TorR:
            GUI.alert("serial \"%s\" is not %s so ignore" % (serial, TorR))
        else:
            self.IrisSerialNums.append(ele)

def Init_CreateDefaultGain_WithFrontEnd(self):
    self.default_rx_gains = {
        'LNA2': 15,  # [0,17]
        'LNA1': 20,  # [0,33]
        'ATTN': 0,   # [-18,0]
        'LNA': 25,   # [0,30]
        'TIA': 0,    # [0,12]
        'PGA': 0     # [-12,19]
    }
    self.default_tx_gains = {
        'ATTN': 0,   # [-18,0] by 3
        'PA1': 15,   # [0|15]
        'PA2': 0,    # [0|15]
        'PA3': 30,   # [0|30]
        'IAMP': 12,  # [0,12]
        'PAD': 0,    # [-52,0] ? wy@180805: PAD range is positive to ensure 0 dB is minimum power: Converting PAD value of -30 to 22 dB...
    }

def Init_CreateDefaultGain_WithDevFE(self):
    self.default_rx_gains = {
        "rxGain": 20  # Rx gain (dB)
    }
    self.default_tx_gains = {
        "txGain": 40  # Tx gain (dB)
    }

def Init_CreateDefaultGain_FileAnalyze(self):  # the following arguments will be changed when a file is loaded
    self.tx_gains = {}
    self.rx_gains = {}
    self.tx_serials_ant = []
    self.rx_serials_ant = []

def Init_CollectSDRInstantNeeded(self, clockRate=80e6):
    self.sdrs = {}
    self.odered_serials = []
    self.clockRate = clockRate
    # first collect what sdr has been included (it's possible that some only use one antenna)
    for ele in self.rx_serials_ant + self.tx_serials_ant:
        serial = Format_SplitSerialAnt(ele)[0]
        self.sdrs[serial] = None
        if serial not in self.odered_serials: self.odered_serials.append(serial)
    # then create SoapySDR objects for these serial numbers, as they are now all 'None' object
    for serial in self.sdrs:
        sdr = SoapySDR.Device(dict(driver="iris", serial=serial))
        self.sdrs[serial] = sdr
        if clockRate is not None: sdr.setMasterClockRate(clockRate)  # set master clock
    
def Init_CreateBasicGainSettings(self, rate=None, bw=None, freq=None, dcoffset=None, txrate=None, rxrate=None):
    self.rx_gains = {}  # if rx_serials_ant contains xxx-3-rx-1 then it has "xxx-0-rx" and "xxx-1-rx", they are separate (without trigger option)
    self.tx_gains = {}
    if rate is not None:
        self.txrate = rate
        self.rxrate = rate
    if txrate is not None:
        self.txrate = txrate
    if rxrate is not None:
        self.rxrate = rxrate
    self.bw = bw
    self.freq = freq
    self.dcoffset = dcoffset
    # create basic gain settings for tx/rx (surely you can add new "gain" settings or even delete some of them in child class, it's up to you!)
    for serial_ant in self.rx_serials_ant:
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.rx_gains["%s-0-rx" % serial] = self.default_rx_gains.copy()  # this is a fixed bug, no copy will lead to the same gain
            self.rx_gains["%s-1-rx" % serial] = self.default_rx_gains.copy()
        else:
            self.rx_gains["%s-%d-rx" % (serial, ant)] = self.default_rx_gains.copy()
        sdr = self.sdrs[serial]  # get sdr object reference
        chans = [0, 1] if ant == 2 else [ant]  # if ant is 2, it means [0, 1] both
        for chan in chans:
            if hasattr(self, 'rxrate'): sdr.setSampleRate(SOAPY_SDR_RX, chan, self.rxrate)
            if bw is not None: sdr.setBandwidth(SOAPY_SDR_RX, chan, bw)
            if freq is not None: sdr.setFrequency(SOAPY_SDR_RX, chan, "RF", freq)
            sdr.setAntenna(SOAPY_SDR_RX, chan, "TRX")  # TODO: I assume that in base station given, it only has two TRX antenna but no RX antenna wy@180804
            sdr.setFrequency(SOAPY_SDR_RX, chan, "BB", 0) # don't use cordic
            if dcoffset is not None: sdr.setDCOffsetMode(SOAPY_SDR_RX, chan, dcoffset) # dc removal on rx
            for key in self.default_rx_gains:
                if key == "rxGain":  # this is a special gain value for Iris, just one parameter
                    sdr.setGain(SOAPY_SDR_RX, chan, self.default_rx_gains[key])
                else: sdr.setGain(SOAPY_SDR_RX, chan, key, self.default_rx_gains[key])
    for serial_ant in self.tx_serials_ant:
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.tx_gains["%s-0-tx" % serial] = self.default_tx_gains.copy()
            self.tx_gains["%s-1-tx" % serial] = self.default_tx_gains.copy()
        else:
            self.tx_gains["%s-%d-tx" % (serial, ant)] = self.default_tx_gains.copy()
        sdr = self.sdrs[serial]
        chans = [0, 1] if ant == 2 else [ant]  # if ant is 2, it means [0, 1] both
        for chan in chans:
            if hasattr(self, 'txrate'): sdr.setSampleRate(SOAPY_SDR_TX, chan, self.txrate)
            if bw is not None: sdr.setBandwidth(SOAPY_SDR_TX, chan, bw)
            if freq is not None: sdr.setFrequency(SOAPY_SDR_TX, chan, "RF", freq)
            sdr.setAntenna(SOAPY_SDR_TX, chan, "TRX")
            sdr.setFrequency(SOAPY_SDR_TX, chan, "BB", 0)  # don't use cordic
            for key in self.default_tx_gains:
                if key == "txGain":  # this is a special gain value for Iris, just one parameter
                    sdr.setGain(SOAPY_SDR_TX, chan, self.default_tx_gains[key])
                else: sdr.setGain(SOAPY_SDR_TX, chan, key, self.default_tx_gains[key])

def Init_CreateTxStreams(self):
    self.txStreams = []  # index just matched to tx_serials_ant
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        chans = [0, 1] if ant == 2 else [ant]
        sdr = self.sdrs[serial]
        stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        self.txStreams.append(stream)

def Init_CreateRxStreams(self):
    self.rxStreams = [] # index just matched to rx_serials_ant
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        chans = [0, 1] if ant == 2 else [ant]
        sdr = self.sdrs[serial]
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        self.rxStreams.append(stream) 

def Init_CreateTxRxStreams(self):
    Init_CreateRxStreams(self)
    Init_CreateTxStreams(self)

def Init_CreateTxStreams_RevB(self):
    self.txStreams = []  # index just matched to tx_serials_ant
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        chans = [0, 1] if ant == 2 else [ant]
        sdr = self.sdrs[serial]
        sdr.writeSetting(SOAPY_SDR_TX, 0, 'CALIBRATE', 'SKLK')  # this is from sklk-demos/python/SISO.py wy@180823
        stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        self.txStreams.append(stream)

def Init_CreateRxStreams_RevB(self):
    self.rxStreams = []  # index just matched to rx_serials_ant
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        chans = [0, 1] if ant == 2 else [ant]
        sdr = self.sdrs[serial]
        sdr.writeSetting(SOAPY_SDR_RX, 0, 'CALIBRATE', 'SKLK')  # this is from sklk-demos/python/SISO.py wy@180823
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        self.rxStreams.append(stream) 

def Init_CreateTxRxStreams_RevB(self):
    Init_CreateRxStreams_RevB(self)
    Init_CreateTxStreams_RevB(self)

def Init_SynchronizeTriggerClock(self):
    trigsdr = self.sdrs[self.trigger_serial]
    trigsdr.writeSetting('SYNC_DELAYS', "")
    for serial in self.sdrs: self.sdrs[serial].setHardwareTime(0, "TRIGGER")
    trigsdr.writeSetting("TRIGGER_GEN", "")

def Init_CreateRepeatorSinusoidSequence(self):
    seqlen = len(self.tx_gains) + 2  # how many antennas plus 2
    waveFreq = self.rate / 100  # every period has 100 points
    s_time_vals = np.array(np.arange(0, self.txFrameSize)).transpose() * 1 / self.rate  # time of each point
    tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
    self.tones = []
    idx = 0
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.tones.append([np.zeros(seqlen*self.txFrameSize, dtype=np.complex64), np.zeros(seqlen*self.txFrameSize, dtype=np.complex64)])  # two stream
            self.tones[r][0][idx*self.txFrameSize:(idx+1)*self.txFrameSize] = tone
            self.tones[r][1][(idx+1)*self.txFrameSize:(idx+2)*self.txFrameSize] = tone
            idx += 2
        else:
            self.tones.append([np.zeros(seqlen*self.txFrameSize, dtype=np.complex64)])
            self.tones[r][0][idx*self.txFrameSize:(idx+1)*self.txFrameSize] = tone
            idx += 1

def Init_CreateRepeatorOnehotWaveformSequence(self):  # one-hot send on self.txSelect
    self.WaveFormSignal = np.zeros(4096, dtype=np.complex64)
    self.tones = []
    act_serial, act_ant = Format_SplitSerialAnt(self.txSelect)
    # the given self.WaveFormData is OFDM symbols
    idx = 0
    for i in range(self.WaveFormData.shape[1]):
        symbols = self.WaveFormData[:,i]
        signal = np.fft.ifft(np.fft.ifftshift(symbols)) * 4  # make sure the max signal is under 1
        # add cyclic prefix
        cplen = len(signal) // 10  # 10% prefix
        signal = np.concatenate((signal[len(signal)-cplen:], signal))
        print(np.absolute(signal).max())
        lidx = idx
        idx += len(signal)
        self.WaveFormSignal[lidx:idx] = signal
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.tones.append([np.zeros(4096, dtype=np.complex64), np.zeros(4096, dtype=np.complex64)])  # two stream
        else:
            self.tones.append([np.zeros(4096, dtype=np.complex64)])
        if serial == act_serial:
            if ant == 2:
                self.tones[r][act_ant] = self.WaveFormSignal
            elif ant == act_ant:
                self.tones[r][0] = self.WaveFormSignal

def Deinit_SafeTxStopRepeat(self):
    if hasattr(self, 'sdrs') and self.sdrs is not None:
        for serial in self.sdrs:
            sdr = self.sdrs[serial]
            print('stopping repeating of serial:', serial)
            sdr.writeSetting("TX_REPLAY", '')

def Deinit_SafeDelete(self):
    if hasattr(self, 'rxStreams') and self.rxStreams is not None:
        for r,stream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = Format_SplitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
    if hasattr(self, 'txStreams') and self.txStreams is not None:
        for r,stream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = Format_SplitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
    if hasattr(self, 'sdrs') and self.sdrs is not None:
        for serial in self.sdrs:
            sdr = self.sdrs[serial]
            print('deleting serial:', serial)
            if UseFakeSoapy: sdr.deleteref()  # this is simulation, if you want to delete all references, call it explicitly 

def Extra_GetExtraInfo_WithFrontEnd(self):  # this is for Iris with front-end, the case in base-station
    info = {}
    info["list"] = [ele for ele in self.odered_serials]
    info["data"] = {}
    for serial in self.odered_serials:  # to keep order, that's necessary for using web controller wy@180804
        localinfo = []
        localinfo.append(["LMS7", float(self.sdrs[serial].readSensor("LMS7_TEMP"))])
        localinfo.append(["Zynq", float(self.sdrs[serial].readSensor("ZYNQ_TEMP"))])
        localinfo.append(["Frontend", float(self.sdrs[serial].readSensor("FE_TEMP"))])
        localinfo.append(["PA0", float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 0, 'TEMP'))])
        localinfo.append(["PA1", float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 1, 'TEMP'))])
        info["data"][serial] = localinfo
    return info

def Extra_GetExtraInfo_WithDevFE(self):  # this is for dev front-end, without front amplifier
    info = {}
    info["list"] = [ele for ele in self.odered_serials]
    info["data"] = {}
    for serial in self.odered_serials:  # to keep order, that's necessary for using web controller wy@180804
        localinfo = []
        localinfo.append(["LMS7", float(self.sdrs[serial].readSensor("LMS7_TEMP"))])
        localinfo.append(["Zynq", float(self.sdrs[serial].readSensor("ZYNQ_TEMP"))])
        info["data"][serial] = localinfo
    return info

def Gains_GetBasicGains(self):
    ret = {}
    rxlst = []
    txlst = []
    for serial_ant in self.tx_serials_ant:
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            txlst.append(serial + '-0-tx')
            txlst.append(serial + '-1-tx')
        else:
            txlst.append(serial + '-%d-tx' % ant)
    for serial_ant in self.rx_serials_ant:
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            rxlst.append(serial + '-0-rx')
            rxlst.append(serial + '-1-rx')
        else:
            rxlst.append(serial + '-%d-rx' % ant)
    data = {}
    retlist = []
    for r,name in enumerate(txlst):
        gains = self.tx_gains[name]
        a = []
        for gainElementKey in gains:
            a.append(gainElementKey)
            data[name + '-' + gainElementKey] = str(gains[gainElementKey])
        retlist.append([name, a])
    for r,name in enumerate(rxlst):
        gains = self.rx_gains[name]
        a = []
        for gainElementKey in gains:
            a.append(gainElementKey)
            data[name + '-' + gainElementKey] = str(gains[gainElementKey])
        retlist.append([name, a])
    ret["list"] = retlist
    ret["data"] = data
    return ret

def Gains_SetBasicGains(self, gains):
    for gainKey in gains:
        ret = Format_SplitGainKey(self, gainKey)
        if ret is None: 
            GUI.error("unknown key: " + gainKey)
            continue
        serial_ant, txrx, key = ret
        gainObj = None
        if txrx == 'rx': gainObj = self.rx_gains["%s-%s" % (serial_ant, txrx)]
        else: gainObj = self.tx_gains["%s-%s" % (serial_ant, txrx)]
        Gains_ChangeBasicGains(self, serial_ant, txrx, gainObj, key, gains[gainKey])

# return anything if cannot change the gain or unknown gainKey, otherwise just return None (or simply do not return)
def Gains_ChangeBasicGains(self, serial_ant, txrx, gainObj, gainKey, gainNewValue):  # note that when using web controller, gainNewValue will always be string!
    gk = gainKey
    serial, ant = Format_SplitSerialAnt(serial_ant)
    chan = ant
    sdr = self.sdrs[serial]
    if txrx == "rx":
        if gk=="LNA2" or gk=="LNA1" or gk=="ATTN" or gk=="LNA" or gk=="TIA" or gk=="PGA" or gk == "rxGain":
            try:
                gainObj[gainKey] = int(gainNewValue)
                if gk == "rxGain": sdr.setGain(SOAPY_SDR_RX, chan, gainObj[gainKey])  # this is special, only one parameter
                else: sdr.setGain(SOAPY_SDR_RX, chan, gainKey, gainObj[gainKey])
            except Exception as e:
                GUI.error(str(e))
                return None
            return True
        if hasattr(self, 'rxGainKeyException'): return self.rxGainKeyException(self, gainKey, newValue=gainNewValue, gainObj=gainObj)
    elif txrx == "tx":
        if gk=="ATTN" or gk=="PA1" or gk=="PA2" or gk=="PA3" or gk=="IAMP" or gk=="PAD" or gk == "txGain":
            try:
                gainObj[gainKey] = int(gainNewValue)
                if gk == "txGain": sdr.setGain(SOAPY_SDR_TX, chan, gainObj[gainKey])  # this is special, only one parameter
                else: sdr.setGain(SOAPY_SDR_TX, chan, gainKey, gainObj[gainKey])
            except Exception as e:
                GUI.error(str(e))
                return None
            return True
        if hasattr(self, 'txGainKeyException'): return self.txGainKeyException(self, gainKey, newValue=gainNewValue, gainObj=gainObj)
    return None

def Gains_NoGainKeyException(self, gainKey, newValue, gainObj):
    return None  # do nothing

def Gains_GainKeyException_TxPrecode(self, gainKey, newValue, gainObj):
    if gainKey == "precode":
        try:
            gainObj["precode"] = complex(newValue)
        except ValueError:
            GUI.error("cannot convert to complex number: " + newValue)
            return None
        return True
    return None

def Gains_GainKeyException_RxPostcode(self, gainKey, newValue, gainObj):
    if gainKey == "postcode":
        try:
            gainObj["postcode"] = complex(newValue)
        except ValueError:
            GUI.error("cannot convert to complex number: " + newValue)
            return None
        return True
    return None

def Gains_LoadGainKeyException(self, rxGainKeyException=Gains_NoGainKeyException, txGainKeyException=Gains_NoGainKeyException):
    self.rxGainKeyException = rxGainKeyException
    self.txGainKeyException = txGainKeyException

def Gains_HandleSelfParameters(self, gains):
    if not hasattr(self, "selfparameters"): return
    toDelete = []
    paralen = len("parameters-")
    for gainKey in gains:
        if gainKey[:paralen] == "parameters-":
            key = gainKey[paralen:]
            toDelete.append(gainKey)
            if key in self.selfparameters:
                parser = self.selfparameters[key]
                self.__dict__[key] = parser(gains[gainKey])
    for key in toDelete: gains.pop(key)

def Gains_AddParameter(self, ret=None):
    if ret is None:  # if doesn't provide, just create a empty one
        ret = {
            "list": [],
            "data": {}
        }
    names = [key for key in self.selfparameters]
    ret["list"].insert(0, ["parameters", names])  # random order, but OK
    for name in names:
        ret["data"]["parameters-" + name] = str(self.__dict__[name])

def Gains_AddPostcodeGains(self):
    for key in self.rx_gains: 
        self.rx_gains[key]["postcode"] = 1.+0.j  # I don't known how to name it >.< see "postProcessRxSamples" below

def Gains_AddPrecodePostcodeGains(self):
    for key in self.tx_gains:  # add precode 'gain' :)
        self.tx_gains[key]["precode"] = 1.+0.j  
    Gains_AddPostcodeGains(self)

def Process_BuildTxTones_Sinusoid(self):
    waveFreq = self.rate / 100  # every period has 100 points
    s_time_vals = np.array(np.arange(0, self.numSamples)).transpose() * 1 / self.rate  # time of each point
    tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
    self.tones = []
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.tones.append([tone * complex(self.tx_gains[serial + '-0-tx']["precode"]), tone * complex(self.tx_gains[serial + '-1-tx']["precode"])])  # two stream
        else:
            self.tones.append([tone * complex(self.tx_gains[serial_ant + '-tx']["precode"])])

def Process_CreateReceiveBuffer(self):
    self.sampsRecv = []
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        chans = [0, 1] if ant == 2 else [ant]
        if ant == 2:
            self.sampsRecv.append([np.zeros(self.numSamples, np.complex64), np.zeros(self.numSamples, np.complex64)])
        else:
            self.sampsRecv.append([np.zeros(self.numSamples, np.complex64)])

def Process_ClearStreamBuffer(self):  # clear out socket buffer from old requests, call after Process_CreateReceiveBuffer
    for r, rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sr = sdr.readStream(rxStream, self.sampsRecv[r], len(self.sampsRecv[r][0]), timeoutUs = 0)
        while sr.ret != SOAPY_SDR_TIMEOUT and not UseFakeSoapy:
            sr = sdr.readStream(rxStream, self.sampsRecv[r], len(self.sampsRecv[r][0]), timeoutUs = 0)

def Process_TxActivate_WriteFlagAndDataToTxStream(self):
    flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
    for r, txStream in enumerate(self.txStreams):
        serial_ant = self.tx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sdr.activateStream(txStream)  # activate it!
        # then send data, make sure that all data is written
        numSent = 0
        while numSent < len(self.tones[r]):
            sr = sdr.writeStream(txStream, [tone[numSent:] for tone in self.tones[r]], len(self.tones[r][0])-numSent, flags)
            if sr.ret == -1:
                GUI.error("Error: Bad Write!")
            else: numSent += sr.ret

def Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0):  # by default: 10ms delay
    self.delay = delay
    self.ts = self.sdrs[self.trigger_serial].getHardwareTime() + delay  # give us delay ns to set everything up.
    if alignment != 0:  # alignment, self.alignOffset needed
        self.ts = ((self.ts + alignment) // alignment) * alignment + self.alignOffset

def Process_TxActivate_WriteFlagAndDataToTxStream_UseHasTime(self):
    flags = SOAPY_SDR_HAS_TIME | SOAPY_SDR_END_BURST
    for r,txStream in enumerate(self.txStreams):
        serial_ant = self.tx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sdr.activateStream(txStream)  # activate it!
        numSent = 0
        while numSent < len(self.tones[r]):
            sr = sdr.writeStream(txStream, [tone[numSent:] for tone in self.tones[r]], len(self.tones[r][0])-numSent, flags, timeNs=self.ts)
            if sr.ret == -1:
                GUI.error("Error: Bad Write!")
            else: numSent += sr.ret

def Process_TxActivate_WriteFlagAndDataToTxStream_RepeatFlag(self):
    # this is from https://github.com/skylarkwireless/sklk-demos/blob/master/python/SISO.py
    replay_addr = 0
    max_replay = 4096  # TODO: read from hardware
    replay_len = len(self.tones[0][0])  # assume they are all the same
    if replay_len > max_replay:
        replay_len = max_replay
        GUI.alert("Continuous mode signal must be less than %d samples. Using first %d samples." % (max_replay, max_replay))
    zeroseq = np.zeros(replay_len, dtype=np.complex64)  # for backup
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        if ant == 2:
            sdr.writeRegisters('TX_RAM_A', replay_addr, Format_cfloat2uint32(self.tones[r][0][:replay_len]).tolist())
            sdr.writeRegisters('TX_RAM_B', replay_addr, Format_cfloat2uint32(self.tones[r][1][:replay_len]).tolist())
        elif ant == 0:
            sdr.writeRegisters('TX_RAM_A', replay_addr, Format_cfloat2uint32(self.tones[r][0][:replay_len]).tolist())
            sdr.writeRegisters('TX_RAM_B', replay_addr, Format_cfloat2uint32(zeroseq).tolist())  # TODO: check whether this is needed
        elif ant == 1:
            sdr.writeRegisters('TX_RAM_A', replay_addr, Format_cfloat2uint32(zeroseq).tolist())  # TODO: check whether this is needed
            sdr.writeRegisters('TX_RAM_B', replay_addr, Format_cfloat2uint32(self.tones[r][0][:replay_len]).tolist())
        sdr.writeSetting("TX_REPLAY", str(replay_len))

def Process_WriteRepeatDataToTxRAM(self):
    replay_addr = 0
    for r, serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        if ant == 2:
            sdr.writeRegisters('TX_RAM_A', replay_addr, Format_cfloat2uint32(self.tones[r][0][:]).tolist())
            sdr.writeRegisters('TX_RAM_B', replay_addr, Format_cfloat2uint32(self.tones[r][1][:]).tolist())
        elif ant == 0:
            sdr.writeRegisters('TX_RAM_A', replay_addr, Format_cfloat2uint32(self.tones[r][0][:]).tolist())
        elif ant == 1:
            sdr.writeRegisters('TX_RAM_B', replay_addr, Format_cfloat2uint32(self.tones[r][0][:]).tolist())

def Process_RxActivate_WriteFlagToRxStream(self):
    flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
    # activate all receive stream
    for r,rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sdr.activateStream(rxStream, flags, 0, len(self.sampsRecv[r][0]))

def Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 57):
    rx_delay_ns = SoapySDR.ticksToTimeNs(rx_delay, self.rate) if rx_delay != 0 else 0
    ts = self.ts + rx_delay_ns  # rx is a bit after tx
    flags = SOAPY_SDR_HAS_TIME | SOAPY_SDR_END_BURST
    # activate all receive stream
    for r,rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sdr.activateStream(rxStream, flags, ts, len(self.sampsRecv[r][0]))

def Process_GenerateTrigger(self):
    self.sdrs[self.trigger_serial].writeSetting("TRIGGER_GEN", "")

def Process_WaitForTime_NoTrigger(self):
    hw_time = self.sdrs[self.trigger_serial].getHardwareTime()
    if self.ts > hw_time: time.sleep((self.ts - hw_time) / 1e9)  # otherwise do not sleep

def Process_ReadFromRxStream(self):
    for r,rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        numRecv = 0
        while numRecv < len(self.sampsRecv[r][0]):
            sr = sdr.readStream(rxStream, [samps[numRecv:] for samps in self.sampsRecv[r]], len(self.sampsRecv[r][0])-numRecv, timeoutUs=int(1e6))
            if sr.ret == -1:
                GUI.error('Error: Bad Read!')
                break  # always break because it cannot recover for most of time
            else: numRecv += sr.ret

def Thread_ReceiveStream(sdr, stream, sampsRecv):
    numRecv = 0
    while numRecv < len(sampsRecv[0]):
        sr = sdr.readStream(stream, [samps[numRecv:] for samps in sampsRecv], len(sampsRecv[0])-numRecv, timeoutUs=int(1e6))
        if sr.ret == -1:
            GUI.error('Error: Bad Read!')
            break  # always break because it cannot recover for most of time
        else: numRecv += sr.ret

def Process_ReadFromRxStream_MultiThread(self):
    ths = []
    for r,rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        t = threading.Thread(target=Thread_ReceiveStream, args=(sdr, rxStream, self.sampsRecv[r]))
        t.setDaemon(False)  # set this thread to daemon thread
        t.start()
        ths.append(t)
    for t in ths:
        t.join()  # wait them to finish

def Process_TxDeactive(self):
    for r,txStream in enumerate(self.txStreams):
        serial_ant = self.tx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sr = sdr.readStreamStatus(txStream, timeoutUs=int(1e6))
        sdr.deactivateStream(txStream)

def Process_RxDeactive(self):
    for r,rxStream in enumerate(self.rxStreams):
        serial_ant = self.rx_serials_ant[r]
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sdr = self.sdrs[serial]
        sdr.deactivateStream(rxStream)

def Process_HandlePostcode(self):
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.sampsRecv[r][0] *= complex(self.rx_gains[serial + "-0-rx"]["postcode"])
            self.sampsRecv[r][1] *= complex(self.rx_gains[serial + "-1-rx"]["postcode"])
        else:
            self.sampsRecv[r][0] *= complex(self.rx_gains[serial + "-%d-rx" % ant]["postcode"])  # received samples

def Process_DoCorrelation2FindFirstPFDMSymbol(self):
    symbols = self.WaveFormData[:,0]
    upsample = int(self.rxrate / self.txrate)
    up_zeros = np.zeros(len(symbols) // 2 * (upsample-1))
    upsymbols = np.concatenate((up_zeros, symbols ,up_zeros))
    refsignal = np.fft.ifft(np.fft.ifftshift(upsymbols))
    self.correlationSampes = {}
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.correlationSampes["corr_%s-0" % serial] = np.correlate(self.sampsRecv[r][0], refsignal, mode='same')  # by default is 'full' which is M+N-1 points
            self.correlationSampes["corr_%s-1" % serial] = np.correlate(self.sampsRecv[r][1], refsignal, mode='same')
        else:
            self.correlationSampes["corr_%s-%d" % (serial, ant)] = np.correlate(self.sampsRecv[r][0], refsignal, mode='same')

def Process_InitHDF5File_RxOnlyBurst(self):
    name = self.fileName
    if name == "":
        mst = str((int(time.time() * 1000) % 1000) + 1000)[1:]
        name = Format_GetObjectClassName(self) + '_' + time.strftime("%Y-%m-%d_%H-%M-%S_", time.localtime()) + mst + '.hdf5'
    print(name)
    self.worker = HDF5Worker(name, "w")
    attrs = {
        "Description": "record by class \"%s\" of ArgosWebGui GitHub project" % Format_GetObjectClassName(self),
        "CreateTime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }
    Format_AddSelfAttr(self, attrs, ['clockRate', 'rate', 'freq', 'bw', 'dcoffset', 'numSamples'])  # add self attributes to attrs
    # create dataset in hdf5
    self.dsetnames = []
    for r, serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            self.dsetnames.append("%s-0" % serial)
            self.dsetnames.append("%s-1" % serial)
        else:
            self.dsetnames.append("%s-%d" % (serial, ant))
    dsetnamestr = self.dsetnames[0]
    for i in range(1, len(self.dsetnames)): dsetnamestr += ' ' + self.dsetnames[i]
    attrs["IQnames"] = dsetnamestr
    self.worker.Write_Attr(attrs)
    self.dset = self.worker.create_dataset("rawIQ", (len(self.dsetnames), self.numSamples), dtype='<c8')  # complex-floating point, single resolution

def Process_SaveHDF5File_RxOnlyBurst(self):
    i = 0
    for r,serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        sampsRecv = self.sampsRecv[r]
        if ant == 2:
            self.dset[i][:] = sampsRecv[0]
            self.dset[i+1][:] = sampsRecv[1]
            i += 2
        else:
            self.dset[i][:] = sampsRecv[0]
            i += 1

def Interface_UpdateUserGraph(self, addition=None):  # addition should be a map object
    struct = []
    for r,serial_ant in enumerate(self.tx_serials_ant + self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        if ant == 2:
            struct.append(serial + '-0')
            struct.append(serial + '-1')
        else:
            struct.append(serial_ant)
    data = {}
    for r,serial_ant in enumerate(self.tx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        cdat = [(tone[:self.showSamples] if len(tone) > self.showSamples else tone) for tone in self.tones[r]]
        if ant == 2:
            for antt in [0,1]:
                data["I-%s-%d" % (serial, antt)] = [float(e.real) for e in cdat[antt]]
                data["Q-%s-%d" % (serial, antt)] = [float(e.imag) for e in cdat[antt]]
        else:
            data["I-" + serial_ant] = [float(e.real) for e in cdat[0]]
            data["Q-" + serial_ant] = [float(e.imag) for e in cdat[0]]
    for r,serial_ant in enumerate(self.rx_serials_ant):
        serial, ant = Format_SplitSerialAnt(serial_ant)
        cdat = [(samps[:self.showSamples] if len(samps) > self.showSamples else samps) for samps in self.sampsRecv[r]]
        if ant == 2:
            for antt in [0,1]:
                data["I-%s-%d" % (serial, antt)] = [float(e.real) for e in cdat[antt]]
                data["Q-%s-%d" % (serial, antt)] = [float(e.imag) for e in cdat[antt]]
        else:
            data["I-" + serial_ant] = [float(e.real) for e in cdat[0]]
            data["Q-" + serial_ant] = [float(e.imag) for e in cdat[0]]
    # if has additional graphs, just append them
    if addition is not None:
        for key in addition:
            struct.append(key)
            cdat = addition[key][:self.showSamples] if len(addition[key]) > self.showSamples else addition[key]
            data["I-" + key] = [float(e.real) for e in cdat]
            data["Q-" + key] = [float(e.imag) for e in cdat]
    self.main.sampleData = {"struct": struct, "data": data}
    self.main.sampleDataReady = True

def Analyze_LoadHDF5FileByName(self, filename):
    print("loading %s" % filename)
    return filename
