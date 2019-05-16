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
import threading

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
    obj = LTE_Receiver(main, conf_dict=conf_dict)
    
    numSamples = conf_dict['numSamples']
    gain_dict = {
        "parameters-showSamples": "65536",
        "parameters-numSamples":numSamples, # recvNum (should be less than 65536)
    }
    if (conf_dict['receiver_master']['port']!='0'):  gain_dict[conf_dict['receiver_master']['serial']+"-1-rx-rxGain"] = rx_gain
    if (conf_dict['receiver_master']['port']!='1'):  gain_dict[conf_dict['receiver_master']['serial']+"-0-rx-rxGain"] = rx_gain
    for idx in range(int(conf_dict['receivernum'])-1):
        if (conf_dict['receiver'][idx]['port']!='0'): gain_dict[conf_dict['receiver'][idx]['serial']+"-1-rx-rxGain"] = rx_gain
        if (conf_dict['receiver'][idx]['port']!='1'): gain_dict[conf_dict['receiver'][idx]['serial']+"-0-rx-rxGain"] = rx_gain
    print(gain_dict)
    obj.setGains(gain_dict)
    
    '''
    buflen = int(numSamples)
    for idx in range(int(conf_dict['receivernum'])):
        if (conf_dict['receiver'][idx]['port']!='2'): emptybuf=[np.zeros(buflen, np.complex64)]
        else: emptybuf=[np.zeros(buflen, np.complex64),np.zeros(buflen, np.complex64)]
        streamingbuffer[0].append(emptybuf)
        streamingbuffer[1].append(emptybuf)
    '''
    print()
    print('[SOAR] parameters : value')
    paras = obj.nowGains()
    for para,value in paras['data'].items():
        print(para,':',value)
    print()

    obj.loop(conf_dict['filesource'], repeat_time=rx_repeat_time, repeat_duration=rx_repeat_duration, rx_path=rx_path, rx_gain=rx_gain)

class streamingReceiveThread(threading.Thread):
    def __init__(self,LTE_Receiver):
        threading.Thread.__init__(self)
        self.LTE_Receiver = LTE_Receiver
    def run(self):
        global threadlock
        global producing_ptr
        global consuming_flag
        print('start streaming reveiving')
        epoch=0
        while (True):
                # read stream
                flag = IrisUtil.Process_ReadFromRxStream(self.LTE_Receiver)
                if (flag==False):
                    print('(streamingReceiveThread) warning: Process_ReadFromRxStream() return false')
                    continue
                #IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
                threadlock.acquire()
                if (consuming_flag==False):
                    producing_ptr = 1-producing_ptr
                data_ptr = producing_ptr
                threadlock.release()

                if (data_ptr==-1):
                    break
                print(data_ptr)
                recvdata = IrisUtil.Process_SaveData(self.LTE_Receiver,datadest=databuffer[data_ptr])
                epoch=epoch+1
                
        # deactive
        IrisUtil.Process_RxDeactive(self.LTE_Receiver)

        
class LTE_Receiver:
    def __init__(self, main, conf_dict):
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
        self.rate = eval(conf_dict['srate'])
        self.bw = eval(conf_dict['bandwidth'])
        IrisUtil.Init_CreateBasicGainSettings(self, bw=self.bw, freq=eval(conf_dict['carrier_freq']), dcoffset=True, txrate=self.rate, rxrate=self.rate)

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


        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
        IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime_Streaming(self, rx_delay = 0)


        receiving_thread = streamingReceiveThread(self)
        receiving_thread.start() 
        # sleep to wait
        #IrisUtil.Process_WaitForTime_NoTrigger(self)
        
        global threadlock
        global producing_ptr
        global consuming_flag

        epoch=-1
        while (True):                
            while (True):
                print('*********************')
                print('cmd input:',end=' ')
                nextstep = input()
                if (nextstep in ['q','r','n','s']):
                    break
                else:
                    print(' q - quit\n r - repeat this epoch\n n - save and next epoch\n s - show receive signal \n other - help')

            if (nextstep == 'q'):
                break    
            if (nextstep == 'n'):
                epoch=epoch+1

            rx_dir = rx_path+'epoch'+str(epoch)
            if os.path.exists(rx_dir)==False:
                os.makedirs(rx_dir)
            
            # save data from databuffer to epoch
            threadlock.acquire()
            consuming_flag = True
            data_ptr=1-producing_ptr
            threadlock.release()
            
            recvdata = databuffer[data_ptr]
            if (nextstep != 's'):
                print("save data in"+rx_path+"epoch"+str(epoch)+"/rx0.mat")
                sio.savemat(rx_path+"epoch"+str(epoch)+"/rx0.mat",recvdata)

            show_peak = True
            if show_peak:
                maxpeak = 0
                peak_info = {}
                for chan in recvdata:
                    chanpeak = np.max(np.abs(recvdata[chan]))
                    peak_info[chan] = chanpeak
                    if (chanpeak > maxpeak): maxpeak = chanpeak
                for chan in sorted(peak_info.keys()):
                    print('AGC: peak of', chan, 'is', peak_info[chan])
                print('AGC: maxpeak is', maxpeak)  

            threadlock.acquire()
            consuming_flag = False
            threadlock.release()

            

        threadlock.acquire()
        consuming_flag = True
        producing_ptr = -1
        threadlock.release()
        receiving_thread.join()   
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
    #global_value
    threadlock = threading.Lock()
    producing_ptr = 0
    consuming_flag = 0
    databuffer = [{},{}]

    test()
