########################################################################
## Simple signal generator for testing transmit
########################################################################

import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np
from optparse import OptionParser
import time
import os
import math
import signal
import threading
import matplotlib.pyplot as plt

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

def siggen_app(args, srl, rate, ampl, freq, bbfreq, waveFreq, txGain):
    global sdr, txStream

    sdr = SoapySDR.Device(dict(driver="iris", serial = srl))
    info = sdr.getHardwareInfo()
    sdr.setMasterClockRate(8*rate)
    amplFixed = int(ampl*(1 << 15))
    if bbfreq > 0:
        print("using cording to generate a sinusoid ...") 
    for c in [0, 1]:
        sdr.setFrequency(SOAPY_SDR_TX, c, freq)
        sdr.setFrequency(SOAPY_SDR_RX, c, freq)
        sdr.setSampleRate(SOAPY_SDR_TX, c, rate)
        if bbfreq > 0: sdr.setFrequency(SOAPY_SDR_TX, c, "BB", bbfreq) 
        if ("CBRS" in info["frontend"]):
            print("set CBRS front-end gains")
            #sdr.writeSetting(SOAPY_SDR_TX, c, 'TX_ENB_OVERRIDE', 'true')
            #sdr.writeSetting(SOAPY_SDR_TX, c, 'TSP_TSG_CONST', str(amplFixed))
            sdr.setGain(SOAPY_SDR_TX, c, "ATTN", 0)
            sdr.setGain(SOAPY_SDR_TX, c, "PA1", 15)
            sdr.setGain(SOAPY_SDR_TX, c, "PA2", 0)
            sdr.setGain(SOAPY_SDR_TX, c, "PA3", 30)
            sdr.setGain(SOAPY_SDR_TX, c, "IAMP", 12)
        sdr.setGain(SOAPY_SDR_TX, c, "PAD", txGain)
        #sdr.writeSetting(SOAPY_SDR_TX, c, "CALIBRATE", '')
        sdr.writeSetting(SOAPY_SDR_TX, c, "CALIBRATE", 'SKLK')

    #sdr.writeRegister("LMS7IC", 0x0108, 0xD58C) # CG_IAMP_TBB register 0x0108[15-10] -> 54
    #sdr.writeRegister("LMS7IC", 0x0108, 0x958C) # 37
    #sdr.writeRegister("LMS7IC", 0x0108, 0x198C) # 12

    Ts = 1/rate
    if waveFreq is None: waveFreq = rate/50
    numSamps = int(20*rate/waveFreq) # 20 period worth of samples
    s_freq = waveFreq
    s_time_vals = np.array(np.arange(0,numSamps)).transpose()*Ts
    tone = np.exp(s_time_vals*1j*2*np.pi*s_freq).astype(np.complex64)*ampl
    if bbfreq > 0:  
        tone = np.array([0]*numSamps, np.complex64)   # use with cordic  
        tone += .5

    txStream = sdr.setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, [0, 1],dict(REPLAY='true'))
    flags = SOAPY_SDR_END_BURST
    sdr.activateStream(txStream)
    sr = sdr.writeStream(txStream, [tone, tone], len(tone), flags)
    if sr.ret != len(tone):
        print("Bad write!!! %s" % sdr.getHardwareInfo()['serial'])
        print(sr)

    #fig = plt.figure(figsize=(20, 8), dpi=100)
    #ax1 = fig.add_subplot(1, 1, 1)
    #ax1.plot(np.real(tone), label='pilot i')
    #ax1.plot(np.imag(tone), label='pilot q')
    #plt.show()

    signal.signal(signal.SIGINT, signal_handler)
    pth = threading.Thread(target=print_thread, args=(sdr, info))
    pth.start()
    print("ctrl-c to stop ...")
    signal.pause()

def signal_handler(signal, frame):
    global sdr, txStream, running
    running = False
    #cleanup txStream
    print("Cleanup txStreams")
    if txStream is not None:
        sdr.deactivateStream(txStream)
        sdr.closeStream(txStream)

def main():
    parser = OptionParser()
    parser.add_option("--args", type="string", dest="args", help="device factor arguments", default="")
    parser.add_option("--rate", type="float", dest="rate", help="Tx and Rx sample rate", default=5e6)
    parser.add_option("--ampl", type="float", dest="ampl", help="Tx digital amplitude rate", default=0.5)
    parser.add_option("--txGain", type="float", dest="txGain", help="Tx gain (dB)", default=-30)
    parser.add_option("--freq", type="float", dest="freq", help="Tx RF freq (Hz)", default=3.65e9)
    parser.add_option("--bbfreq", type="float", dest="bbfreq", help="Lime Baseband frequency", default=0)
    parser.add_option("--waveFreq", type="float", dest="waveFreq", help="Baseband waveform freq (Hz)", default=None)
    parser.add_option("--serial", type="string", dest="serial", help="serial number of the device", default="0240")
    (options, args) = parser.parse_args()
    siggen_app(
        args=options.args,
        srl=options.serial,
        rate=options.rate,
        ampl=options.ampl,
        freq=options.freq,
        bbfreq=options.bbfreq,
        waveFreq=options.waveFreq,
        txGain=options.txGain,
    )

if __name__ == '__main__': main()
