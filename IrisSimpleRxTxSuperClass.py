"""
parameters:

rate                sample rate (Hz)
freq                tx freq (Hz)
bw                  filter bandwidth (Hz)
txGain              tx gain (dB)
rxGain              rx gain (dB)
clockRate           master clock rate (Hz)
rxAnt(arg deleted, as always using "TRX")
txAnt(arg deleted, as always using "TRX")
num_samps           number of samples
replay              if set tx in replay mode
rx_serials_ant      serial number of Iris, an array of strings like "xxx:0", where the last number is channal (in Iris will be 0/1)
tx_serials_antpython
all_used_serials    if you want to control the order of output (seial number), then provide the order you want here, otherwise it'll be random
"""

DEBUG_WITH_FAKESOAPYSDR = False
UseFakeSoapy = False

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
import time

def main_test():  # you could play with this class here
    obj = IrisSimpleRxTxSuperClass(
        rate=10e6, 
        freq=3.6e9, 
        bw=None, 
        txGain=40.0, 
        rxGain=30.0, 
        clockRate=80e6,
        num_samps=1024, 
        replay=False, 
        rx_serials_ant = ['RF3C000045:0'], 
        tx_serials_ant = ['RF3C000045:1']
    )
    obj.setTrigger(["RF3C000045"])
    print("not triggered objects:", obj.tryTrigger())  # if triggered, this will return a empty list
    print(obj.getExtraInfos())  # get temperature information, note that this is for web controller, so may not friendly enough to read
    print(obj.doSimpleRxTx(0.8+0.j))  # get samples received

