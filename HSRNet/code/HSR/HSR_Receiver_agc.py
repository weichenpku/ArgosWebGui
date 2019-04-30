#!/usr/bin/python3

import sys
sys.path.append("..")
from utils import IrisUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio
import sys
import json
import os

def test():
    class FakeMain:
        def __init__(self,master,slaves):
            self.IrisSerialNums = slaves # serial-chan-TX/RX-trigger
            self.IrisSerialNums.append(master)
            self.userTrig = True
        def changedF(self):
            print('changedF called')
    
    conf_dict={}
    with open(sys.argv[1],"r") as f:
        conf_dict = json.load(f)
    print(conf_dict)

    rx_serial_master = conf_dict['receiver_master']['serial'] + "-" + conf_dict['receiver_master']['port'] + "-Rx-1"
    rx_serial_slaves = []
    for idx in range(int(conf_dict['receivernum'])-1):
        rx_serial_slaves.append(conf_dict['receiver'][idx]['serial'] + "-" + conf_dict['receiver_master']['port'] + "-Rx-0")

    rx_gain = conf_dict['rx_gain']
    rx_repeat_time = int(conf_dict['rx_repeat_time']) # number of frames
    rx_repeat_duration = float(conf_dict['rx_repeat_duration']) # seconds
    rx_path = conf_dict['rx_path']
    
    main = FakeMain(rx_serial_master,rx_serial_slaves)
    obj = LTE_Receiver(main)
    
    gain_dict = {
        "parameters-showSamples": "60928",
        "parameters-numSamples":"60000", # recvNum (should be less than 60928)
        conf_dict['receiver_master']['serial']+"-0-rx-rxGain": rx_gain,
        conf_dict['receiver_master']['serial']+"-1-rx-rxGain": rx_gain
    }
    for idx in range(int(conf_dict['receivernum'])-1):
        gain_dict[conf_dict['receiver'][idx]['serial']+"-0-rx-rxGain"] = rx_gain
        gain_dict[conf_dict['receiver'][idx]['serial']+"-1-rx-rxGain"] = rx_gain
    obj.setGains(gain_dict)
    
    print()
    print('[SOAR] parameters : value')
    paras = obj.nowGains()
    for para,value in paras['data'].items():
        print(para,':',value)
    print()

    obj.loop(conf_dict['filesource'], repeat_time=rx_repeat_time, repeat_duration=rx_repeat_duration, rx_path=rx_path, rx_gain=rx_gain)


