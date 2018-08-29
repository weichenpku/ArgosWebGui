try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = ["0313-0-Rx-1", "0283-0-Rx-0"]
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = Recorder_BurstRecord_DevFE_RevB_180829(main)
    obj.setGains({
        "parameters-numSamples": "4096",
        "parameters-showSamples": "16"
    })
    print(obj.nowGains())
    print(obj.loop())
    print(main.sampleData)

class Recorder_BurstRecord_DevFE_RevB_180829:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Alert_OnlyTorR_OtherIgnored(self, "Rx")  # ignore Iris not Rx
        IrisUtil.Format_UserInputSerialAnts(self)

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 10e6  # save this for later build tx tone
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=30e6, freq=2.35e9, dcoffset=True)

        # create streams (but not activate them)
        IrisUtil.Init_CreateTxRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 1024  # could be changed during runtime
        self.showSamples = 8192  # init max show samples
        self.fileName = ""  # the hdf5 filename, must end with ".hdf5" otherwise will be create automatically by class name and time
        self.selfparameters = {
            "fileName": IrisUtil.Format_CheckEndWithHDF5OrAddIt,
            "numSamples": int, 
            "showSamples": int
        }  # this will automatically added to UI

        # add precode and postcode support
        IrisUtil.Gains_AddPrecodePostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)
    
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
    
    def doSimpleRxTx(self):
        # create hdf5 file first, in case the file is not proper
        IrisUtil.Process_InitHDF5File_RxOnlyBurst(self)

        # prepare work, create rx buffer
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 0)

        # sleep to wait
        IrisUtil.Process_WaitForTime_NoTrigger(self)

        # read stream
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
    
        # deactive
        IrisUtil.Process_RxDeactive(self)

        # save data to hdf5 file
        IrisUtil.Process_SaveHDF5File_RxOnlyBurst(self)
    
    def loop(self):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleRxTx()
            IrisUtil.Interface_UpdateUserGraph(self)  # update to user graph

if __name__ == "__main__":
    test()
