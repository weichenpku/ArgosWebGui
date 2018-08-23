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
        clockRate=80e6,
        rx_serials_ant = ['0123:0'],
        tx_serials_ant = []
    )
    #obj.setTrigger(["RF3C000034"])
    #print("not triggered objects:", obj.tryTrigger())  # if triggered, this will return a empty list
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
    obj.close()


class IrisSimpleRxTxSuperClass:
    def __init__(self, 
        rate=10e6, 
        freq=3.6e9, 
        bw=None, 
        clockRate=80e6,
        rx_serials_ant=[], 
        tx_serials_ant=[]
    ):
        self.sdrs = {}
        self.rx_gains = []
        self.tx_gains = []
        # deep copy of rx_serials_ant and tx_serials_ant, this is python necessary :)
        self.rx_serials_ant = [ele for ele in rx_serials_ant]
        self.tx_serials_ant = [ele for ele in tx_serials_ant]
        self.rxStreams = []  # index just matched to rx_serials_ant, also does rx_gains
        self.txStreams = []
        self.triggerIrisList = []
        self.all_used_serials = []
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
            #if clockRate is not None: sdr.setMasterClockRate(clockRate)  # set master clock
        # self.all_used_serials = [serial for serial in self.all_used_serials if serial in self.sdrs]  # to avoid user input strange serial numbers :)

        # create basic gain settings for tx/rx (surely you can add new "gain" settings or even delete some of them in child class, it's up to you!)
        # for serial_ant in self.rx_serials_ant:
        #     serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        #     default_rx_gains = {
        #         'LNA2': 15,  # [0,17]
        #         'LNA1': 20,  # [0,33]
        #         'ATTN': 0,   # [-18,0]
        #         'LNA': 25,   # [0,30]
        #         'TIA': 0,    # [0,12]
        #         'PGA': 0     # [-12,19]
        #     }
        #     self.rx_gains.append(default_rx_gains)
        #     chan = ant  # TODO: two antenna using two channel! I'm not sure if it works! wy@180804
        #     sdr = self.sdrs[serial]  # get sdr object reference
        #     if bw is not None: sdr.setBandwidth(SOAPY_SDR_RX, chan, bw)
        #     if freq is not None: sdr.setFrequency(SOAPY_SDR_RX, chan, "RF", freq)
        #     sdr.setAntenna(SOAPY_SDR_RX, chan, "TRX")  # TODO: I assume that in base station given, it only has two TRX antenna but no RX antenna wy@180804
        #     sdr.setFrequency(SOAPY_SDR_RX, chan, "BB", 0) #don't use cordic
        #     sdr.setDCOffsetMode(SOAPY_SDR_RX, chan, True) #dc removal on rx
        #     if rate is not None: sdr.setSampleRate(SOAPY_SDR_RX, chan, rate)
        #     for key in default_rx_gains:
        #         sdr.setGain(SOAPY_SDR_RX, chan, key, default_rx_gains[key])
        # for serial_ant in self.tx_serials_ant:
        #     serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        #     default_tx_gains = {
        #         'ATTN': 0,   # [-18,0] by 3
        #         'PA1': 15,   # [0|15]
        #         'PA2': 0,    # [0|15]
        #         'PA3': 30,   # [0|30]
        #         'IAMP': 12,  # [0,12]
        #         'PAD': 0,  # [-52,0] ? wy@180805: PAD range is positive to ensure 0 dB is minimum power: Converting PAD value of -30 to 22 dB...
        #     }
        #     self.tx_gains.append(default_tx_gains)
        #     chan = ant
        #     sdr = self.sdrs[serial]
        #     if bw is not None: sdr.setBandwidth(SOAPY_SDR_TX, chan, bw)
        #     if freq is not None: sdr.setFrequency(SOAPY_SDR_TX, chan, "RF", freq)
        #     sdr.setAntenna(SOAPY_SDR_TX, chan, "TRX")
        #     sdr.setFrequency(SOAPY_SDR_TX, chan, "BB", 0)  # don't use cordic
        #     if rate is not None: sdr.setSampleRate(SOAPY_SDR_TX, chan, rate)
        #     for key in default_tx_gains:
        #         sdr.setGain(SOAPY_SDR_TX, chan, key, default_tx_gains[key])

        # create rx/tx streams
        for r, serial_ant in enumerate(self.rx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chan = ant  # different ant using different channel
            sdr = self.sdrs[serial]
            stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [chan], {})
            self.rxStreams.append(stream) 
            # np.empty(num_samps).astype(np.complex64)  # not create numpy arrays here, leave this to child class (maybe user could change num_samps at run-time)
        for r, serial_ant in enumerate(self.tx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            chan = ant
            sdr = self.sdrs[serial]
            stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, [chan], {"remote:prot":"tcp", "remote:mtu":"1024"})
            self.txStreams.append(stream) 
            # for sdr in self.tx_sdrs: sdr.activateStream(txStream)  # not activate streams, leave it to child class or trigger function in this class
    
    def buildTxTones(self, num_samps):
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, num_samps)).transpose() * 1 / self.rate  # time of each point
        tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
        return [tone for i in range(len(self.txStreams))]  # send all sinosuid wave
    
    def postProcessRxSamples(self):
        for r,rxStream in enumerate(self.rxStreams):
            sampsRecv = self.sampsRecv[r]  # received samples
            # do nothing here, if you want to modify received stream (for example, to practice the process of recognize pilot and )

    def doSimpleRxTx(self, num_samps):  # this is just a demo: send sinosuid to all tx
        tones = self.buildTxTones(num_samps)  # build tx samples

        # create numpy arrays for receiving
        self.sampsRecv = [np.zeros(num_samps, np.complex64) for r in range(len(self.rxStreams))]

        # clear out socket buffer from old requests
        # for r,rxStream in enumerate(self.rxStreams):
        #     serial_ant = self.rx_serials_ant[r]
        #     serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        #     sdr = self.sdrs[serial]
        #     sr = sdr.readStream(rxStream, [self.sampsRecv[r][:]], len(self.sampsRecv[r]), timeoutUs = 0)
        #     while sr.ret != SOAPY_SDR_TIMEOUT and not UseFakeSoapy:
        #         sr = sdr.readStream(rxStream, [self.sampsRecv[r][:]], len(self.sampsRecv[r]), timeoutUs = 0)
        
        # prepare data for sending
        # flags = SOAPY_SDR_WAIT_TRIGGER | SOAPY_SDR_END_BURST
        # for r,txStream in enumerate(self.txStreams):
        #     serial_ant = self.tx_serials_ant[r]
        #     serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        #     sdr = self.sdrs[serial]
        #     sdr.activateStream(txStream)  # activate it!
        #     # then send data, make sure that all data is written
        #     numSent = 0
        #     tone = tones[r]
        #     while numSent < len(tone):
        #         sr = sdr.writeStream(txStream, [tone[numSent:]], len(tone)-numSent, flags)
        #         if sr.ret == -1: print("Error: Bad Write!")
        #         else: numSent += sr.ret
        
        flags = SOAPY_SDR_HAS_TIME | SOAPY_SDR_END_BURST
        # activate all receive stream
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.activateStream(rxStream, flags, 0, len(self.sampsRecv[r]))

        # trigger in the near future
        time.sleep(0.1)
        # for serial in self.triggerIrisList:  # just simple trigger all
        #     self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        # time.sleep(0.05)

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
                    break
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
        idx = serial_ant.rfind(':')
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
        serial_ant = serial + ':' + ant
        index = -1
        if txrx == "rx": index = self.rx_serials_ant.index(serial_ant)  # this step consume linear time! but always antenna is under 20 elements I guessssssss......
        else: index = self.tx_serials_ant.index(serial_ant)
        if index == -1: return None
        gk = key
        if txrx == "rx":
            if gk not in self.rx_gains[index]: return None
        elif gk not in self.tx_gains[index]: return None
        return serial_ant, index, txrx, key
    
    # return anything if cannot change the gain or unknown gainKey, otherwise just return None (or simply do not return)
    def changeGain(self, serial_ant, gainObj, gainKey, gainNewValue):  # note that when using web controller, gainNewValue will always be string!
        # you can overwrite this, but note that you can call IrisSimpleRxTxSuperClass.changeGain(self, xxx) to support basic gain settings without repeat code
        gk = gainKey
        serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
        chan = ant
        sdr = self.sdrs[serial]
        if serial_ant in self.rx_serials_ant:
            if gk=="LNA2" or gk=="LNA1" or gk=="ATTN" or gk=="LNA" or gk=="TIA" or gk=="PGA":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                    sdr.setGain(SOAPY_SDR_RX, chan, gainKey, gainObj[gainKey])
                except:
                    return None
                return True
            return self.rxGainKeyException(gainKey, newValue=gainNewValue, gainObj=gainObj)
        elif serial_ant in self.tx_serials_ant:
            if gk=="ATTN" or gk=="PA1" or gk=="PA2" or gk=="PA3" or gk=="IAMP" or gk=="PAD":
                try:
                    gainObj[gainKey] = int(gainNewValue)
                    sdr.setGain(SOAPY_SDR_TX, chan, gainKey, gainObj[gainKey])
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
            self.sdrs[serial].setHardwareTime(0, "TRIGGER")
        serial_list = [serial for serial in self.sdrs]  # put in a list to avoid random index of dictionary
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        timeLastTriggered0 = [self.sdrs[serial].getHardwareTime("TRIGGER") for serial in serial_list]
        time.sleep(0.1)  # wait for all trigger work
        for serial in self.triggerIrisList:  # just simple trigger all
            self.sdrs[serial].writeSetting("TRIGGER_GEN", "")
        time.sleep(0.1)
        timeLastTriggered1 = [self.sdrs[serial].getHardwareTime("TRIGGER") for serial in serial_list]
        print(timeLastTriggered0)
        print(timeLastTriggered1)
        notTriggered = []
        for i in range(len(timeLastTriggered0)):  # if trigger time not changed, it means it's not triggered
            if timeLastTriggered0[i] == timeLastTriggered1[i]: notTriggered.append(serial_list[i])
        return notTriggered
    
    def __del__(self):
        print('Iris destruction called')
        for serial in self.sdrs:
            sdr = self.sdrs[serial]
            print('deleting serial:', serial)
            if UseFakeSoapy: sdr.deleteref()  # this is simulation, if you want to delete all references, call it explicitly 
            del sdr  # release sdr device
        self.sdrs = None
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

    def getExtraInfos(self):
        return {
            "list": [],
            "data": {}
        }
        info = {}
        info["list"] = [ele for ele in self.all_used_serials]
        info["data"] = {}
        for serial in self.all_used_serials:  # to keep order, that's necessary for using web controller wy@180804
            localinfo = []
            localinfo.append(["LMS7", float(self.sdrs[serial].readSensor("LMS7_TEMP"))])
            localinfo.append(["Zynq", float(self.sdrs[serial].readSensor("ZYNQ_TEMP"))])
            localinfo.append(["Frontend", float(self.sdrs[serial].readSensor("FE_TEMP"))])
            localinfo.append(["PA0", float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 0, 'TEMP'))])
            localinfo.append(["PA1", float(self.sdrs[serial].readSensor(SOAPY_SDR_TX, 1, 'TEMP'))])
            info["data"][serial] = localinfo
        return info
    
    def nowGains(self):  # tell user what gains could be adjusted, as well as now values
        return {
            "list": [],
            "data": {}
        }
        ret = {}
        rxlst = []
        txlst = []
        for serial_ant in self.rx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            rxlst.append(serial + '-%d-rx' % ant)
        for serial_ant in self.tx_serials_ant:
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            txlst.append(serial + '-%d-tx' % ant)
        data = {}
        retlist = []
        for r,name in enumerate(rxlst):
            gains = self.rx_gains[r]
            a = []
            for gainElementKey in gains:
                a.append(gainElementKey)
                data[name + '-' + gainElementKey] = str(gains[gainElementKey])
            retlist.append([name, a])
        for r,name in enumerate(txlst):
            gains = self.tx_gains[r]
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
            if ret is None: 
                print("unknown key: " + gainKey)
                continue
            serial_ant, index, txrx, key = ret
            gainObj = None
            if txrx == 'rx': gainObj = self.rx_gains[index]
            else: gainObj = self.tx_gains[index]
            self.changeGain(serial_ant, gainObj, key, gains[gainKey])

if __name__=='__main__':
    main_test()
