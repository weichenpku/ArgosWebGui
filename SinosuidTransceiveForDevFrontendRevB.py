from IrisSimpleRxTxSuperClass import IrisSimpleRxTxSuperClass, DEBUG_WITH_FAKESOAPYSDR

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
import GUI, helperfuncs, time
import numpy as np

def main_test():
    obj = SinosuidTransceiveForDevFrontendRevB(["0313-0-Tx-1", "0283-0-Rx-0"])
    # obj.doSimpleRxTx()
    print(obj.getExtraInfos())


class SinosuidTransceiveForDevFrontendRevB(IrisSimpleRxTxSuperClass):  # provding precode settings to practice MU-MIMO or beamforming
    def __init__(self, 
        serials=[]
    ):
        rx_serials_ant = []
        tx_serials_ant = []
        triggerIrisList = []
        for ele in serials:
            ret = helperfuncs.FormatFromSerialAntTRtrigger(ele)
            if ret is None:
                GUI.error("unkown format: %s" % ele)
                return
            serial, ant, TorR, trigger = ret
            if trigger:
                triggerIrisList.append(serial)
            if TorR == 'Rx':
                rx_serials_ant.append(serial + '-' + ant)
            elif TorR == 'Tx':
                tx_serials_ant.append(serial + '-' + ant)
            else:
                GUI.error("unkown TorR: %s" % TorR)
                return
        self.default_rx_gains = {  # the dev front-end is rather different
            "rxGain": 20  # Rx gain (dB)
        }
        self.default_tx_gains = {
            "txGain": 40  # Tx gain (dB)
        }
        if len(triggerIrisList) != 1:  # for dedicated use: just a few Iris, about 8, that's our case
            GUI.error("no trigger Iris or more than one trigger Iris are provided, this will cause exception when trigger")
        self.triggerIrisList = [ele for ele in triggerIrisList]  # deep copy
        super(SinosuidTransceiveForDevFrontendRevB, self).__init__(
            rate=10e6, 
            freq=2.35e9, 
            bw=30e6, 
            clockRate=80e6, 
            rx_serials_ant=rx_serials_ant, 
            tx_serials_ant=tx_serials_ant,
            dcoffset=False # we'll remove this in post-processing
        )
        # Synchronize Triggers and Clocks
        if len(self.triggerIrisList) > 0:
            trigsdr = self.sdrs[self.triggerIrisList[0]]
            trigsdr.writeSetting('SYNC_DELAYS', "")
            for serial in self.sdrs: self.sdrs[serial].setHardwareTime(0, "TRIG")
            self.sdrs[self.triggerIrisList[0]].writeSetting("TRIGGER_GEN", "")
        
        self.numSamples = 1024  # could be changed during runtime
        # didn't check trigger condition. It's your responsibility to make sure they'll all be triggered
        for key in self.tx_gains:  # add precode 'gain' :)
            self.tx_gains[key]["precode"] = 1.+0.j  
        for key in self.rx_gains: 
            self.rx_gains[key]["postcode"] = 1.+0.j  # I don't known how to name it >.< see "postProcessRxSamples" below
        self.showSamples = 8192  # init max samples
    
    def getExtraInfos(self):
        info = {}
        info["list"] = [ele for ele in self.all_used_serials]
        info["data"] = {}
        for serial in self.all_used_serials:  # to keep order, that's necessary for using web controller wy@180804
            localinfo = []
            localinfo.append(["LMS7", float(self.sdrs[serial].readSensor("LMS7_TEMP"))])
            localinfo.append(["Zynq", float(self.sdrs[serial].readSensor("ZYNQ_TEMP"))])
            info["data"][serial] = localinfo
        return info

    def prepareTx(self, tones, delay = 10000000, breakWhenBadRW = True):  # by default: 10ms delay
        # first ask the first trigger Iris for time
        self.ts = self.sdrs[self.triggerIrisList[0]].getHardwareTime() + delay  # give us delay ns to set everything up.
        flags = SOAPY_SDR_HAS_TIME | SOAPY_SDR_END_BURST
        for r,txStream in enumerate(self.txStreams):
            serial_ant = self.tx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.activateStream(txStream)  # activate it!
            # then send data, make sure that all data is written
            numSent = 0
            tone = tones[r]
            while numSent < len(tone):
                sr = sdr.writeStream(txStream, [tone[numSent:]], len(tone)-numSent, flags, timeNs=self.ts)
                if sr.ret == -1:
                    print("Error: Bad Write!")
                    if breakWhenBadRW: break
                else: numSent += sr.ret
    
    def prepareRx(self, rx_delay = 57, delay = 10000000):
        rx_delay_ns = SoapySDR.ticksToTimeNs(rx_delay, self.rate)
        ts = self.ts + rx_delay_ns  # rx is a bit after tx
        flags = SOAPY_SDR_HAS_TIME | SOAPY_SDR_END_BURST
        # activate all receive stream
        for r,rxStream in enumerate(self.rxStreams):
            serial_ant = self.rx_serials_ant[r]
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            sdr = self.sdrs[serial]
            sdr.activateStream(rxStream, flags, ts, len(self.sampsRecv[r]))

    def triggerProcess(self):  # use HAS_TIME mode, so no trigger will be generated
        hw_time = self.sdrs[self.triggerIrisList[0]].getHardwareTime()
        if self.ts > hw_time: time.sleep((self.ts - hw_time) / 1e9)  # otherwise do not sleep
    
    # override parent function!
    def rxStreamSetup(self, sdr, chans):
        sdr.writeSetting(SOAPY_SDR_RX, 0, 'CALIBRATE', 'SKLK')  # this is from sklk-demos/python/SISO.py wy@180823
        stream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        return stream
    
    # override parent function!
    def txStreamSetup(self, sdr, chans):
        sdr.writeSetting(SOAPY_SDR_TX, 0, 'CALIBRATE', 'SKLK')  # this is from sklk-demos/python/SISO.py wy@180823
        stream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, chans, {"remote:prot": "tcp", "remote:mtu": "1024"})
        return stream
    
    # override parent function!
    def buildTxTones(self, numSamples):
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, numSamples)).transpose() * 1 / self.rate  # time of each point
        tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
        ret = []
        for i in range(len(self.txStreams)):
            localtone = tone * complex(self.tx_gains[i]["precode"])
            ret.append(localtone)
        return ret
    
    # override parent function!
    def postProcessRxSamples(self):
        for r,rxStream in enumerate(self.rxStreams):
            self.sampsRecv[r] *= complex(self.rx_gains[r]["postcode"])   # received samples
    
    # override parent function!
    def rxGainKeyException(self, gainKey, newValue=None, gainObj=None):  # for DIY gain key
        if gainKey == "postcode":
            try:
                gainObj["postcode"] = complex(newValue)
            except ValueError:
                GUI.error("cannot convert to complex number: " + newValue)
                return None
            return True
        return None
    
    # override parent function!
    def txGainKeyException(self, gainKey, newValue=None, gainObj=None):  # for DIY gain key
        if gainKey == "precode":
            try:
                gainObj["precode"] = complex(newValue)
            except ValueError:
                GUI.error("cannot convert to complex number: " + newValue)
                return None
            return True
        return None

    # add some parameter due to Xieyan Xu's advice, e.g. the "max sample" which is sent to the browser, to test the performance meanwhile limit overhead on browser
    def nowGains(self):
        ret = super(SinosuidTransceiveForDevFrontendRevB, self).nowGains()
        ret["list"].insert(0, ["parameters", ["numSamples", "showSamples"]])
        ret["data"]["parameters-numSamples"] = str(self.numSamples)
        ret["data"]["parameters-showSamples"] = str(self.showSamples)
        return ret
    
    def setGains(self, gains):
        for gainKey in gains:
            if gainKey == "parameters-showSamples":
                try:
                    self.showSamples = int(gains[gainKey])
                except:
                    GUI.error("set showSamples error")
            elif gainKey == "parameters-numSamples":
                try:
                    self.numSamples = int(gains[gainKey])
                except:
                    GUI.error("set numSamples error")
        super(SinosuidTransceiveForDevFrontendRevB, self).setGains(gains)
        print(self.rx_gains)
        print(self.tx_gains)
    
    def doSimpleRxTx(self):
        ret = super(SinosuidTransceiveForDevFrontendRevB, self).doSimpleRxTx(self.numSamples)
        ((_, tones), (_, sampsRecv)) = ret
        exceeded = False  # flag to indicate whether there is sequence longer than self.showSamples
        for i in range(len(tones)):
            if (len(tones[i]) > self.showSamples):
                tones[i] = tones[i][:self.showSamples]
                exceeded = True
        for i in range(len(sampsRecv)):
            if (len(sampsRecv[i]) > self.showSamples):
                sampsRecv[i] = sampsRecv[i][:self.showSamples]
                exceeded = True
        if exceeded:
            print("data has been sliced to %d due to showSamples" % self.showSamples)
        return ret



if __name__ == '__main__':
    main_test()
