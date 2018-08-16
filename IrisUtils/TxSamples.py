########################################################################
## Receive a collection of samples and plot it to file
########################################################################

import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np
from optparse import OptionParser
import time
import os
import math
import sys
import signal
import threading
import pickle
import lts
import LTE5_re
import LTE5_im
from functools import partial

sdr = None
txStream = None
running = True

def printSensor(irises, *args):
    info = irises[0].getSensorInfo(*args)
    name, units = info.name, info.units
    out = name.ljust(25)
    for iris in irises:
        value = iris.readSensor(*args)
        out += ('%g'%float(value)).ljust(10) + " "
    out += units
    print(out)

def print_thread(sdr, info):
    global running
    while(running and "CBRS" in info["frontend"]):
        print('-'*80)
        printSensor([sdr], 'LMS7_TEMP')
        printSensor([sdr], 'ZYNQ_TEMP')
        printSensor([sdr], 'FE_TEMP')
        printSensor([sdr], SOAPY_SDR_TX, 0, 'TEMP')
        printSensor([sdr], SOAPY_SDR_TX, 1, 'TEMP')
        time.sleep(2)

def txsamples_app(args, srl, rate, freq, bw, ant, gain, numSamps, tddMode, lteMode):
    global sdr, txStream
    txSignal = np.empty(numSamps).astype(np.complex64)
    wbz = txSignal
    if lteMode:
        for i in range(numSamps):
            txSignal[i] = np.complex(LTE5_re.lte5i[i]/32768.0, LTE5_im.lte5q[i]/32768.0)
    else:
        ltsSym = lts.genLTS(upsample=1,cp=0)  
        txSignal = np.tile(ltsSym,numSamps/len(ltsSym)).astype(np.complex64)*.5

    sdr = SoapySDR.Device(dict(serial=srl))
    info = sdr.getHardwareInfo()

    #set clock rate first
    #clockRate = rate*8
    #sdr.setMasterClockRate(clockRate)
    print('setting PAD to %f ...' % gain)
    #set params on both channels
    for ch in [0, 1]:
        #sdr.setBandwidth(SOAPY_SDR_TX, ch, 10e6)
        sdr.setSampleRate(SOAPY_SDR_TX, ch, rate)
        if ("CBRS" in info["frontend"]):
            print("setting CBRS TX gains")
            sdr.setFrequency(SOAPY_SDR_TX, ch, freq)
            sdr.setFrequency(SOAPY_SDR_RX, ch, freq)
            sdr.setGain(SOAPY_SDR_TX, ch, 'ATTN', 0) #[-18,0] by 3
            sdr.setGain(SOAPY_SDR_TX, ch, 'PA1', 15) #[0|15]
            sdr.setGain(SOAPY_SDR_TX, ch, 'PA2', 0) #[0|15]
            sdr.setGain(SOAPY_SDR_TX, ch, 'PA3', 30) #[0|30]
            sdr.setGain(SOAPY_SDR_TX, ch, 'IAMP', 12) #[0,12]
            sdr.setGain(SOAPY_SDR_TX, ch, 'PAD', gain) #[-52,0]
        else:
            sdr.setFrequency(SOAPY_SDR_TX, ch, freq)
            sdr.setGain(SOAPY_SDR_TX, ch, 'PAD', gain) #[-52,0]
    for ch in [0, 1]:
        sdr.writeSetting(SOAPY_SDR_TX, ch, "CALIBRATE", 'SKLK')
    print("Set Frequency to %f" %sdr.getFrequency(SOAPY_SDR_TX, 0))
    #sdr.writeRegister("LMS7IC", 0x0108, 0xD58C) # CG_IAMP_TBB register 0x0108[15-10] -> 54
    if tddMode:
        print("setting up TDD mode ...")
        sdr.writeRegister("RFCORE", 104, numSamps)
        sdr.writeRegister("RFCORE", 108, 2) # numSyms
        sdr.writeRegister("RFCORE", 112, 2**32 -1)
        sdr.writeSetting("TDD_MODE", str(0x80000000))
        # write the schedule for base station
        for i in range(16):
            sdr.writeRegister("RFCORE", 116, i*256) # subframe 0
            sdr.writeRegister("RFCORE", 120, 1) # 01 replay: beacon
            sdr.writeRegister("RFCORE", 116, i*256+1) # subframe 1
            sdr.writeRegister("RFCORE", 120, 0) # 00 guard

        txStream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, [0, 1], dict(TDD="True"))
        sdr.activateStream(txStream)
        flags = SOAPY_SDR_END_BURST | SOAPY_SDR_TX_REPLAY
        sr = sdr.writeStream(txStream, [txSignal, wbz], numSamps, flags)
    else:
        #setup rxStreaming
        txStream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, [0, 1] , dict(REPLAY="true"))
        sdr.activateStream(txStream)
        flags = SOAPY_SDR_END_BURST
        #sr = sdr.writeStream(txStream, [txSignal, txSignal], numSamps, flags)
        sdr.writeStream(txStream, [txSignal, wbz], numSamps, flags)

    signal.signal(signal.SIGINT, partial(signal_handler, tddMode))
    if lteMode:
        print("Send LTE frame with length %d" % len(txSignal))
    else:
        print("Send LTS signal with length %d" % len(txSignal))
    if tddMode:
        sdr.writeSetting("TRIGGER_GEN", "")
    pth = threading.Thread(target=print_thread, args=(sdr, info))
    pth.start()
    signal.pause()


