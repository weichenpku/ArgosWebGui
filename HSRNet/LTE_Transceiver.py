#!/usr/bin/python3

import IrisUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["RF3E000002-2-Tx-1", "RF3E000003-2-Rx-0"] # serial-chan-TX/RX-trigger
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902(main)
    obj.setGains({
        "parameters-showSamples": "30000",
        "parameters-numSamples":"19200",
        "parameters-txSelect": "RF3E000002-1",
        "RF3E000002-0-tx-txGain": "40",
        "RF3E000002-1-tx-txGain": "40",
        "RF3E000003-0-rx-rxGain": "40",
        "RF3E000003-1-rx-rxGain": "40"
    })
    print(obj.nowGains())
    print(obj.loop())
    # print(main.sampleData)
    for key in main.sampleData['data'].keys():
        print(type(main.sampleData['data'][key]))
        print(key+".mat")
        sio.savemat("rxdata/"+key+".mat", {"wave" : main.sampleData['data'][key]})

class LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Tx_Required(self)  # require at least one tx
        
        # import waveform file
        # IrisUtil.Format_LoadWaveFormFile(self, '../modes/LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902_Waveform.csv')
        IrisUtil.Format_DataDir(self, nb_rb=6)
        IrisUtil.Format_LoadTimeWaveForm(self, self.data_dir+"sig_pss.csv")

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        IrisUtil.Init_CreateBasicGainSettings(self, bw=5e6, freq=2.45e9, dcoffset=True, txrate=1.92e6, rxrate=1.92e6)

        # create streams (but not activate them)
        IrisUtil.Init_CreateRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 19200 # 1024  # could be changed during runtime
        self.showSamples = 30000 # 8192  # init max show samples
        serial, ant = IrisUtil.Format_SplitSerialAnt(self.tx_serials_ant[0])
        if ant == 2: self.txSelect = "%s-0" % serial  # select one to send, other set 0
        else: self.txSelect = "%s-%d" % (serial, ant)
        self.alignOffset = 0
        self.selfparameters = {
            "numSamples": int, 
            "showSamples": int, 
            "txSelect": lambda x: IrisUtil.Format_CheckSerialAntInTx(self, x),  # use closure to send "self" object in
            "alignOffset": int
        }  # this will automatically added to UI

        # add postcode support
        IrisUtil.Gains_AddPostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)

        # repeat sequence generate
        # IrisUtil.Init_CreateRepeatorOnehotWaveformSequence(self)
        IrisUtil.Init_CreateRepeatorTimeWaveformSequence(self)

        # set repeat
        IrisUtil.Process_TxActivate_WriteFlagAndDataToTxStream_RepeatFlag(self)
    
    def __del__(self):
        print('Iris destruction called')
        IrisUtil.Deinit_SafeTxStopRepeat(self)
        IrisUtil.Deinit_SafeDelete(self)
    
    def getExtraInfos(self):
        return IrisUtil.Extra_GetExtraInfo_WithDevFE(self)  # with front-end temperature
    
    def nowGains(self):
        gains = IrisUtil.Gains_GetBasicGains(self)
        IrisUtil.Gains_AddParameter(self, gains)
        return gains
    
    # WARNING: this function is NOT thread safe! call only in the same thread or use lock!
    def setGains(self, gains):
        IrisUtil.Gains_HandleSelfParameters(self, gains)
        IrisUtil.Gains_SetBasicGains(self, gains)
    
    def doSimpleRx(self):
        # prepare work, create tx rx buffer
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 0)

        # sleep to wait
        IrisUtil.Process_WaitForTime_NoTrigger(self)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
    
        # deactive
        IrisUtil.Process_RxDeactive(self)

        # do correlation
        # IrisUtil.Process_DoCorrelation2FindFirstPFDMSymbol(self)
    
    def loop(self):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleRx()
            #IrisUtil.Interface_UpdateUserGraph(self, self.correlationSampes)  # update to user graph
            IrisUtil.Interface_UpdateUserGraph(self)

if __name__ == "__main__":
    test()


#{'list': 
#   [['parameters', ['txSelect', 'numSamples', 'showSamples', 'alignOffset']], 
#    ['RF3E000002-0-tx', ['txGain']], 
#    ['RF3E000002-1-tx', ['txGain']], 
#    ['RF3E000010-0-rx', ['postcode', 'rxGain']], 
#    ['RF3E000010-1-rx', ['postcode', 'rxGain']]], 
# 'data': 
#   {'RF3E000010-1-rx-rxGain': '20', 
#    'parameters-txSelect': 'RF3E000002-1', 
#    'RF3E000002-0-tx-txGain': '40', 
#    'RF3E000010-1-rx-postcode': '(1+0j)', 
#    'RF3E000010-0-rx-postcode': '(1+0j)', 
#    'parameters-numSamples': '1024', 
#    'RF3E000002-1-tx-txGain': '40', 
#    'RF3E000010-0-rx-rxGain': '20', 
#    'parameters-alignOffset': '0', 
#    'parameters-showSamples': '1600'}}
