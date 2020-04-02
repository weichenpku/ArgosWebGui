#!/usr/bin/python3
import numpy as np
import sys
sys.path.append("..")
from utils import IrisUtil
import scipy.io as sio

def batch_trans():
	argc = len(sys.argv)
	if (argc<3):
		print('[ERROR] arg is not enough')
		print('[ERROR] arg2: directory of npy files; arg3: epoch num')
		return 0
	path = sys.argv[1]
	num = sys.argv[2]
	for idx in range(int(num)):
		subdir = path+'epoch'+str(idx)+'/'
		print(subdir)
		trans_one_file(path=subdir)

def trans_one_file(path):
	datafile = path+'data.npy'
	devfile = path+'msg.npy'
	tsfile = path+'ts.npy'
	srfile = path+'srate.npy'
	rawdata = np.load(datafile)
	rx_serials_ant = np.load(devfile)
	ts = np.load(tsfile)
	srate = np.load(srfile)

	data={}
	for r,serial_ant in enumerate(rx_serials_ant):
		serial, ant = IrisUtil.Format_SplitSerialAnt(serial_ant)
		cdat = [samps for samps in rawdata[r]]
		if ant == 2:
			for antt in [0,1]:
				data["%s_%d_I" % (serial, antt)] = [float(e.real) for e in cdat[antt]]
				data["%s_%d_Q" % (serial, antt)] = [float(e.imag) for e in cdat[antt]]
		else:
			data[serial + "_I"] = [float(e.real) for e in cdat[0]]
			data[serial + "_Q"] = [float(e.imag) for e in cdat[0]]
	data['ts']=ts
	data['srate']=srate

	matfile = path+'rx0.mat'
	sio.savemat(matfile,data)
	#print(data.keys())


if __name__ == "__main__":
	batch_trans()