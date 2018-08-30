try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["0313-0-Tx-1"]
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = Sinusoid_Repeator_DevFE_RevB_180830(main)
    obj.setGains({
        "parameters-showSamples": "16"
    })
    print(obj.nowGains())
    print(obj.loop())
    print(main.sampleData)

class Sinusoid_Repeator_DevFE_RevB_180830:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Tx_Required(self)  # require at least one tx

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 10e6  # save this for later build tx tone
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=30e6, freq=2.35e9, dcoffset=True)

        # create streams (but not activate them)
        IrisUtil.Init_CreateRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.txFrameSize = 1024  # immutable
        self.numSamples = 1024  # could be changed during runtime
        self.showSamples = 8192  # init max show samples
        self.selfparameters = {"numSamples": int, "showSamples": int}  # this will automatically added to UI

        # add postcode support
        IrisUtil.Gains_AddPostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)
        
        # repeat sequence generate
        IrisUtil.Init_CreateRepeatorSinusoidSequence(self)

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
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 57)

        # sleep to wait
        IrisUtil.Process_WaitForTime_NoTrigger(self)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
    
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
