"""
this file exposes some variable and function to host.py, which host a web server

export variables:
    version             # indicate the main.py version
    state               # now running state, could be "running", "run-pending", "stopped", "stop-pending"
    IrisCount           # the number of Iris module
    IrisSerialNums      # a vector recording all Iris module serial number
    loopDelay           # delay between one "loop()" end and next "loop()" begin, see loop() function below
    userTrig            # user press "trig" button, using in some mode
    userSing            # user press "sing" button
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
    reload()            # reload mode functions by file
"""

import time, random, GUI, traceback
from helperfuncs import LoopTimer
from helperfuncs import ModifyQueue
import modes.manager as modesm
modesm.import2main()  # support reload by call this twice
availableModes = modesm.makelist()
def reload():
    try:
        modesm.import2main()
        global availableModes
        availableModes = modesm.makelist()
    except Exception as e:
        GUI.error(str(e))
        print(traceback.format_exc())

version = "ArgosWebGui v0.3"
state = "stopped"
IrisCount = 0  # when it's 0, it could be used to test the web page functionality
IrisSerialNums = []
loopDelay = 0.5
userTrig = False
userSing = False
sampleData = None
sampleDataReady = False
extraInfos = {}
extraInfosReady = False
IrisObj = None
gainModified = ModifyQueue()
otherSystemSettings = {
    'QueryExtra': 'true'
}

# availableModes = ["sinusoid transceiver", "hdf5 analysis", "sinusoid dev-front"]
# mode = availableModes[0]
mode = "choose a mode"

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
    if IrisObj is not None and hasattr(IrisObj, 'getExtraInfos'):
        try:
            extraInfos = IrisObj.getExtraInfos()  # get information from Iris board
            extraInfosReady = True
        except Exception as e:  # just print, but not die
            GUI.error(str(e))
            print(traceback.format_exc())

extraInfosQueryTimer = LoopTimer(extraInfosQueryTimerdo, 2000, Always=True, running=False)

def loop(main, sleepFunc=None):
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
            try:
                Mode = modesm.modefiles[mode][0]
                IrisObj = Mode(main)
                state = 'running'
            except Exception as e:  # just print, but not die
                GUI.error(str(e))
                print(traceback.format_exc())
                state = 'stop-pending'
        changedF()
    elif state == 'stop-pending':
        extraInfosQueryTimer.stop()
        if IrisObj is not None:
            try:
                IrisObj = None
            except Exception as e:
                GUI.error(str(e))
                print(traceback.format_exc())
        state = 'stopped'
        changedF()
    elif state == 'running':
        if otherSystemSettings['QueryExtra'] == "true":
            extraInfosQueryTimer.loop()
        if IrisObj is not None and not gainModified.empty():  # set new gains during run-time (but not when using the stream, so it's safe)
            dic = {}
            while not gainModified.empty():
                a = gainModified.dequeue()
                dic[a[0]] = a[1]
            try:
                if hasattr(IrisObj, 'setGains'): IrisObj.setGains(dic)
            except Exception as e:  # just print, but not die
                GUI.error(str(e))
                print(traceback.format_exc())
            changedF()  # notify user
        if IrisObj is not None:
            try:
                IrisObj.loop()
            except Exception as e:  # just print, but not die
                GUI.error(str(e))
                print(traceback.format_exc())
                state = 'stop-pending'  # if running cause problem, just stop later

if __name__ == '__main__':
    print("run host.py with python3.x")
