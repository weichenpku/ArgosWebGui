from IrisSimpleRxTxSuperClass import IrisSimpleRxTxSuperClass
import GUI, helperfuncs

class UserTrigOneSendOtherRecv(IrisSimpleRxTxSuperClass):
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
        super(UserTrigOneSendOtherRecv, self).__init__(
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
