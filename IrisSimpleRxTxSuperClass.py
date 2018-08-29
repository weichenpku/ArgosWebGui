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
rx_serials_ant      serial number of Iris, an array of strings like "xxx:0", where the last number is channal (in Iris will be 0/1)
tx_serials_antpython
odered_serials    if you want to control the order of output (seial number), then provide the order you want here, otherwise it'll be random
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
        clockRate=80e6,
        rx_serials_ant = ['RF3C000034-2'],
        tx_serials_ant = []
    )
    obj.setTrigger(["RF3C000034"])
    print("not triggered objects:", obj.tryTrigger())  # if triggered, this will return a empty list
    # print("not triggered objects:", obj.tryTrigger())  # if triggered, this will return a empty list
    # print("not triggered objects:", obj.tryTrigger())  # if triggered, this will return a empty list
    # print(obj.getExtraInfos())  # get temperature information, note that this is for web controller, so may not friendly enough to read
    # ret = obj.doSimpleRxTx(1024)  # get samples received
    # print(ret)
    # print(obj.nowGains())
    # from helperfuncs import ModifyQueue
    # queue = ModifyQueue()
    # queue.enqueue("0274-0-rx-LNA2", "10")
    # queue.enqueue("0274-1-tx-ATTN", "5")
    # dic = {}
    # while not queue.empty():
    #     a = queue.dequeue()
    #     dic[a[0]] = a[1]
    # obj.setGains(dic)