class IrisSimpleRxTxSuperClass:
    def __init__(self, 
        rate=10e6, 
        freq=3.6e9, 
        bw=None, 
        txGain=40.0, 
        rxGain=30.0, 
        clockRate=80e6, 
        num_samps=1024, 
        replay=False, 
        rx_serials_ant=[], 
        tx_serials_ant=[],
        all_used_serials=None
    ):
        self.sdrs = {}
        self.rx_gains = []
        self.tx_gains = []
        self.num_samps = num_samps
        # deep copy of rx_serials_ant and tx_serials_ant, this is python necessary :)
        self.rx_serials_ant = [ele for ele in rx_serials_ant]
        self.tx_serials_ant = [ele for ele in tx_serials_ant]
        self.rxStreams = []  # index just matched to rx_serials_ant, also does rx_gains
        self.txStreams = []
        self.triggerIrisList = []
        self.all_used_serials = []
        if all_used_serials is not None: elf.all_used_serials = [ele for ele in all_used_serials]
        self.rate = rate  # rate of sampling
        self.released = False

        # first collect what sdr has been included (it's possible that some only use one antenna)
        for ele in self.rx_serials_ant: self.sdrs[IrisSimpleRxTxSuperClass.splitSerialAnt(ele)[0]] = None
        for ele in self.tx_serials_ant: self.sdrs[IrisSimpleRxTxSuperClass.splitSerialAnt(ele)[0]] = None
        # then create SoapySDR objects for these serial numbers, as they are now all 'None' object
        for serial in self.sdrs:
            if serial not in self.all_used_serials:
                self.all_used_serials.append(serial)  # this may be a mistake of user, just recover it
            sdr = SoapySDR.Device(dict(driver="iris", serial=serial))
            self.sdrs[serial] = sdr
            if clockRate is not None: sdr.setMasterClockRate(clockRate)  # set master clock
        self.all_used_serials = [serial for serial in self.all_used_serials if serial in self.sdrs]  # to avoid user input strange serial numbers :)

        # create basic gain settings for tx/rx (surely you can add new "gain" settings or even delete some of them in child class, it's up to you!)
        for serial_ant in self.rx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            default_rx_gains = {
                'LNA2': 15,  # [0,17]
                'LNA1': 20,  # [0,33]
                'ATTN': 0,   # [-18,0]
                'LNA': 25,   # [0,30]
                'TIA': 0,    # [0,12]
                'PGA': 0     # [-12,19]
            }
            self.rx_gains.append(default_rx_gains)
            chan = ant  # TODO: two antenna using two channel! I'm not sure if it works! wy@180804
            sdr = self.sdrs[serial]  # get sdr object reference
            if bw is not None: sdr.setBandwidth(SOAPY_SDR_RX, chan, bw)
            if freq is not None: sdr.setFrequency(SOAPY_SDR_RX, chan, "RF", freq)
            sdr.setAntenna(SOAPY_SDR_RX, chan, "TRX")  # TODO: I assume that in base station given, it only has two TRX antenna but no RX antenna wy@180804
            sdr.setFrequency(SOAPY_SDR_RX, chan, "BB", 0) #don't use cordic
            sdr.setDCOffsetMode(SOAPY_SDR_RX, chan, True) #dc removal on rx
            if rate is not None: sdr.setSampleRate(SOAPY_SDR_RX, chan, rate)
            for key in default_rx_gains:
                sdr.setGain(SOAPY_SDR_RX, chan, key, default_rx_gains[key])
        for serial_ant in self.tx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            default_tx_gains = {
                'ATTN': 0,   # [-18,0] by 3
                'PA1': 15,   # [0|15]
                'PA2': 0,    # [0|15]
                'PA3': 30,   # [0|30]
                'IAMP': 12,  # [0,12]
                'PAD': -30,  # [-52,0]
            }
            self.tx_gains.append(default_tx_gains)
            chan = ant
            sdr = self.sdrs[serial]
            if bw is not None: sdr.setBandwidth(SOAPY_SDR_TX, chan, bw)
            if freq is not None: sdr.setFrequency(SOAPY_SDR_TX, chan, "RF", freq)
            sdr.setAntenna(SOAPY_SDR_TX, chan, "TRX")
            sdr.setFrequency(SOAPY_SDR_TX, chan, "BB", 0) #don't use cordic
            if rate is not None: sdr.setSampleRate(SOAPY_SDR_TX, chan, rate)
            for key in default_tx_gains:
                sdr.setGain(SOAPY_SDR_TX, chan, key, default_tx_gains[key])

        # create rx/tx streams
        for r, serial_ant in enumerate(self.rx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chan = ant  # different ant using different channel
            sdr = self.sdrs[serial]
            stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [chan], {"remote:prot":"tcp", "remote:mtu":"1024"})
            self.rxStreams.append(stream) 
            # np.empty(num_samps).astype(np.complex64)  # not create numpy arrays here, leave this to child class (maybe user could change num_samps at run-time)
        for r, serial_ant in enumerate(self.tx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chan = ant
            sdr = self.sdrs[serial]
            stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, [chan], {"remote:prot":"tcp", "remote:mtu":"1024", "REPLAY":replay})
            self.txStreams.append(stream) 
            # for sdr in self.tx_sdrs: sdr.activateStream(txStream)  # not activate streams, leave it to child class or trigger function in this class

    def doSimpleRxTx(self, precode=0.8+0.j):  # this is just a demo: send sinosuid to all tx, precode is to change the phase of carrier
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, self.num_samps)).transpose() * 1 / self.rate  # time of each point
        tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64) * precode

        # create numpy arrays for receiving
        self.sampsRecv = [np.empty(self.num_samps).astype(np.complex64) for r in range(len(self.rxStreams))]

        # clear out socket buffer from old requests
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sr = sdr.readStream(rxStream, [self.sampsRecv[r][:]], len(self.sampsRecv[r]), timeoutUs = 0)
            while sr.ret != SOAPY_SDR_TIMEOUT and not UseFakeSoapy:
                sr = sdr.readStream(rxStream, [self.sampsRecv[r][:]], len(self.sampsRecv[r]), timeoutUs = 0)
        
        # prepare data for sending
        flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
        for r,txStream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.activateStream(txStream)  # activate it!
            # then send data, make sure that all data is written
            numSent = 0
            while numSent < len(tone):
                sr = sdr.writeStream(txStream, [tone[numSent:]], len(tone)-numSent, flags)
                if sr.ret == -1: print("Error: Bad Write!")
                else: numSent += sr.ret
        
        flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
        # activate all receive stream
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.activateStream(rxStream, flags, 0, len(self.sampsRecv[r]))

        # trigger in the near future
        time.sleep(0.1)
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        time.sleep(0.05)

        # read samples from stream
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            numRecv = 0
            while numRecv < len(self.sampsRecv[r]):
                sr = sdr.readStream(rxStream, [self.sampsRecv[r][numRecv:]], len(self.sampsRecv[r])-numRecv, timeoutUs=int(1e6))
                if sr.ret == -1:
                    print('Error: Bad Read!')
                    return None
                else: numRecv += sr.ret

        # look at any async messages, also deactivate all those stream
        for r,txStream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sr = sdr.readStreamStatus(txStream, timeoutUs=int(1e6))
            print(sr)
            sdr.deactivateStream(txStream)
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.deactivateStream(rxStream)

        return self.sampsRecv

    @staticmethod
    def splitSerialAnt(serial_ant):
        idx = serial_ant.rfind(':')
        if idx == -1: return None
        return (serial_ant[:idx], int(serial_ant[idx+1:]))
    
    def setTrigger(self, triggerIrisList: list):  # the serial number of trigger Iris, I suppose there could be multiple trigger
        # note that in wy@180804 version, the simpleTriggerTxRx function just trigger them one-by-one, not consider the time difference
        # but it will be definately OK if you only use one trigger, obviously
        self.triggerIrisList = [ele for ele in triggerIrisList]  # deep copy
        for serial in self.triggerIrisList:
            if serial in self.sdrs:
                self.sdrs[serial].writeSetting('SYNC_DELAYS', "")
        for serial in self.sdrs:
            self.sdrs[serial].setHardwareTime(0, "TRIG")
    
    def tryTrigger(self):  # test if all the Iris could be trigger by self.triggerIrisList, return the list of not triggered Iris' serial number
        serial_list = [serial for serial in self.sdrs]  # put in a list to avoid random index of dictionary
        timeLastTriggered0 = [self.sdrs[serial].getHardwareTime("TRIGGER") for serial in serial_list]
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        time.sleep(0.1)  # wait for all trigger work
        timeLastTriggered1 = [self.sdrs[serial].getHardwareTime("TRIGGER") for serial in serial_list]
        notTriggered = []
        for i in range(len(timeLastTriggered0)):  # if trigger time not changed, it means it's not triggered
            if timeLastTriggered0[i] == timeLastTriggered1[i]: notTriggered.append(serial_list[i])
        return notTriggered
    
    def __del__(self):
        if not self.released:
            self.close()
    
    def close(self):
        print("Iris close called")
        for r,stream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
        for r,stream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
        self.released = True

    # return anything if cannot change the gain or unknown gainKey, otherwise just return None (or simply do not return)
    def changeGain(self, serial_ant, gainObj, gainKey, gainNewValue):  # note that when using web controller, gainNewValue will always be string!
        # you can overwrite this, but note that you can call IrisSimpleRxTxSuperClass.changeGain(self, xxx) to support basic gain settings without repeat code
        gk = gainKey
        serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        chan = ant
        if serial_ant in self.rx_serials_ant:
            if gk=="LNA2" or gk=="LNA1" or gk=="ATTN" or gk=="LNA" or gk=="TIA" or gk=="PGA":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                except:
                    return None
                sdr.setGain(SOAPY_SDR_RX, chan, gainKey, gainObj[gainKey])
                return True
        elif serial_ant in self.tx_serials_ant:
            if gk=="ATTN" or gk=="PA1" or gk=="PA2" or gk=="PA3" or gk=="IAMP" or gk=="PAD":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                except:
                    return None
                sdr.setGain(SOAPY_SDR_TX, chan, gainKey, gainObj[gainKey])
                return True
        return None

    def updateGains(self, newGain):  # newGain is dict e.t. {"SERIAL:ANT-ATTN": 13} where SERIAL and ANT is defined before
        for key in newGain:
            idx = key.rfind('-')
            if idx == -1:
                print("Error: gain update key is not formatted as 'SERIAL:ANT-ATTN'")
                continue
            serial_ant = key[:idx]
            gainKey = key[idx+1:]
            gainObj = None
            if serial_ant in self.rx_serials_ant: gainObj = self.rx_gains[self.rx_serials_ant.index(serial_ant)]
            if serial_ant in self.tx_serials_ant: gainObj = self.tx_gains[self.tx_serials_ant.index(serial_ant)]
            if gainObj is None:
                print("Error: serial_ant %s is not in rx or tx list" % serial_ant)
                continue
            if self.changeGain(serial_ant, gainObj, gainKey, newGain(key)) is None:
                print("Error: gainKey %s may not supported" % gainKey)

    def getExtraInfos(self):
        info = {}
        for r,serial in enumerate(self.all_used_serials):  # to keep order, that's necessary for using web controller wy@180804
            info["LMS7-%d" % r] = float(self.sdrs[serial].readSensor("LMS7_TEMP"))
            info["Zynq-%d" % r] = float(self.sdrs[serial].readSensor("ZYNQ_TEMP"))
            info["Frontend-%d" % r] = float(self.sdrs[serial].readSensor("FE_TEMP"))
            info["PA0-%d" % r] = float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 0, 'TEMP'))
            info["PA1-%d" % r] = float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 1, 'TEMP'))
        return info
    
    def availableRxGains(self):  # tell user what gains could be adjusted
        ret = []
        for r,ele in self.rx_gains:
            a = []
            for gainElementKey in ele:
                a.append[(self.rx_serials_ant[r], gainElementKey)]
            ret.append(a)
        return ret

    def availableTxGains(self):
        ret = []
        for r,ele in self.tx_gains:
            a = []
            for gainElementKey in ele:
                a.append[(self.tx_serials_ant[r], gainElementKey)]
            ret.append(a)
        return ret

    def nowGains(self):
        return self.rx_gains, self.tx_gains


if __name__=='__main__':
    main_test()
