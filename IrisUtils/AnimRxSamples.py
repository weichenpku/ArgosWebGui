########################################################################
## Receive a collection of samples and plot it to file
########################################################################

import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy as np
from optparse import OptionParser
import time
import datetime
import os
import math
import sys
import pickle
import matplotlib
matplotlib.rcParams.update({'font.size': 10})
import matplotlib.pyplot as plt
from matplotlib import animation
import lts
#from DataRecorder import *
sdr = None
rxStream = None
rxSamps = None
timeScale = None
recorder = None
FIG_LEN = int(sys.argv[1])   
# tag = sys.argv[2]
record = False 
overwrite = False
filename = "rx" 
sampsRx = None 
#create plots
fig = plt.figure(figsize=(20, 8), dpi=100)
fig.subplots_adjust(hspace=.5, top=.85)
ax1 = fig.add_subplot(2, 1, 1)
ax1.grid(True)
#ax1.set_title('Waveform capture')
title = ax1.text(0.5, 1, '|', ha="center")
ax1.set_ylabel('Amplitude (units)')
line1, = ax1.plot([], [], label='AI', animated=True)
line2, = ax1.plot([], [], label='AQ', animated=True)
ax1.set_ylim(-1, 1)
ax1.set_xlim(0, FIG_LEN)
ax1.legend(fontsize=10)
ax2 = fig.add_subplot(2, 1, 2)
ax2.grid(True)
ax2.set_xlabel('Time (ms)')
ax2.set_ylabel('Amplitude (units)')
line3, = ax2.plot([], [], label='A Corr I', animated=True)
line4, = ax2.plot([], [], label='A Corr Q', animated=True)
ax2.set_ylim(-10, 10)
ax2.set_xlim(0, FIG_LEN)
ax2.legend(fontsize=10)
def init():
    line1.set_data([], [])
    line2.set_data([], [])
    line3.set_data([], [])
    line4.set_data([], [])
    return line1, line2, line3, line4

def write_to_file(name,arr, overwrite):
    """Save complex numpy array val to files prefixed with name in binary twos-complement binary format with num_bits."""
    fi = None
    if overwrite: 
        fi = open(name+'.bin', 'wb')
    else:
        fi = open(name+'.bin', 'ab')
    for a in arr:
        pickle.dump(a,fi)
    fi.close()

def read_from_file(name,leng,offset=0):
    """Save complex numpy array val to files prefixed with name in binary twos-complement binary format with num_bits."""
    fi = open(name+'.bin', 'rb')
    for k in range(offset):
        pickle.load(fi)
    arr = np.array([0]*leng, np.uint32)
    for a in range(leng):
        #fi.write(np.binary_repr(a,width=num_bits))
        arr[a] = pickle.load(fi)
    fi.close()
    return arr

def rxsamples_app(args, srl, rate, freq, bw, ant, gain, clockRate, numSamps, waveSamps, out):
    global sdr, rxStream, timeScale, sampsRx, recorder
    sdr = SoapySDR.Device(dict(serial=srl))
    info = sdr.getHardwareInfo()

    #set clock rate first
    #if clockRate is None: sdr.setMasterClockRate(rate*8)
    #else: sdr.setMasterClockRate(clockRate)
    #set params on both channels
    for ch in [0, 1]:
        #sdr.setBandwidth(SOAPY_SDR_RX, ch, 30e6)
        #sdr.setBandwidth(SOAPY_SDR_TX, ch, 30e6)
        sdr.setSampleRate(SOAPY_SDR_RX, ch, rate)
        #sdr.setSampleRate(SOAPY_SDR_TX, ch, rate)
        sdr.setFrequency(SOAPY_SDR_RX, ch, freq)
        #sdr.setFrequency(SOAPY_SDR_TX, ch, freq)
        if ("CBRS" in info["frontend"]):
            sdr.setGain(SOAPY_SDR_RX, ch, 'LNA2', gain[5]) #[0,17]
            sdr.setGain(SOAPY_SDR_RX, ch, 'LNA1', gain[4]) #[0,17]
            sdr.setGain(SOAPY_SDR_RX, ch, 'ATTN', gain[3]) #[-18,0]
        sdr.setGain(SOAPY_SDR_RX, ch, 'LNA', gain[2]) #[0,30]
        sdr.setGain(SOAPY_SDR_RX, ch, 'TIA', gain[1]) #[0,12]
        sdr.setGain(SOAPY_SDR_RX, ch, 'PGA', gain[0]) #[-12,19]
        sdr.setAntenna(SOAPY_SDR_RX, ch, "TRX")
        sdr.setDCOffsetMode(SOAPY_SDR_RX, ch, True)
    for ch in [0, 1]:
        sdr.writeSetting(SOAPY_SDR_RX, ch, "CALIBRATE", 'SKLK')
    #    sdr.writeSetting(SOAPY_SDR_RX, ch, "CALIBRATE", '')
    print("Set Frequency to %f" %sdr.getFrequency(SOAPY_SDR_RX, 0))
    #sdr.writeSetting("TDD_MODE", str(0x0)) # enable when TDD mode is used. earlier versions had a bug that needed this

    #setup rxStreaming
    rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0, 1] )
    #request an rx burst as an example
    #repeat activateStream and readStream() for each burst needed

    #cleanup rxStream
    #print("Cleanup rxStreams")
    #sdr.deactivateStream(rxStream)
    #sdr.closeStream(rxStream)
    step = 1
    timeScale = np.arange(0, numSamps*step, numSamps)
    sampsRx = [np.zeros(numSamps, np.complex64), np.zeros(numSamps, np.complex64)]

    anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=100, interval=100, blit=True)

    #fig.show()
    plt.show()
    #if out is not None: fig.savefig(out)
    #plt.close(fig)