def signal_handler(tddMode, signal, frame):
    global sdr, txStream, running
    running = False
    if tddMode:
        print("printing number of frames")
        print("0x%X" % sdr.getHardwareTime(""))
        # ADC_rst, stops the tdd time counters
        sdr.writeRegister("IRIS30", 48, (1<<29)| 0x1)
        sdr.writeRegister("IRIS30", 48, (1<<29))
        sdr.writeRegister("IRIS30", 48, 0)
        for i in range(16*256):
            sdr.writeRegister("RFCORE", 116, i) # subframe 0
            sdr.writeRegister("RFCORE", 120, 0) # 
    #cleanup txStream
    print("Cleanup txStreams")
    sdr.deactivateStream(txStream)
    sdr.closeStream(txStream)


def main():
    parser = OptionParser()
    parser.add_option("--args", type="string", dest="args", help="device factory arguments", default="")
    parser.add_option("--rate", type="float", dest="rate", help="Tx sample rate", default=5e6)
    parser.add_option("--ant", type="string", dest="ant", help="Optional Tx antenna", default=None)
    parser.add_option("--txGain", type="float", dest="gain", help="Optional Tx gain (dB)", default=-25)
    parser.add_option("--freq", type="float", dest="freq", help="Optional Tx freq (Hz)", default=3.65e9)
    parser.add_option("--bw", type="float", dest="bw", help="Optional Tx filter bw (Hz)", default=None)
    parser.add_option("--numSamps", type="int", dest="numSamps", help="Num samples to receive", default=1024)
    parser.add_option("--serial", type="string", dest="serial", help="serial number of the device", default="RF3C000064")
    parser.add_option("--tdd", action="store_true", dest="tddMode", help="Setting up the radio in TDD mode ", default=False)
    parser.add_option("--LTE", action="store_true", dest="lteMode", help="Sending LTE waveform otherwise WiFi LTS", default=False)
    (options, args) = parser.parse_args()
    txsamples_app(
        args=options.args,
        srl=options.serial,
        rate=options.rate,
        freq=options.freq,
        bw=options.bw,
        ant=options.ant,
        gain=options.gain,
        numSamps=options.numSamps,
        tddMode=options.tddMode,
        lteMode=options.lteMode,
    )

if __name__ == '__main__': main()

