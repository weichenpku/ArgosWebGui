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
                rx_serials_ant.append(serial + ':' + ant)
            elif TorR == 'Tx':
                tx_serials_ant.append(serial + ':' + ant)
            else:
                GUI.error("unkown TorR: %s" % TorR)
                return
        super(SinosuidTransceiveWithPrecode, self).__init__(
            rate=10e6, 
            freq=3.6e9, 
            bw=None, 
            txGain=40.0, 
            rxGain=30.0, 
            clockRate=80e6, 
            num_samps=1024,
            rx_serials_ant=rx_serials_ant, 
            tx_serials_ant=tx_serials_ant
        )
        for ele in self.tx_gains:  # add precode 'gain' :)
            ele["precode"] = 1.+0.j  
        for ele in self.rx_gains: 
            ele["postcode"] = 1.+0.j  # I don't known how to name it >.< see "postProcessRxSamples" below
    
    # override parent function!
    def buildTxTones(self):
        waveFreq = self.rate / 100  # every period has 100 points
        s_time_vals = np.array(np.arange(0, self.num_samps)).transpose() * 1 / self.rate  # time of each point
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
    