class LTE_Receiver:
    def __init__(self, main):
        self.main = main
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        # IrisUtil.Assert_Tx_Required(self)  # require at least one tx
        
        # import waveform file
        # IrisUtil.Format_LoadWaveFormFile(self, '../modes/LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902_Waveform.csv')
        # IrisUtil.Format_DataDir(self, nb_rb=6)
        # IrisUtil.Format_LoadTimeWaveForm(self, self.data_dir+"tone.csv")

        # init sdr object
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)

        # create gains and set them
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 1.92e6*2
        IrisUtil.Init_CreateBasicGainSettings(self, bw=10e6, freq=3.495e9, dcoffset=True, txrate=self.rate, rxrate=self.rate)

        # create streams (but not activate them)
        IrisUtil.Init_CreateRxStreams_RevB(self)

        # sync trigger and clock
        IrisUtil.Init_SynchronizeTriggerClock(self)

        self.numSamples = 19200  # could be changed during runtime
        self.showSamples = 30000  # init max show samples
        self.alignOffset = 0
        self.selfparameters = {
            "numSamples": int, 
            "showSamples": int, 
            # "txSelect": lambda x: IrisUtil.Format_CheckSerialAntInTx(self, x),  # use closure to send "self" object in
            "alignOffset": int
        }  # this will automatically added to UI

        # add postcode support
        IrisUtil.Gains_AddPostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)

        # repeat sequence generate
        # IrisUtil.Init_CreateRepeatorOnehotWaveformSequence(self)
        # IrisUtil.Init_CreateRepeatorTimeWaveformSequence(self)

        # set repeat
        # IrisUtil.Process_TxActivate_WriteFlagAndDataToTxStream_RepeatFlag(self)
    
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
    
    def doSimpleRx(self,fsrc,repeat_time,repeat_duration, rx_path, rx_gain):
        # prepare work, create tx rx buffer
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)

        # clear buffer
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay=10000000, alignment=0)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay=0)
        IrisUtil.Process_WaitForTime_NoTrigger(self)
        IrisUtil.Process_ReadFromRxStream(self)
        IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
        IrisUtil.Process_SaveData(self)

        # activate
        epoch = 0
        while (True):  # test case
            rx_dir = rx_path+'epoch'+str(epoch)
            if os.path.exists(rx_dir)==False:
                os.makedirs(rx_dir)
            
            # agc for gain set
            gain_val = rx_gain
            while (True):
                IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay=10000000, alignment=0)
                IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay=0)
                IrisUtil.Process_WaitForTime_NoTrigger(self)
                flag = IrisUtil.Process_ReadFromRxStream(self)
                if (flag==False):
                    continue
                IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
                recvdata = IrisUtil.Process_SaveData(self)
                maxpeak = 0
                for chan in recvdata:
                    chanpeak = np.max(np.abs(recvdata[chan]))
                    if (chanpeak > maxpeak): maxpeak = chanpeak
                print('AGC: chanpeak is', chanpeak,'; rxgain is ',gain_val)
                print('AGC test')
                print()
                if maxpeak > 0.95:
                    gain_val = str(int(gain_val)-5)
                    gain_obj = {}
                    for key in self.rx_gains:
                        gain_obj[key+"-rxGain"]=gain_val
                    self.setGains(gain_obj)
                else:
                    break

            #start epoch receiving
            i=1
            while i <= repeat_time: 
                IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
                IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 0)

                # sleep to wait
                IrisUtil.Process_WaitForTime_NoTrigger(self)

                # read stream
                flag = IrisUtil.Process_ReadFromRxStream(self)
                IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data

                recvdata = IrisUtil.Process_SaveData(self)

                maxpeak = 0
                for chan in recvdata:
                    chanpeak = np.max(np.abs(recvdata[chan]))
                    print('AGC: chanpeak is', chanpeak)
                    if (chanpeak > maxpeak): maxpeak = chanpeak
                print('AGC: chanpeak is', maxpeak, '; rxgain is ', gain_val)

                sio.savemat(rx_path+"epoch"+str(epoch)+"/rx"+str(i)+".mat",recvdata)
                print('repeat_time: ',i)
                print()
                # sleep before next activation
                time.sleep(repeat_duration)
                if flag==True:
                    i=i+1
            print('epoch finish: ', epoch)

            # mini shell
            while (true):
                nextstep = input()
                if (nextstep == 'q'): # quit
                    break
                elif (nextstep == 'r'): # repeat
                    break
                elif (nextstep == 'n'): # next 
                    epoch = epoch + 1
                    break
                else:
                    print(' q - quit\n r - repeat\n n - next\n other - help')

            if (nextstep == 'q'):
                break
            

        # deactive
        IrisUtil.Process_RxDeactive(self)

        # do correlation
        # IrisUtil.Process_DoCorrelation2FindFirstPFDMSymbol(self)
    
    def loop(self,fsrc,repeat_time,repeat_duration,rx_path, rx_gain):
        if self.main.userTrig:
            self.main.userTrig = False
            self.main.changedF()  # just register set
            self.doSimpleRx(fsrc=fsrc,repeat_time=repeat_time,repeat_duration=repeat_duration,rx_path=rx_path, rx_gain=rx_gain)
            #IrisUtil.Interface_UpdateUserGraph(self, self.correlationSampes)  # update to user graph
            IrisUtil.Interface_UpdateUserGraph(self)

if __name__ == "__main__":
    test()
