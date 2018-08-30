try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["foo-0-Tx-1", "bar-0-Tx-0", "buk-0-Rx-0"]
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = Sinusoid_Repeator_ArgosV3FE_180829(main)
    obj.setGains({
        "foo-0-tx-ATTN": "10",
        "parameters-showSamples": "16"
    })
    print(obj.nowGains())
    print(obj.loop())
    print(main.sampleData)

class Sinusoid_Repeator_ArgosV3FE_180829:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithFrontEnd(self)
        self.rate = 10e6  # save this for later build tx tone
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=30e6, freq=3.6e9, dcoffset=True)

        # create streams (but not activate them)
        IrisUtil.Init_CreateTxRxStreams(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.txFrameSize = 1024  # immutable
        self.numSamples = 1024  # could be changed during runtime
        self.showSamples = 8192  # init max show samples
        self.selfparameters = {"numSamples": int, "showSamples": int}  # this will automatically added to UI

        # add precode and postcode support
        # IrisUtil.Gains_AddPrecodePostcodeGains(self)
        # IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode, txGainKeyException=IrisUtil.Gains_GainKeyException_TxPrecode)
        
        # repeat sequence generate
        self.numSamples = 1024  # immutable during runtime, this is the sinusoid of each antenna, but every antenna is sending this one by one
        IrisUtil.Init_CreateRepeatorSinusoidSequence(self)

        # set repeat
        IrisUtil.Process_TxActivate_WriteFlagAndDataToTxStream_RepeatFlag(self)
    
    def __del__(self):
        print('Iris destruction called')
        IrisUtil.Deinit_SafeTxStopRepeat(self)
        IrisUtil.Deinit_SafeDelete(self)
    
    def getExtraInfos(self):
        return IrisUtil.Extra_GetExtraInfo_WithFrontEnd(self)  # with front-end temperature
    
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
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 57)

        # sleep to wait
        IrisUtil.Process_WaitForTime_NoTrigger(self)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
    
        # deactive
        IrisUtil.Process_RxDeactive(self)
    
    def loop(self):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleRx()
            IrisUtil.Interface_UpdateUserGraph(self)  # update to user graph

if __name__ == "__main__":
    test()
