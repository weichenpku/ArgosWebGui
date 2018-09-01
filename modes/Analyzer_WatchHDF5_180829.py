try:  # called from host.py, main dir is ../
    import modes.IrisUtil as IrisUtil
except Exception as e:
    import IrisUtil
import time

def test():
    class FakeMain:
        def __init__(self):
            self.IrisSerialNums = []
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    main = FakeMain()
    obj = Analyzer_WatchHDF5_180829(main)
    obj.setGains({
        "parameters-fileName": "Recorder_BurstRecord_DevFE_RevB_180829_2018-08-29_21-37-59.hdf5",
    })
    print(obj.nowGains())
    print(obj.loop())
    print(main.sampleData)

class Analyzer_WatchHDF5_180829:
    def __init__(self, main):
        self.main = main
        IrisUtil.Alert_SerialNumsIgnored(self)

        # create empty variables to prevent exception, when user load a file, it will be set again
        IrisUtil.Init_CreateDefaultGain_FileAnalyze(self)

        # add input to user GUI, for them to input
        self.fileName = ""  # the hdf5 filename
        self.offset = 0  # the offset of data to show
        self.length = 128  # how many points to show in user space. if not enough, a warning will be shown in GUI
        self.selfparameters = {
            "fileName": lambda filename: IrisUtil.Analyze_LoadHDF5FileByName(self, filename),  # if check failed, raise exception, otherwise load it!
            "offset": int, 
            "length": int
        }  # this will automatically added to UI

    def nowGains(self):
        gains = IrisUtil.Gains_GetBasicGains(self)  # enable operations on data recorded
        IrisUtil.Gains_AddParameter(self, gains)
        return gains
    
    # WARNING: this function is NOT thread safe! call only in the same thread or use lock!
    def setGains(self, gains):
        IrisUtil.Gains_HandleSelfParameters(self, gains)
    
    def doSimpleShow(self):
        pass
    
    def loop(self):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleShow()
            IrisUtil.Interface_UpdateUserGraph(self)  # update to user graph

if __name__ == "__main__":
    test()
