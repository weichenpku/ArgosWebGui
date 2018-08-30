try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["foo-0-Tx-1", "bar-0-Rx-0"]
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = Sinusoid_Transceiver_ArgosV3FE_180828(main)
    obj.setGains({
        "foo-0-tx-ATTN": "10",
        "parameters-numSamples": "16",
        "foo-0-tx-precode": "0.5-0.5j"
    })
    print(obj.nowGains())
    print(obj.loop())
    print(main.sampleData)

class Sinusoid_Transceiver_ArgosV3FE_180828_NOTFINISHED:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithFrontEnd(self)
        self.rate = 10e6  # save this for later build tx tone
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=None, freq=3.6e9, dcoffset=None)

        # create streams (but not activate them)
        IrisUtil.Init_CreateTxRxStreams(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 1024  # could be changed during runtime
        self.showSamples = 8192  # init max show samples
        self.selfparameters = {"numSamples": int, "showSamples": int}  # this will automatically added to UI

        # add precode and postcode support
        IrisUtil.Gains_AddPrecodePostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode, txGainKeyException=IrisUtil.Gains_GainKeyException_TxPrecode)
    
    def __del__(self):
        print('Iris destruction called')
        IrisUtil.Deinit_SafeDelete(self)
    
    def getExtraInfos(self):
        return IrisUtil.Extra_GetExtraInfo_WithFrontEnd(self)  # with front-end temperature
    
    def nowGains(self):
        gains = IrisUtil.Gains_GetBasicGains(self)
        IrisUtil.Gains_AddParameter(self, gains)
        return gains
    
    # WARNING: this function is NOT thread safe! call only in the same thread or use lock!
    def setGains(self, gains):
        IrisUtil.Gains_SetBasicGains(self, gains)
    
    def doSimpleRxTx(self):
        # prepare work, create tx rx buffer
        IrisUtil.Process_BuildTxTones_Sinusoid(self)
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)
        # activate
        IrisUtil.Process_TxActivate_WriteFlagAndDataToTxStream(self)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream(self)

        # trigger in the near future
        time.sleep(0.1)
        IrisUtil.Process_GenerateTrigger(self)
        time.sleep(0.1)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
    
        # deactive
        IrisUtil.Process_TxDeactive(self)
        IrisUtil.Process_RxDeactive(self)
    
    def loop(self):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleRxTx()
            IrisUtil.Interface_UpdateUserGraph(self)  # update to user graph

if __name__ == "__main__":
    test()
