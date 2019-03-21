#!/usr/bin/python3

import IrisUtil
import time
import numpy as np
import scipy as sp
import scipy.io as sio

def Singletone_loadmat(datafile,rx_serial,port):
    data_dict = sio.loadmat(datafile)
    sig_i = data_dict[rx_serial+'_'+port+'_I'][0]
    sig_q = data_dict[rx_serial+'_'+port+'_Q'][0]
    sig=sig_i+1j*sig_q
    return sig[:19200]

def Singletone_verify(sig,idx):
    sig_f = np.fft.fft(np.array(sig))
    z1 = sig_f[idx]
    z2 = sig_f[-idx]
    # print('z1,z2=',z1,z2)
    sinr = np.log(abs(z1)/abs(z2))/np.log(10)*10
    return sinr