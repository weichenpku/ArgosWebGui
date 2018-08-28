from IrisSimpleRxTxSuperClass import IrisSimpleRxTxSuperClass
import GUI, helperfuncs
import numpy as np

class SinosuidTransceiveWithPrecode(IrisSimpleRxTxSuperClass):  # provding precode settings to practice MU-MIMO or beamforming
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
        super(SinosuidTransceiveWithPrecode, self).__init__(
            rate=10e6, 
            freq=3.6e9, 
            bw=None, 
            clockRate=80e6, 
            rx_serials_ant=rx_serials_ant, 
            tx_serials_ant=tx_serials_ant
        )
        self.numSamples = 1024  # could be changed during runtime
        self.setTrigger(triggerIrisList)
        triggerret = self.tryTrigger()
        if len(triggerret) != 0:
            GUI.alert("not triggered Iris: %s" % str(triggerret))
        for key in self.tx_gains:  # add precode 'gain' :)
            self.tx_gains[key]["precode"] = 1.+0.j  
        for key in self.rx_gains: 
            self.rx_gains[key]["postcode"] = 1.+0.j  # I don't known how to name it >.< see "postProcessRxSamples" below
        self.showSamples = 8192  # init max samples
    
    # override parent function!
    def buildTxTones(self, numSamples):
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, numSamples)).transpose() * 1 / self.rate  # time of each point
        tone = np.exp(s_time_vals * 2.j * np.pi * waveFreq).astype(np.complex64)
        tones = []
        for r, serial_ant in enumerate(self.tx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                tones.append([tone * complex(self.tx_gains[serial + '-0-tx']["precode"]), tone * complex(self.tx_gains[serial + '-1-tx']["precode"])])  # two stream
            else:
                tones.append([tone * complex(self.tx_gains[serial_ant + '-tx']["precode"])])
        return tones
    
    # override parent function!
    def postProcessRxSamples(self):
        for r, serial_ant in enumerate(self.rx_serials_ant):
            serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
            if ant == 2:
                self.sampsRecv[r][0] *= complex(self.rx_gains[serial + "-0-rx"]["postcode"])
                self.sampsRecv[r][1] *= complex(self.rx_gains[serial + "-1-rx"]["postcode"])
            else:
                self.sampsRecv[r][0] *= complex(self.rx_gains[serial + "-%d-rx" % ant]["postcode"])  # received samples
    
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
        ret = super(SinosuidTransceiveWithPrecode, self).nowGains()
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
        super(SinosuidTransceiveWithPrecode, self).setGains(gains)
    
    def doSimpleRxTx(self):
        ret = super(SinosuidTransceiveWithPrecode, self).doSimpleRxTx(self.numSamples)
        ((_, tones), (_, sampsRecv)) = ret
        exceeded = False  # flag to indicate whether there is sequence longer than self.showSamples
        for i in range(len(tones)):
            if (len(tones[i]) > self.showSamples):
                tones[i] = [tone[:self.showSamples] for tone in tones[i]]
                exceeded = True
        for i in range(len(sampsRecv)):
            if (len(sampsRecv[i]) > self.showSamples):
                sampsRecv[i] = [samps[:self.showSamples] for samps in sampsRecv[i]]
                exceeded = True
        if exceeded:
            print("data has been sliced to %d due to showSamples" % self.showSamples)
        return ret

