#!/usr/bin/python3

import IrisUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio
import sys
import json


def test():
    class FakeMain:
        def __init__(self,tx_serial):
            self.IrisSerialNums = [tx_serial+ "-2-Tx-1"] #serial-chan-TX/RX-trigger
            self.userTrig = True
        def changedF(self):
            print('changedF called')

    conf_dict={}
    with open(sys.argv[1],"r") as f:
        conf_dict = json.load(f)
    print(conf_dict)

    tx_serial = conf_dict['transmitter']['serial']  #"RF3E000002"
    tx_ant = conf_dict['transmitter']['port']
    tx_gain = conf_dict['tx_gain']
    tx_rb = int(conf_dict['nrb'])  # 1.4MHz
    tx_repeat_time = int(conf_dict['tx_repeat_time']) # number of frames(10ms)

    main = FakeMain(tx_serial)
    obj = LTE_Transmitter(main, nb_rb=tx_rb,  conf_dict=conf_dict)
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

    obj.loop(repeat_time=tx_repeat_time)

    # print(main.sampleData)
    for key,value in main.sampleData['data'].items():
        # print(type(main.sampleData['data'][key]))
        # print(key+".mat")
        sio.savemat("rxdata/"+key+".mat", {"wave" : value})
   
    # End

class LTE_Transmitter:
    def __init__(self, main, nb_rb, conf_dict):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Tx_Required(self)  # require at least one tx
        
        # import waveform file
        # IrisUtil.Format_LoadWaveFormFile(self, '../modes/LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902_Waveform.csv')
        scale = float(conf_dict['scale'])
        if (conf_dict['filesource']=='LTE'):
            IrisUtil.Format_DataDir(self, nb_rb=nb_rb)
            data_file = self.data_dir+conf_dict['sig_type']
            IrisUtil.Format_LoadTimeWaveForm(self, data_file, scale)
        else: # selfdefine
            data_file = conf_dict['file']
            IrisUtil.Format_LoadTimeWaveForm(self, data_file, scale)

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 1.92e6*2
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=10e6, freq=3.495e9, dcoffset=True)
        #IrisUtil.Setting_ChangeIQBalance(self,txangle=-0.2,txscale=1.2)

         # create streams (but not activate them)
        IrisUtil.Init_CreateTxStreams_RevB(self)
        # create streams (but not activate them)
        # IrisUtil.Init_CreateRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 38400 # 1024  # could be changed during runtime
        self.showSamples = 60928 # 8192  # init max show samples
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
    
    def doSimpleTx(self,repeat_time):
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
        IrisUtil.Process_TxActivate_WriteFlagAndMultiFrameToTxStream_UseHasTime(self,repeat_time=repeat_time)

    
        # deactive
        IrisUtil.Process_TxDeactive(self)

    def loop(self,repeat_time):
        self.doSimpleTx(repeat_time=repeat_time)
        #IrisUtil.Interface_UpdateUserGraph(self, self.correlationSampes)  # update to user graph
        IrisUtil.Interface_UpdateUserGraph(self)

if __name__ == "__main__":
    test()