class IrisSimpleRxTxSuperClass:
    def __init__(self, 
        rate=10e6, 
        freq=3.6e9, 
        bw=None, 
        clockRate=80e6,
        rx_serials_ant=[], 
        tx_serials_ant=[],
        dcoffset = True
    ):
        self.sdrs = {}
        self.rx_gains = {}  # if rx_serials_ant contains xxx-3-rx-1 then it has "xxx-0-rx" and "xxx-1-rx", they are separate (without trigger option)
        self.tx_gains = {}
        # deep copy of rx_serials_ant and tx_serials_ant, this is python necessary :)
        self.rx_serials_ant = [ele for ele in rx_serials_ant]
        self.tx_serials_ant = [ele for ele in tx_serials_ant]
        self.rxStreams = []  # index just matched to rx_serials_ant
        self.txStreams = []
        if not hasattr(self, 'triggerIrisList'): self.triggerIrisList = []
        self.odered_serials = []
        self.rate = rate  # rate of sampling

        # first collect what sdr has been included (it's possible that some only use one antenna)
        for ele in self.rx_serials_ant: self.sdrs[IrisSimpleRxTxSuperClass.splitSerialAnt(ele)[0]] = None
        for ele in self.tx_serials_ant: self.sdrs[IrisSimpleRxTxSuperClass.splitSerialAnt(ele)[0]] = None
        # then create SoapySDR objects for these serial numbers, as they are now all 'None' object
        for serial in self.sdrs:
            if serial not in self.odered_serials:
                self.odered_serials.append(serial)  # this may be a mistake of user, just recover it
            sdr = SoapySDR.Device(dict(driver="iris", serial=serial))
            self.sdrs[serial] = sdr
            if clockRate is not None: sdr.setMasterClockRate(clockRate)  # set master clock
        # self.odered_serials = [serial for serial in self.odered_serials if serial in self.sdrs]  # to avoid user input strange serial numbers :)

        if not hasattr(self, 'default_rx_gains'):  # could be set by child class before super.init
            self.default_rx_gains = {
                'LNA2': 15,  # [0,17]
                'LNA1': 20,  # [0,33]
                'ATTN': 0,   # [-18,0]
                'LNA': 25,   # [0,30]
                'TIA': 0,    # [0,12]
                'PGA': 0     # [-12,19]
            }
        if not hasattr(self, 'default_tx_gains'):  # could be set by child class before super.init
            self.default_tx_gains = {
                'ATTN': 0,   # [-18,0] by 3
                'PA1': 15,   # [0|15]
                'PA2': 0,    # [0|15]
                'PA3': 30,   # [0|30]
                'IAMP': 12,  # [0,12]
                'PAD': 0,  # [-52,0] ? wy@180805: PAD range is positive to ensure 0 dB is minimum power: Converting PAD value of -30 to 22 dB...
            }

        # create basic gain settings for tx/rx (surely you can add new "gain" settings or even delete some of them in child class, it's up to you!)
        for serial_ant in self.rx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                self.rx_gains["%s-0-rx" % serial] = self.default_rx_gains.copy()  # this is a fixed bug, no copy will lead to the same gain
                self.rx_gains["%s-1-rx" % serial] = self.default_rx_gains.copy()
            else:
                self.rx_gains["%s-%d-rx" % (serial, ant)] = self.default_rx_gains.copy()
            sdr = self.sdrs[serial]  # get sdr object reference
            chans = [0, 1] if ant == 2 else [ant]  # if ant is 2, it means [0, 1] both
            for chan in chans:
                if rate is not None: sdr.setSampleRate(SOAPY_SDR_RX, chan, rate)
                if bw is not None: sdr.setBandwidth(SOAPY_SDR_RX, chan, bw)
                if freq is not None: sdr.setFrequency(SOAPY_SDR_RX, chan, "RF", freq)
                sdr.setAntenna(SOAPY_SDR_RX, chan, "TRX")  # TODO: I assume that in base station given, it only has two TRX antenna but no RX antenna wy@180804
                sdr.setFrequency(SOAPY_SDR_RX, chan, "BB", 0) # don't use cordic
                sdr.setDCOffsetMode(SOAPY_SDR_RX, chan, dcoffset) # dc removal on rx
                for key in self.default_rx_gains:
                    if key == "rxGain":  # this is a special gain value for Iris, just one parameter
                        sdr.setGain(SOAPY_SDR_RX, chan, self.default_rx_gains[key])
                    else: sdr.setGain(SOAPY_SDR_RX, chan, key, self.default_rx_gains[key])
        for serial_ant in self.tx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                self.tx_gains["%s-0-tx" % serial] = self.default_tx_gains.copy()
                self.tx_gains["%s-1-tx" % serial] = self.default_tx_gains.copy()
            else:
                self.tx_gains["%s-%d-tx" % (serial, ant)] = self.default_tx_gains.copy()
            sdr = self.sdrs[serial]
            chans = [0, 1] if ant == 2 else [ant]  # if ant is 2, it means [0, 1] both
            for chan in chans:
                if rate is not None: sdr.setSampleRate(SOAPY_SDR_TX, chan, rate)
                if bw is not None: sdr.setBandwidth(SOAPY_SDR_TX, chan, bw)
                if freq is not None: sdr.setFrequency(SOAPY_SDR_TX, chan, "RF", freq)
                sdr.setAntenna(SOAPY_SDR_TX, chan, "TRX")
                sdr.setFrequency(SOAPY_SDR_TX, chan, "BB", 0)  # don't use cordic
                for key in self.default_tx_gains:
                    if key == "txGain":  # this is a special gain value for Iris, just one parameter
                        sdr.setGain(SOAPY_SDR_TX, chan, self.default_tx_gains[key])
                    else: sdr.setGain(SOAPY_SDR_TX, chan, key, self.default_tx_gains[key])

        # create rx/tx streams
        for r, serial_ant in enumerate(self.rx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chans = [0, 1] if ant == 2 else [ant]
            sdr = self.sdrs[serial]
            stream = self.rxStreamSetup(sdr, chans)
            self.rxStreams.append(stream) 
            # np.empty(num_samps).astype(np.complex64)  # not create numpy arrays here, leave this to child class (maybe user could change num_samps at run-time)
        for r, serial_ant in enumerate(self.tx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chans = [0, 1] if ant == 2 else [ant]
            sdr = self.sdrs[serial]
            stream = self.txStreamSetup(sdr, chans)
            self.txStreams.append(stream) 
            # for sdr in self.tx_sdrs: sdr.activateStream(txStream)  # not activate streams, leave it to child class or trigger function in this class

    def rxStreamSetup(self, sdr, chans):
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        return stream
    
    def txStreamSetup(self, sdr, chans):
        stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        return stream

    def buildTxTones(self, num_samps):
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, num_samps)).transpose() * 1 / self.rate  # time of each point
        tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
        tones = []
        for r, serial_ant in enumerate(self.tx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                tones.append([tone, tone])  # two stream
            else:
                tones.append([tone])
        return tones  # send all sinosuid wave
    
    def postProcessRxSamples(self):
        for r,rxStream in enumerate(self.rxStreams):
            sampsRecv = self.sampsRecv[r]  # received samples, it a list of 1 or 2
            # do nothing here, if you want to modify received stream (for example, to practice the process of recognize pilot and )

    def doSimpleRxTx(self, num_samps, breakWhenBadRW = True):  # this is just a demo: send sinosuid to all tx
        tones = self.buildTxTones(num_samps)  # build tx samples

        # create numpy arrays for receiving
        self.sampsRecv = []
        for r, serial_ant in enumerate(self.rx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chans = [0, 1] if ant == 2 else [ant]
            if ant == 2:
                self.sampsRecv.append([np.zeros(num_samps, np.complex64), np.zeros(num_samps, np.complex64)])
            else:
                self.sampsRecv.append([np.zeros(num_samps, np.complex64)])

        # clear out socket buffer from old requests
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sr = sdr.readStream(rxStream, self.sampsRecv[r], len(self.sampsRecv[r][0]), timeoutUs = 0)
            while sr.ret != SOAPY_SDR_TIMEOUT and not UseFakeSoapy:
                sr = sdr.readStream(rxStream, self.sampsRecv[r], len(self.sampsRecv[r][0]), timeoutUs = 0)

        # prepare data for sending, if child class define the function, just call it, otherwise use the default one
        if hasattr(self, "prepareTx"):
            self.prepareTx(tones)
        else:
            flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
            for r,txStream in enumerate(self.txStreams):
                serial_ant = self.tx_serials_ant[r]
                serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
                sdr = self.sdrs[serial]
                sdr.activateStream(txStream)  # activate it!
                # then send data, make sure that all data is written
                numSent = 0
                while numSent < len(tones[r]):
                    sr = sdr.writeStream(txStream, [tone[numSent:] for tone in tones[r]], len(tones[r][0])-numSent, flags)
                    if sr.ret == -1:
                        print("Error: Bad Write!")
                        if breakWhenBadRW: break
                    else: numSent += sr.ret
        
        # prepare stream for receiving, if child class define the function, just call it, otherwise use the default one
        if hasattr(self, "prepareRx"):
            self.prepareRx()
        else:
            flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
            # activate all receive stream
            for r,rxStream in enumerate(self.rxStreams):
                serial_ant = self.rx_serials_ant[r]
                serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
                sdr = self.sdrs[serial]
                sdr.activateStream(rxStream, flags, 0, len(self.sampsRecv[r][0]))

        if hasattr(self, "triggerProcess"):
            self.triggerProcess()
        else:
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
            while numRecv < len(self.sampsRecv[r][0]):
                sr = sdr.readStream(rxStream, [samps[numRecv:] for samps in self.sampsRecv[r]], len(self.sampsRecv[r][0])-numRecv, timeoutUs=int(1e6))
                if sr.ret == -1:
                    print('Error: Bad Read!')
                    if breakWhenBadRW: break
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

        self.postProcessRxSamples()  # post-handle received data

        return ((self.tx_serials_ant, tones), (self.rx_serials_ant, self.sampsRecv))  # together with transmit arrays

    @staticmethod
    def splitSerialAnt(serial_ant):
        idx = serial_ant.rfind('-')
        if idx == -1: return None
        return (serial_ant[:idx], int(serial_ant[idx+1:]))
    
    def rxGainKeyException(self, gainKey, newValue=None, gainObj=None):  # for DIY gain key
        # do other setting works here
        # return True if you update the new 'gain' successfully
        return None
    
    def txGainKeyException(self, gainKey, newValue=None, gainObj=None):  # for DIY gain key
        # do other setting works here
        # return True if you update the new 'gain' successfully
        return None

    def splitGainKey(self, gainKey):
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
        # index = -1
        # if txrx == "rx": index = self.rx_serials_ant.index(serial_ant)  # this step consume linear time! but always antenna is under 20 elements I guessssssss......
        # else: index = self.tx_serials_ant.index(serial_ant)
        # if index == -1: return None
        gk = key
        if txrx == "rx":
            if gk not in self.rx_gains[gainKey[:a]]: return None
        elif gk not in self.tx_gains[gainKey[:a]]: return None
        return serial_ant, txrx, key
    
    # return anything if cannot change the gain or unknown gainKey, otherwise just return None (or simply do not return)
    def changeGain(self, serial_ant, txrx, gainObj, gainKey, gainNewValue):  # note that when using web controller, gainNewValue will always be string!
        # you can overwrite this, but note that you can call IrisSimpleRxTxSuperClass.changeGain(self, xxx) to support basic gain settings without repeat code
        gk = gainKey
        serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        chan = ant
        sdr = self.sdrs[serial]
        if txrx == "rx":
            if gk=="LNA2" or gk=="LNA1" or gk=="ATTN" or gk=="LNA" or gk=="TIA" or gk=="PGA" or gk == "rxGain":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                    if gk == "rxGain": sdr.setGain(SOAPY_SDR_RX, chan, gainObj[gainKey])  # this is special, only one parameter
                    else: sdr.setGain(SOAPY_SDR_RX, chan, gainKey, gainObj[gainKey])
                except:
                    return None
                return True
            return self.rxGainKeyException(gainKey, newValue=gainNewValue, gainObj=gainObj)
        elif txrx == "tx":
            if gk=="ATTN" or gk=="PA1" or gk=="PA2" or gk=="PA3" or gk=="IAMP" or gk=="PAD" or gk == "txGain":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                    if gk == "txGain": sdr.setGain(SOAPY_SDR_TX, chan, gainObj[gainKey])  # this is special, only one parameter
                    else: sdr.setGain(SOAPY_SDR_TX, chan, gainKey, gainObj[gainKey])
                except:
                    return None
                return True
            return self.txGainKeyException(gainKey, newValue=gainNewValue, gainObj=gainObj)
        return None
    
    def setTrigger(self, triggerIrisList: list):  # the serial number of trigger Iris, I suppose there could be multiple trigger
        # note that in wy@180804 version, the simpleTriggerTxRx function just trigger them one-by-one, not consider the time difference
        # but it will be definately OK if you only use one trigger, obviously
        self.triggerIrisList = [ele for ele in triggerIrisList]  # deep copy
        for serial in self.triggerIrisList:
            if serial in self.sdrs:
                self.sdrs[serial].writeSetting('SYNC_DELAYS', "")
    
    def tryTrigger(self):  # test if all the Iris could be trigger by self.triggerIrisList, return the list of not triggered Iris' serial number
        for serial in self.sdrs:
            self.sdrs[serial].setHardwareTime(0, "TRIG")
        serial_list = [serial for serial in self.sdrs]  # put in a list to avoid random index of dictionary
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        timeLastTriggered0 = [self.sdrs[serial].getHardwareTime("TRIG") for serial in serial_list]
        time.sleep(0.1)  # wait for all trigger work
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        time.sleep(0.1)
        timeLastTriggered1 = [self.sdrs[serial].getHardwareTime("TRIG") for serial in serial_list]
        print(timeLastTriggered0)
        print(timeLastTriggered1)
        notTriggered = []
        for i in range(len(timeLastTriggered0)):  # if trigger time not changed, it means it's not triggered
            if timeLastTriggered0[i] == timeLastTriggered1[i]: notTriggered.append(serial_list[i])
        return notTriggered
    
    def __del__(self):
        print('Iris destruction called')
        for r,stream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
        for r,stream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            self.sdrs[serial].closeStream(stream)
        for serial in self.sdrs:
            sdr = self.sdrs[serial]
            print('deleting serial:', serial)
            if UseFakeSoapy: sdr.deleteref()  # this is simulation, if you want to delete all references, call it explicitly 
            del sdr  # release sdr device
        self.sdrs = None

    def getExtraInfos(self):
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
    
    def nowGains(self):  # tell user what gains could be adjusted, as well as now values
        ret = {}
        rxlst = []
        txlst = []
        for serial_ant in self.tx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                txlst.append(serial + '-0-tx')
                txlst.append(serial + '-1-tx')
            else:
                txlst.append(serial + '-%d-tx' % ant)
        for serial_ant in self.rx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
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
    
    # WARNING: this function is NOT thread safe! call only in the same thread or use lock!
    def setGains(self, gains):  # newGain is dict e.t. {"SERIAL-ANT-rx-gainKey": "13"} where SERIAL and ANT is defined before
        for gainKey in gains:
            ret = self.splitGainKey(gainKey)
            print(ret)
            if ret is None: 
                print("unknown key: " + gainKey)
                continue
            serial_ant, txrx, key = ret
            gainObj = None
            if txrx == 'rx': gainObj = self.rx_gains["%s-%s" % (serial_ant, txrx)]
            else: gainObj = self.tx_gains["%s-%s" % (serial_ant, txrx)]
            self.changeGain(serial_ant, txrx, gainObj, key, gains[gainKey])

if __name__=='__main__':
    main_test()
