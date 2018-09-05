try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["0313-0-Rx-1"]#, "0283-2-Rx-0"]
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902(main)
    obj.setGains({
        "parameters-showSamples": "16"
    })
    print(obj.nowGains())
    for i in range(10):
        obj.loop()

class LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Alert_OnlyTorR_OtherIgnored(self, "Rx")  # ignore Iris not Rx
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Rx_Required(self)  # require at least one rx

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        IrisUtil.Init_CreateBasicGainSettings(self, bw=5e6, freq=2.35e9, dcoffset=True, rxrate=9e6)

        # create streams (but not activate them)
        IrisUtil.Init_CreateRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 10000000  # could be changed during runtime
        self.showSamples = 8192  # init max show samples
        self.showIntervalS = 10  # 10s show one picture with length of self.showSamples
        self.selfparameters = {
            "numSamples": lambda x: int(x) if not self.running else None,  # only set when it's not running
            "showSamples": int,
            "showIntervalS": int
        }  # this will automatically added to UI

        # record time of now, it will then be used to calculate when to show samples
        self.lastTime = time.time()
        self.running = False
    
    def __del__(self):
        print('Iris destruction called')
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
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 2730667)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 0)

        # sleep to wait
        IrisUtil.Process_WaitForTime_NoTrigger(self)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
    
        # deactive
        IrisUtil.Process_RxDeactive(self)

        # do correlation
        IrisUtil.Process_DoCorrelation2FindFirstPFDMSymbol(self)
    
    def run(self):
        # do read for any length of data
        finished = IrisUtil.Process_ReadFromRxStream_Async(self)

        if finished:
            # do deinitialize work here
            IrisUtil.Process_RxDeactive(self)
            self.running = False
        
        return finished
    
    def prepareReceive(self):
        # prepare work, create tx rx buffer
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000)
        IrisUtil.Process_RxActivate_SetupContinuousReadRxStream(self)

        # setup registers of how many samples are already received (initialized as 0)
        IrisUtil.Process_BuildAsyncRxRegisters(self)

        # set register and time
        self.lastTime = time.time()
        self.running = True
    
    def loop(self):
        if self.main.userTrig:
            if not self.running:
                self.main.userTrig = False
                self.main.changedF()  # just register set
                self.prepareReceive()
        if self.running:
            finished = self.run()
            if finished or time.time() - self.lastTime >= self.showIntervalS:
                self.lastTime = time.time()
                IrisUtil.Interface_UpdateUserGraph(self, uselast=True)  # update to user graph, use the last few data but not the head

if __name__ == "__main__":
    test()
