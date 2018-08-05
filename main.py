"""
this file exposes some variable and function to host.py, which host a web server

export variables:
    version             # indicate the main.py version
    state               # now running state, could be "running", "run-pending", "stopped", "stop-pending"
    IrisCount           # the number of Iris module
    IrisSerialNums      # a vector recording all Iris module serial number
    loopDelay           # delay between one "loop()" end and next "loop()" begin, see loop() function below
    mode                # run different mode, avaliable mode is below
    userTrig            # user press "trig" button, using in some mode
    sampleRate          # sample rate, default is 10e6
    extraInfos          # other information, such as the temperature of each Iris, or so
    extraInfosReady     # tell the server to send infos to others
    IrisObj             # object of Iriss, could be None, if not, host will send gain settings to web browsers

    sampleData          # rx/tx sample data
    sampleDataReady     # if it's ready
    changed             # when any export varibles is modified, set this to True, and will be broadcast to all users

export functions:
    setup()              # running all the time you wish to, it could be a loop to check
    loop()               # running all the time, you could check stream input/output, with delay 
"""

import time, random
from helperfuncs import LoopTimer

version = "ArgosWebGui v0.1"
state = "stopped"
IrisCount = 0  # when it's 0, it could be used to test the web page functionality
IrisSerialNums = []
loopDelay = 0.5
mode = "user-trig-one-send-other-recv"  #  "user-trig-one-send-other-recv"
userTrig = False
sampleData = None
sampleDataReady = False
extraInfos = {}
extraInfosReady = False
IrisObj = None

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

ifSimulateMode = False

def extraInfosQueryTimerdo(timer):
    global extraInfos
    global extraInfosReady
    if IrisObj is not None:
        pass
    else:  # 模拟状态，随便传过去些东西
        ret = {}
        for i in range(IrisCount):
            ret["LMS7-%d" % i] = 11111
            ret["Zynq-%d" % i] = 22222
            ret["Frontend-%d" % i] = 33333
            ret["PA0-%d" % i] = 44444
            ret["PA1-%d" % i] = 55555
        extraInfos = ret
        extraInfosReady = True
extraInfosQueryTimer = LoopTimer(extraInfosQueryTimerdo, 2000, Always=True)

def loop():
    global state
    global IrisCount
    global IrisSerialNums
    global changed
    global ifSimulateMode
    global mode
    global sampleData
    global userTrig
    global sampleDataReady
    if state == 'run-pending':
        if IrisCount == 0:
            ifSimulateMode = True
            IrisCount = 3
            IrisSerialNums = ["foo", "bar", "lalala"]
        else:
            from UserTrigOneSendOtherRecv import UserTrigOneSendOtherRecv
            IrisObj = UserTrigOneSendOtherRecv(serials=IrisSerialNums)  # new object
        state = 'running'
        changedF()
    elif state == 'stop-pending':
        # deinitialize operations
        state = 'stopped'
        changedF()
    elif state == 'running':
        extraInfosQueryTimer.loop()
        if mode == "user-trig-one-send-other-recv":  # one send, the other receive
            if ifSimulateMode and userTrig:
                onesend = IrisSerialNums[0]
                otherrecv = IrisSerialNums[1:]
                samples = {}
                for i in range(IrisCount):
                    samples["I%d" % i] = [random.random() for i in range(1024)]
                    samples["Q%d" % i] = [random.random() for i in range(1024)]
                sampleData = samples
                sampleDataReady = True
                userTrig = False
            elif userTrig:
                if userTrig:
                    print(IrisObj)


