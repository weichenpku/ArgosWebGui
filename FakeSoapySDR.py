"""
This is a FAKE SoapySDR file, just for debugging system without Iris or with saved data
I use this class for GUI testing wy@180804
"""

SOAPY_SDR_RX = 0
SOAPY_SDR_TX = 1

SOAPY_SDR_CF32 = None
SOAPY_SDR_TIMEOUT = None
SOAPY_SDR_WAIT_TRIGGER = 0
SOAPY_SDR_END_BURST = 0

import time
import numpy as np

fakeDeviceInstants = {}

from FakeWirelessChannel import rxStreamFromAllChannel

class FakeRetClass:
    def __init__(self, ret=1):
        self.ret = ret

class FakeStream:
    def __init__(self, serial, direction=-1):
        self.serial = serial
        self.direction = direction
        self.data = None
        self.name = "uninitialized Stream"
    def __str__(self):
        return self.name

class Device:
    def __init__(self, attr):
        print("Device construction called")
        self.serial = attr["serial"]
        global fakeDeviceInstants  # to model wireless channel
        fakeDeviceInstants[self.serial] = self
        print(fakeDeviceInstants)
        self.streams = [FakeStream(self.serial), FakeStream(self.serial)]
    
    def deleteref(self):
        global fakeDeviceInstants
        if self.serial in fakeDeviceInstants: fakeDeviceInstants.pop(self.serial)

    def __del__(self):
        print("Device destruction called")
    
    def setMasterClockRate(self, clockRate):
        print("%s set clockRate to %d" % (self.serial, clockRate))
    
    def setFrequency(self, RXTX, chan, typ, freq):
        print("%s (%s:%d) set freqency %s to %d" % (self.serial, "TX" if RXTX==1 else "RX", chan, typ, freq))
    
    def setAntenna(self, RXTX, chan, ant):
        print("%s (%s:%d) set antenna to %s" % (self.serial, "TX" if RXTX==1 else "RX", chan, ant))
    
    def setDCOffsetMode(self, RXTX, chan, mode):
        print("%s (%s:%d) set DC offset mode to %s" % (self.serial, "TX" if RXTX==1 else "RX", chan, "True" if mode else "False"))

    def setSampleRate(self, RXTX, chan, rate):
        print("%s (%s:%d) set sample rate to %d" % (self.serial, "TX" if RXTX==1 else "RX", chan, rate))
    
    def setBandwidth(self, RXTX, chan, bw):
        print("%s (%s:%d) set bandwidth to %d" % (self.serial, "TX" if RXTX==1 else "RX", chan, bw))
    
    def setGain(self, RXTX, chan, key, val=None):
        if val is None:
            print("%s (%s:%d) set gain global to %f" % (self.serial, "TX" if RXTX==1 else "RX", chan, key))
        else:
            print("%s (%s:%d) set gain \"%s\" to %f" % (self.serial, "TX" if RXTX==1 else "RX", chan, key, val))

    def setHardwareTime(self, time, condition):
        print("%s set hardware time %d under \"%s\" condition" % (self.serial, time, condition))
    
    def getHardwareTime(self, condition):
        print("%s getting hardware time" % self.serial)
        return time.time()  # make sure every time call is different
    
    def writeSetting(self, key, val, v2=None, v3=None):
        if v2 is None:
            print("%s write setting \"%s\" to \"%s\"" % (self.serial, key, val))
        else:
            print("%s write setting \"%s\" \"%s\" \"%s\" \"%s\"" % (self.serial, key, val, v2, v3))
    
    def readSensor(self, *arg):
        # print("%s try read sensor %s" % (self.serial, str(arg)))
        return 233.0
        
    def setupStream(self, RXTX, coding, chanlst, attr):
        print("%s (%s:%s) set stream with attr: %s" % (self.serial, "TX" if RXTX==1 else "RX", str(chanlst), str(attr)))
        streamName = "(%s:%s)" % ("TX" if RXTX==1 else "RX", str(chanlst))
        for chan in chanlst:
            self.streams[chan].direction = RXTX
            self.streams[chan].name = streamName
        return streamName

    def readStream(self, stream, npLst:list, length, timeoutUs=0):
        print("%s's stream %s read stream of length %d" % (self.serial, stream, length))
        for npidx in range(len(npLst)):
            for chan in (0,1):
                if self.streams[chan].name == stream:
                    # so here is the rx stream, channel is 'chan', serial number is 'self.serial', all other devices are in global 'fakeDeviceInstants'
                    # you can define your own channel in FakeWirelessChannel.py
                    global fakeDeviceInstants
                    rxStreamFromAllChannel(self.streams[chan], fakeDeviceInstants, npLst[npidx], length)
        return FakeRetClass(length)

    def writeStream(self, stream, npLst:list, length, flags):
        print("%s's stream %s write stream of lenth %d, flags are %s" % (self.serial, stream, length, str(flags)))
        for npidx in range(len(npLst)):
            for chan in (0,1):
                if self.streams[chan].name == stream:
                    self.streams[chan].data = npLst[npidx]  # just save it
        return FakeRetClass(length)

    def activateStream(self, stream, *arg):
        print("%s activate stream %s with arg: %s" % (self.serial, stream, str(arg)))
    
    def deactivateStream(self, stream):
        print("%s deactivate stream %s" % (self.serial, stream))
    
    def readStreamStatus(self, stream, timeoutUs=0):
        print("%s read state of stream %s" % (self.serial, stream))
        return "status-I-AM-FAKE-:)"

    def closeStream(self, stream):
        print("%s close stream: %s" % (self.serial, stream))

    

    