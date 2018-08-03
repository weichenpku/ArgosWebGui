"""
this file exposes some variable and function to host.py, which host a web server

export variables:
    version             # indicate the main.py version
    state               # now running state, could be "running", "run-pending", "stopped", "stop-pending"
    IrisCount           # the number of Iris module
    IrisSerialNums      # a vector recording all Iris module serial number
    loopDelay           # delay between one "loop()" end and next "loop()" begin, see loop() function below

    changed             # when any export varibles is modified, set this to True, and will be broadcast to all users

export functions:
    setup()              # running all the time you wish to, it could be a loop to check
    loop()               # running all the time, you could check stream input/output, with delay 
"""

import time

version = "ArgosWebGui v0.1"
state = "stopped"
IrisCount = 0  # when it's 0, it could be used to test the web page functionality
IrisSerialNums = []
loopDelay = 0.5

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

def 


timers = []
timers.append(LoopTimer(heartbeat, 2000, Always=True))

def loop():
    global state
    global IrisCount
    global IrisSerialNums
    global changed
    global ifSimulateMode
    if state == 'run-pending':
        if IrisCount == 0:
            ifSimulateMode = True
            IrisCount = 3
            IrisSerialNums = ["foo", "bar", "lalala"]
        else:
            # TODO initialze
            pass
        state = 'running'
        changedF()
    elif state == 'stop-pending':
        # deinitialize operations
        state = 'stopped'
        changedF()
    elif state == 'running':

