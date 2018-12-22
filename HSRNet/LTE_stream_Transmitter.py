#!/usr/bin/python3

import IrisUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio

def test():
    class FakeMain:
        def __init__(self,tx_serial):
            self.IrisSerialNums = [tx_serial+"-2-Tx-1"] # serial-chan-TX/RX-trigger
            self.userTrig = True
        def changedF(self):
            print('changedF called')

    tx_serial = "RF3E000010"
    tx_ant = "1"
    tx_gain = "45"


    main = FakeMain(tx_serial)
    obj = LTE_Transmitter(main,data_file='tone.csv',scale=0.9)
    
    obj.setGains({
        "parameters-txSelect": tx_serial+"-"+tx_ant,
        tx_serial+"-0-tx-txGain": tx_gain,
        tx_serial+"-1-tx-txGain": tx_gain,
    })
    
    print()
    print('[SOAR] parameters : value')
    paras = obj.nowGains()
    for para,value in paras['data'].items():
        print(para,':',value)
    print()

    obj.loop()

    # print(main.sampleData)
    for key,value in main.sampleData['data'].items():
        # print(type(main.sampleData['data'][key]))
        # print(key+".mat")
        sio.savemat("rxdata/"+key+".mat", {"wave" : value})

    input() # if the program stops, iris will stop transmitting.
    
    # End

class LTE_Transmitter:
    def __init__(self, main, data_file, scale):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Tx_Required(self)  # require at least one tx
        
        # import waveform file
        # IrisUtil.Format_LoadWaveFormFile(self, '../modes/LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902_Waveform.csv')
        IrisUtil.Format_DataDir(self, nb_rb=6)
        IrisUtil.Format_LoadTimeWaveForm(self, self.data_dir+data_file,scale)

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 1.92e6
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=5e6, freq=3.5e9, dcoffset=True)

         # create streams (but not activate them)
        IrisUtil.Init_CreateTxStreams_RevB(self)
        # create streams (but not activate them)
        # IrisUtil.Init_CreateRxStreams_RevB(self)

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
        # IrisUtil.Process_TxActivate_WriteFlagAndDataToTxStream_RepeatFlag(self)
    
    def __del__(self):
        print('Iris destruction called')
        # IrisUtil.Deinit_SafeTxStopRepeat(self)
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
    
    def doSimpleTx(self):
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
        IrisUtil.Process_TxActivate_WriteFlagAndMultiFrameToTxStream_UseHasTime(self)

    
        # deactive
        IrisUtil.Process_TxDeactive(self)

    def loop(self):
        self.doSimpleTx()
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
