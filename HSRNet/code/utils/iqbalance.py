#!/usr/bin/python3

import IrisUtil
import DSPUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio
import threading
import SoapySDR

tx_serial = "RF3E000021"
tx_port = "0"
rx_serial = "RF3E000010"
rx_port = "1"

tx_gain = "40"
rx_gain = "40"

verify=  True #  False #    
# if verify is False
test_tx = True # test_rx = not test_tx

tx_amp =   1.2438
tx_angle =   -0.1383
rx_amp = 0.9639
rx_angle = -0.1335

class Singletone_tx:
    def __init__(self):
        class FakeMain:
            def __init__(self,tx_serial):
                self.IrisSerialNums = [tx_serial+"-2-Tx-1"] # serial-chan-TX/RX-trigger
        
        self.main = FakeMain(tx_serial)
        
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Assert_Tx_Required(self)
        IrisUtil.Format_LoadTimeWaveForm(self, '../../refdata/generation/test_data/tone.csv', 0.9)
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 1.92e6*2
        IrisUtil.Init_CreateBasicGainSettings(self, rate=self.rate, bw=5e6, freq=3.5e9, dcoffset=True)
        IrisUtil.Init_CreateTxStreams_RevB(self)
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
        IrisUtil.Gains_AddPostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)
        IrisUtil.Init_CreateRepeatorTimeWaveformSequence(self)

    def __del__(self):
        print('Iris destruction called')
        # IrisUtil.Deinit_SafeTxStopRepeat(self)
        IrisUtil.Deinit_SafeDelete(self)

    def setGains(self, gains):
        IrisUtil.Gains_HandleSelfParameters(self, gains)
        IrisUtil.Gains_SetBasicGains(self, gains)

    def setbalance(self,scale,angle):
        IrisUtil.Setting_ChangeIQBalance(self, txscale=scale,txangle=angle)

    def doSimpleTx(self,repeat_time):
        # activate
        IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
        IrisUtil.Process_TxActivate_WriteFlagAndMultiFrameToTxStream_UseHasTime(self,repeat_time=repeat_time)
        IrisUtil.Process_TxDeactive(self)

    def loop(self,repeat_time):
        self.doSimpleTx(repeat_time=repeat_time)
        #IrisUtil.Interface_UpdateUserGraph(self, self.correlationSampes)  # update to user graph
        IrisUtil.Interface_UpdateUserGraph(self)    


class Singletone_rx:
    def __init__(self):
        class FakeMain:
            def __init__(self,rx_serial):
                self.IrisSerialNums = [rx_serial+"-2-Rx-1"] # serial-chan-TX/RX-trigger
        
        self.main = FakeMain(rx_serial)
        IrisUtil.Assert_ZeroSerialNotAllowed(self)
        IrisUtil.Format_UserInputSerialAnts(self)
        IrisUtil.Init_CollectSDRInstantNeeded(self, clockRate=80e6)
        IrisUtil.Init_CreateDefaultGain_WithDevFE(self)
        self.rate = 1.92e6*2
        IrisUtil.Init_CreateBasicGainSettings(self, bw=5e6, freq=3.5e9, dcoffset=True, txrate=self.rate, rxrate=self.rate)
        IrisUtil.Init_CreateRxStreams_RevB(self)
        IrisUtil.Init_SynchronizeTriggerClock(self)
        self.numSamples = 19200  # could be changed during runtime
        self.showSamples = 30000  # init max show samples
        self.alignOffset = 0
        self.selfparameters = {
            "numSamples": int, 
            "showSamples": int, 
            # "txSelect": lambda x: IrisUtil.Format_CheckSerialAntInTx(self, x),  # use closure to send "self" object in
            "alignOffset": int
        }
        IrisUtil.Gains_AddPostcodeGains(self)
        IrisUtil.Gains_LoadGainKeyException(self, rxGainKeyException=IrisUtil.Gains_GainKeyException_RxPostcode)

    def __del__(self):
        print('Iris destruction called')
        IrisUtil.Deinit_SafeTxStopRepeat(self)
        IrisUtil.Deinit_SafeDelete(self)

    def setGains(self, gains):
        IrisUtil.Gains_HandleSelfParameters(self, gains)
        IrisUtil.Gains_SetBasicGains(self, gains)
    
    def setbalance(self,scale,angle):
        IrisUtil.Setting_ChangeIQBalance(self, rxscale=scale,rxangle=angle)

    def doSimpleRx(self,repeat_time):
        # prepare work, create tx rx buffer
        IrisUtil.Process_CreateReceiveBuffer(self)
        IrisUtil.Process_ClearStreamBuffer(self)
        # activate
        for i in range(repeat_time):
            IrisUtil.Process_ComputeTimeToDoThings_UseHasTime(self, delay = 10000000, alignment = 0)
            IrisUtil.Process_RxActivate_WriteFlagToRxStream_UseHasTime(self, rx_delay = 0)
            # sleep to wait
            IrisUtil.Process_WaitForTime_NoTrigger(self)
            # read stream
            IrisUtil.Process_ReadFromRxStream(self)
            IrisUtil.Process_HandlePostcode(self)  # postcode is work on received data
            recvdata = IrisUtil.Process_SaveData(self)
            print(type(recvdata))
            sio.savemat("../../rxdata/rx"+str(i)+".mat",recvdata)
            time.sleep(0.02)
        # deactive
        IrisUtil.Process_RxDeactive(self)

    def loop(self,repeat_time):
        self.doSimpleRx(repeat_time=repeat_time)
        #IrisUtil.Interface_UpdateUserGraph(self, self.correlationSampes)  # update to user graph
        IrisUtil.Interface_UpdateUserGraph(self)    