def animate(i):
    global sdr, rxStream, timeScale, sampsRx, filename, record, overwrite, recorder
    #read samples into this buffer
    buff0 = sampsRx[0]
    buff1 = sampsRx[1]
    sdr.activateStream(rxStream,
        SOAPY_SDR_END_BURST, #flags
        0, #timeNs (dont care unless using SOAPY_SDR_HAS_TIME)
        buff0.size) #numElems - this is the burst size
    sr = sdr.readStream(rxStream, [buff0, buff1], buff0.size)
    if sr.ret != buff0.size: print("Read RX burst of %d, requested %d" % (sr.ret,buff0.size))
    #dc removal
    for i in [0, 1]: sampsRx[i] -= np.mean(sampsRx[i])
    a, b, peaks = lts.findLTS(sampsRx[1])
    # if record: 
    #     frame = np.empty((2,buff0.size),dtype='complex64')
    #     frame[0] = sampsRx[0]
    #     frame[1] = sampsRx[1]
    #     recorder.save_frame(sampsRx, sr.timeNs) 
    # else:
    #     write_to_file(filename+str(0), sampsRx[0], True)
    #     write_to_file(filename+str(1), sampsRx[1], True)
    write_to_file(filename+str(0), sampsRx[0], True)
    write_to_file(filename+str(1), sampsRx[1], True)
    rssi0 = 10*np.log10(np.mean(np.power(np.abs(sampsRx[0]),2)))
    rssi1 = 10*np.log10(np.mean(np.power(np.abs(sampsRx[1]),2)))
    title.set_text("Measured RSSI: (%f, %f)"%(rssi0, rssi1))
    print("Measured RSSI: (%f, %f)"%(rssi0, rssi1))
    line1.set_data(range(buff0.size), np.real(sampsRx[1]))
    line2.set_data(range(buff0.size), np.imag(sampsRx[1]))
    line3.set_data(range(buff0.size), np.real(peaks[:buff1.size])) #np.real(sampsRx[1]))
    line4.set_data(range(buff0.size), np.imag(peaks[:buff1.size])) #np.imag(sampsRx[1]))
    return line1, line2, line3, line4, title,

