from IrisSimpleRxTxSuperClass import IrisSimpleRxTxSuperClass

class UserTrigOneSendOtherRecv(IrisSimpleRxTxSuperClass):
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
        super(UserTrigOneSendOtherRecv, self).__init__(rate, freq, bw, txGain, rxGain, clockRate, rxAnt, txAnt, num_samps, serials)