class tx_thread(threading.Thread):
    def __init__(self,obj,scale,angle):
        threading.Thread.__init__(self)
        self.obj=obj
        self.scale=scale
        self.angle=angle
    def run(self):
        self.obj.setbalance(self.scale,self.angle)
        self.obj.loop(repeat_time=500)
        print('tx finish')

class rx_thread(threading.Thread):
    def __init__(self,obj,scale,angle):
        threading.Thread.__init__(self)
        self.obj=obj
        self.scale=scale
        self.angle=angle
    def run(self):
        self.obj.setbalance(self.scale,self.angle)
        self.obj.loop(repeat_time=10)
        print('rx finish')

def test():
    mean_sinr=0
    filenum=0
    for idx in range(10):
        datafile = '../../rxdata/rx'+str(idx)+'.mat'
        print('file is ',datafile)
        rx_sig = DSPUtil.Singletone_loadmat(datafile,rx_serial,rx_port)
        sinr = DSPUtil.Singletone_verify(rx_sig,int(60000/200))
        print('sinr = ',sinr)
        if max(np.real(rx_sig))-min(np.real(rx_sig))>0.01 and sinr>1:
            mean_sinr += sinr
            filenum += 1   
    if filenum>0:
        return (mean_sinr/filenum,filenum)
    else:
        return (0,filenum)

def main(obj1,obj2,txscale,txangle,rxscale,rxangle):
    thread1=tx_thread(obj1,txscale,txangle)
    thread2=rx_thread(obj2,rxscale,rxangle)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    print("trx finish")
    return test()

if __name__ == "__main__":
    step_amp = 0.1
    step_angle = 0.1
    init_amp = 1
    init_angle = 0    
    last_ans = 0
    total_step = 50
    ans_data = []
    ans = dict()

    

    if not verify:
        if test_tx:
            tx_amp=init_amp
            tx_angle=init_angle
        else:
            rx_amp=init_amp
            rx_angle=init_angle

    obj1 = Singletone_tx()
    obj1.setGains({
            "parameters-txSelect": tx_serial+"-"+tx_port,
            tx_serial+"-0-tx-txGain": tx_gain,
            tx_serial+"-1-tx-txGain": tx_gain,
    })
    obj2 = Singletone_rx()
    obj2.setGains({
            "parameters-showSamples": "60928",
            "parameters-numSamples":"60000", # recvNum (should be less than 60928)
            rx_serial+"-0-rx-rxGain": rx_gain,
            rx_serial+"-1-rx-rxGain": rx_gain
    })
    


    if (verify):
        main(obj1,obj2,tx_amp,tx_angle,rx_amp,rx_angle)
        exit()


    for i in range(total_step):
        ret=main(obj1,obj2,tx_amp,tx_angle,rx_amp,rx_angle)
        p1=round(tx_amp,2)
        p2=round(tx_angle,2)
        p3=round(rx_amp,2)
        p4=round(rx_angle,2)
        if (not (p1,p2,p3,p4) in ans):  ans[(p1,p2,p3,p4)]=ret[0]
        elif (ret[0]>ans[(p1,p2,p3,p4)]): ans[(p1,p2,p3,p4)]=ret[0]

        ans_data.append([tx_amp, tx_angle, rx_amp, rx_angle, ret[0], ret[1]])
        print(ret)
        if ret[0]>last_ans:
            last_ans = ret[0]
            if test_tx:
                tx_angle += step_angle
            else:
                rx_angle += step_angle
        else:
            last_ans = ret[0]
            step_angle = step_angle/-2
            if test_tx:
                tx_angle += step_angle
            else:
                rx_angle += step_angle
        if (abs(step_angle)<0.001):
            break   



    for i in range(total_step):
        ret=main(obj1,obj2,tx_amp,tx_angle,rx_amp,rx_angle)
        p1=round(tx_amp,2)
        p2=round(tx_angle,2)
        p3=round(rx_amp,2)
        p4=round(rx_angle,2)
        if (not (p1,p2,p3,p4) in ans):  ans[(p1,p2,p3,p4)]=ret[0]
        elif (ret[0]>ans[(p1,p2,p3,p4)]): ans[(p1,p2,p3,p4)]=ret[0]
            
        ans_data.append([tx_amp, tx_angle, rx_amp, rx_angle, ret[0], ret[1]])
        print(ret)
        if ret[0]>last_ans:
            last_ans = ret[0]
            if test_tx:
                tx_amp += step_amp
            else:
                rx_amp += step_amp
        else:
            last_ans = ret[0]
            step_amp = step_amp/-2
            if test_tx:
                tx_amp += step_amp    
            else:
                rx_amp += step_amp
        if (abs(step_amp)<0.001):
            break    

     

    #for i in range(total_step):
    #    main()

    print(step_amp)
    print(step_angle)
    print(ans)
    para0=0
    value0=0
    for para,value in ans.items():
        if value>value0:
            value0=value
            para0=para
    print(para0,value0)

    #print(ans_data)
    sio.savemat("../../rxdata/iqbalance_result.mat",{'data':ans_data})