# def replay(name,leng):
#     print("file name %s, batch length %s"%(name, str(leng)))
#     h5file = h5py.File(name,'r')
#     samples = h5file['Samples']
#     leng = h5file.attrs['frame_length']
#     numFrame = samples.shape[0]
#     avg_rssi = [0, 0]
#     rssi = [0, 0]
#     for i in range(numFrame):
#         sampsRx = samples[i,:,:]
#         rssi[0] = np.mean(np.power(np.abs(sampsRx[0]),2)) 
#         rssi[1] = np.mean(np.power(np.abs(sampsRx[1]),2)) 
#         log_rssi = 10*np.log10(rssi)
#         avg_rssi[0] += rssi[0]
#         avg_rssi[1] += rssi[1]
#         print("Measured RSSI from batch %d: (%f, %f)"%(i, log_rssi[0], log_rssi[1]))
#     avg_rssi = 10*np.log10([x/numFrame for x in avg_rssi])
#     print("Average Measured RSSI: (%f, %f)"%(avg_rssi[0], avg_rssi[1]))
   
   
def main():
    global file0, file1, record, overwrite, recorder
    parser = OptionParser()
    parser.add_option("--args", type="string", dest="args", help="device factory arguments", default="")
    parser.add_option("--rate", type="float", dest="rate", help="Tx sample rate", default=5e6)
    parser.add_option("--ant", type="string", dest="ant", help="Optional Rx antenna", default=None)
    parser.add_option("--lna", type="float", dest="lna", help="Lime Chip Rx LNA gain [0:30](dB)", default=20.0)
    parser.add_option("--tia", type="float", dest="tia", help="Lime Chip Rx TIA gain [0,3,9,12] (dB)", default=0.0)
    parser.add_option("--pga", type="float", dest="pga", help="Lime Chip Rx PGA gain [-12:19] (dB)", default=0.0)
    parser.add_option("--lna1", type="float", dest="lna1", help="BRS/CBRS Front-end LNA1 gain stage [0:33] (dB)", default=25)
    parser.add_option("--lna2", type="float", dest="lna2", help="BRS/CBRS Front-end LNA2 gain [0:17] (dB)", default=15)
    parser.add_option("--attn", type="float", dest="rxattn", help="BRS/CBRS Front-end ATTN gain stage [-18:6:0] (dB)", default=0.0)
    parser.add_option("--latitude", type="float", dest="latitude", help="BRS/CBRS Front-end ATTN gain stage [-18:6:0] (dB)", default=0.0)
    parser.add_option("--longitude", type="float", dest="longitude", help="BRS/CBRS Front-end ATTN gain stage [-18:6:0] (dB)", default=0.0)
    parser.add_option("--elevation", type="float", dest="elevation", help="BRS/CBRS Front-end ATTN gain stage [-18:6:0] (dB)", default=0.0)
    parser.add_option("--freq", type="float", dest="freq", help="Optional Rx freq (Hz)", default=3.65e9)
    parser.add_option("--bw", type="float", dest="bw", help="Optional Tx filter bw (Hz)", default=None)
    parser.add_option("--clockRate", type="float", dest="clockRate", help="Optional clock rate (Hz)", default=None)
    parser.add_option("--numSamps", type="int", dest="numSamps", help="Num samples to receive", default=FIG_LEN)
    parser.add_option("--waveSamps", type="int", dest="waveSamps", help="Num samples to time plot", default=16384)
    parser.add_option("--out", type="string", dest="out", help="Path to output image file", default=None)
    parser.add_option("--serial", type="string", dest="serial", help="serial number of the device", default="0182")
    #parser.add_option("--record", action="store_true", dest="record", help="record received signal", default=False)
    #parser.add_option("--overwrite", action="store_true", dest="overwrite", help="overwrite when recording received signal", default=False)
    #parser.add_option("--replay", action="store_true", dest="replay", help="readback existing file and report RSSI", default=False)
    (options, args) = parser.parse_args()
    now = datetime.datetime.now()
    rxsamples_app(
        args=options.args,
        srl=options.serial,
        rate=options.rate,
        freq=options.freq,
        bw=options.bw,
        ant=options.ant,
        gain=[options.pga,options.tia,options.lna,options.rxattn,options.lna1,options.lna2], 
        clockRate=options.clockRate,
        numSamps=options.numSamps,
        waveSamps=options.waveSamps,
        out=options.out,
    )
    # record = options.record 
    # overwrite = options.overwrite
    # if record:
    #    filename ="rx"+'%1.3f'%(float(options.freq)/1e9)+'GHz_'+tag+'.hdf5'
    #    recorder = DataRecorder(sys.argv[2],options.serial,options.freq,options.lna,options.pga,options.tia,options.lna1,options.lna2,options.rxattn,options.numSamps,options.latitude,options.longitude,options.elevation)
    #    recorder.init_h5file(filename=filename)
    # if not options.replay:
    #    rxsamples_app(
    #        args=options.args,
    #        srl=options.serial,
    #        rate=options.rate,
    #        freq=options.freq,
    #        bw=options.bw,
    #        ant=options.ant,
    #        gain=[options.pga,options.tia,options.lna,options.rxattn,options.lna1,options.lna2], 
    #        clockRate=options.clockRate,
    #        numSamps=options.numSamps,
    #        waveSamps=options.waveSamps,
    #        out=options.out,
    #    )
    # else:
    #    replay(sys.argv[2],int(sys.argv[1]))        
if __name__ == '__main__': 
    main()
