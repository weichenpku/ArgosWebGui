"""
this file exposes some variable and function to host.py, which host a web server

export variables:
    version             # indicate the main.py version
    state               # now running state, could be "running", "run-pending", "stopped", "stop-pending"
    IrisCount           # the number of Iris module
    IrisSerialNums      # a vector recording all Iris module serial number
    loopDelay           # delay between one "loop()" end and next "loop()" begin, see loop() function below
    userTrig            # user press "trig" button, using in some mode
    sampleRate          # sample rate, default is 10e6
    extraInfos          # other information, such as the temperature of each Iris, or so
    extraInfosReady     # tell the server to send infos to others
    IrisObj             # object of Iriss, could be None, if not, host will send gain settings to web browsers

    sampleData          # rx/tx sample data
    sampleDataReady     # if it's ready
    changed             # when any export varibles is modified, set this to True, and will be broadcast to all users

    mode                # run different mode, avaliable mode is below
    availableModes      # a list of mode strings which you could handle it in "loop" function, user could NOT change this during no "stopped" state

    gainModified        # ModifyQueue object, record gain modification and keep thread safety
    
    otherSystemSettings # other user settings which is structed as map

export functions:
    setup()             # running all the time you wish to, it could be a loop to check
    loop()              # running all the time, you could check stream input/output, with delay 
"""

import time, random, GUI
from helperfuncs import LoopTimer
from helperfuncs import ModifyQueue
from IrisSimpleRxTxSuperClass import IrisSimpleRxTxSuperClass

version = "ArgosWebGui v0.2"
state = "stopped"
IrisCount = 0  # when it's 0, it could be used to test the web page functionality
IrisSerialNums = []
loopDelay = 0.5
userTrig = False
sampleData = None
sampleDataReady = False
extraInfos = {}
extraInfosReady = False
IrisObj = None
gainModified = ModifyQueue()
otherSystemSettings = {
    'QueryExtra': 'true'
}

availableModes = ["sinosuid transceive", "hdf5 analysis", "sinosuid dev-front"]
mode = availableModes[0]

changed = False
def changedF():  # when any export varible is modified, call this function
    global changed
    changed = True

def setup():
    global state
    global IrisCount
    global IrisSerialNums
    global changed
    print("setup called")

def extraInfosQueryTimerdo(timer):
    global extraInfos
    global extraInfosReady
    if IrisObj is not None:
        extraInfos = IrisObj.getExtraInfos()  # get information from Iris board
        extraInfosReady = True
    else:  # error, inform user
        extraInfos = {
            "list": ["error"], 
            "data": {
                "error": [["Iris object", "None"], ["Please", "ask developer"]]
            }
        }
        extraInfosReady = True
extraInfosQueryTimer = LoopTimer(extraInfosQueryTimerdo, 2000, Always=True, running=False)

def loop(sleepFunc=None):
    global state
    global IrisCount
    global IrisSerialNums
    global changed
    global mode
    global sampleData
    global userTrig
    global sampleDataReady
    global IrisObj
    global otherSystemSettings
    if state == 'run-pending':
        print(mode)
        if mode == "choose a mode":
            GUI.error("select a mode to run")
            state = "stop-pending"            
        else:
            if mode == "hdf5 analysis":
                from Hdf5OfflineAnalysis import Hdf5OfflineAnalysis
                IrisObj = Hdf5OfflineAnalysis(sleepFunc=sleepFunc)  # new object
                IrisCount = 0
                IrisSerialNums = []
                state = 'running'
                # extraInfosQueryTimer.restart()
            elif IrisCount == 0:  # the mode below requires IrisCount > 0
                GUI.error("at least one Iris is required to run")
                state = "stop-pending"
            elif mode == "sinosuid transceive":
                from SinosuidTransceiveWithPrecode import SinosuidTransceiveWithPrecode
                try:
                    IrisObj = SinosuidTransceiveWithPrecode(serials=IrisSerialNums)  # new object
                    state = 'running'
                    extraInfosQueryTimer.restart()
                except RuntimeError as e:
                    IrisObj = None
                    GUI.error("RuntimeError: %s" % str(e))
                    state = 'stop-pending'
            elif mode == "sinosuid dev-front":
                from SinosuidTransceiveForDevFrontendRevB import SinosuidTransceiveForDevFrontendRevB
                try:
                    IrisObj = SinosuidTransceiveForDevFrontendRevB(serials=IrisSerialNums)  # new object
                    state = 'running'
                    extraInfosQueryTimer.restart()
                except RuntimeError as e:
                    IrisObj = None
                    GUI.error("RuntimeError: %s" % str(e))
                    state = 'stop-pending'
        changedF()
    elif state == 'stop-pending':
        # deinitialize operations
        extraInfosQueryTimer.stop()
        if IrisObj is not None:
            # IrisObj.close()  # close api is deleted
            IrisObj = None
        state = 'stopped'
        changedF()
    elif state == 'running':
        if otherSystemSettings['QueryExtra'] == "true":
            extraInfosQueryTimer.loop()
        if IrisObj is not None and  not gainModified.empty():  # set new gains during run-time (but not when using the stream, so it's safe)
            dic = {}
            while not gainModified.empty():
                a = gainModified.dequeue()
                dic[a[0]] = a[1]
            IrisObj.setGains(dic)
            changedF()  # notify user
        if mode == "sinosuid transceive" or mode == "sinosuid dev-front":  # some send, others receive
            if userTrig:
                userTrig = False
                ((tx_serials_ant, tx_complex_data), (rx_serials_ant, rx_complex_data)) = IrisObj.doSimpleRxTx()
                struct = []
                for r,serial_ant in enumerate(tx_serials_ant + rx_serials_ant):
                    serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
                    if ant == 2:
                        struct.append(serial + '-0')
                        struct.append(serial + '-1')
                    else:
                        struct.append(serial_ant)
                data = {}
                for r,serial_ant in enumerate(tx_serials_ant):
                    serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
                    cdat = tx_complex_data[r]
                    if ant == 2:
                        for antt in [0,1]:
                            data["I-%s-%d" % (serial, antt)] = [float(e.real) for e in cdat[antt]]
                            data["Q-%s-%d" % (serial, antt)] = [float(e.imag) for e in cdat[antt]]
                    else:
                        data["I-" + serial_ant] = [float(e.real) for e in cdat[0]]
                        data["Q-" + serial_ant] = [float(e.imag) for e in cdat[0]]
                for r,serial_ant in enumerate(rx_serials_ant):
                    serial, ant = IrisSimpleRxTxSuperClass.splitSerialAnt(serial_ant)
                    cdat = rx_complex_data[r]
                    if ant == 2:
                        for antt in [0,1]:
                            data["I-%s-%d" % (serial, antt)] = [float(e.real) for e in cdat[antt]]
                            data["Q-%s-%d" % (serial, antt)] = [float(e.imag) for e in cdat[antt]]
                    else:
                        data["I-" + serial_ant] = [float(e.real) for e in cdat[0]]
                        data["Q-" + serial_ant] = [float(e.imag) for e in cdat[0]]
                sampleData = {"struct": struct, "data": data}
                sampleDataReady = True
        if mode == "hdf5 analysis":
            if userTrig:
                userTrig = False
                ret = IrisObj.givemesamples()
                if ret is not None:
                    sampleData = ret
                    sampleDataReady = True
                else:
                    GUI.error("trigger failed, the hdf5 file may have error")
