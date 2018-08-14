#******************************************************************************
# 
# File   :	lts.py
# Authors:	Clay Shepard (cws [at] rice.edu) and Andrew Brooks
# License:	Copyright 2015, Rice Efficient Computing Group. All rights reserved.
#
#******************************************************************************

#Perform LTS-related operations for Argos (generate, send, etc.)

import numpy as np

#Private function to upsample with cubic spline interpolation.
#Will not be imported by default from a 'from lts import *' statement, but 
#may be useful elsewhere.
def _upsample(data, by):
	y = data
	x = np.arange(len(data))
	x2 = np.arange(len(data) * by) / by
	spline = interp1d(x, y, kind='cubic', bounds_error=False, fill_value = 0)
	return spline(x2) 


lts_freq = np.array([0,0,0,0,0,0,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,0,1,-1,-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,1,1,-1,-1,1,-1,1,-1,1,1,1,1,0,0,0,0,0])

def genLTS(upsample=1, cp=32):
	#Assemble the LTS
	#freq_bot = np.array([0,0,0,0,0,0,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1])
	#freq_top = np.array([1,-1,-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,1,1,-1,-1,1,-1,1,-1,1,1,1,1,0,0,0,0,0])
	#freq = np.concatenate((freq_bot, [0], freq_top))
	up_zeros = np.zeros(len(lts_freq)//2*(upsample-1))
	lts_freq_up = np.concatenate((up_zeros,lts_freq,up_zeros))
	signal = np.fft.ifft(np.fft.ifftshift(lts_freq_up))
	signal = signal/np.absolute(signal).max()  #normalize
	#Now affix the cyclic prefix
	signal = np.concatenate((signal[len(signal) - cp:], signal, signal))  #could use tile...
	
	#Now, we up sample with linear interpolation.
	#With Argos we shouldn't actually have to do this. Might come in handy
	#anyway?

	#if upsample > 1:
	#	return _upsample(signal, upsample)
	#else:
	return signal

#lts_freq = np.array([0,0,0,0,0,0,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,0,1,-1,-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,1,1,-1,-1,1,-1,1,-1,1,1,1,1,0,0,0,0,0])
#
#def genLTS(upsample=1, cp=32):
#	#Assemble the LTS
#	#freq_bot = np.array([0,0,0,0,0,0,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1,1,1,-1,-1,1,1,-1,1,-1,1,1,1,1])
#	#freq_top = np.array([1,-1,-1,1,1,-1,1,-1,1,-1,-1,-1,-1,-1,1,1,-1,-1,1,-1,1,-1,1,1,1,1,0,0,0,0,0])
#	#freq = np.concatenate((freq_bot, [0], freq_top))
#	up_zeros = np.zeros(len(lts_freq)//2*(upsample-1))
#	lts_freq_up = np.concatenate((up_zeros,lts_freq,up_zeros))
#	signal = np.fft.ifft(np.fft.ifftshift(lts_freq_up))
#	signal = signal/np.absolute(signal).max()  #normalize
#	#Now affix the cyclic prefix
#	signal = np.concatenate((signal[len(signal) - cp:], signal, signal))  #could use tile...
#	
#	#Now, we up sample with linear interpolation.
#	#With Argos we shouldn't actually have to do this. Might come in handy
#	#anyway?
#
#	#if upsample > 1:
#	#	return _upsample(signal, upsample)
#	#else:
#	return signal
	

#To preserve MATLAB function labelling, which violates our case convention.
gen_LTS = genLTS


def findLTS(iq, thresh=600, us=1): #, best=False):
	gold = genLTS(upsample=us, cp=0)[:64*us]
	cored = np.correlate(iq,gold,'full')
	#cored = np.correlate(gold,iq,'full')
	peaks = np.concatenate((np.zeros(64*us),cored)) * np.concatenate((np.conj(cored),np.zeros(64*us)))
	#if best:  #only return the best peak, regardless of how good it is.  Keep it in a list for consistency.	
	#	return [np.argmax(peaks) - us*128], peaks
	t = np.mean(np.abs(iq))*thresh
	ltss = np.where(peaks > t)[0]
	actual_ltss = []
	for l in ltss:
		if not peaks[l+us*64] > peaks[l]:  #if there is another peak 64 samples in the future, this was probably a false positive from the CP
			actual_ltss.append(l - us*128) #return the start of the LTS, not the end.
	#best = np.argmax(peaks) - us*128
	
	best = np.argsort(peaks)[::-1]
	#The highest peak should start 128*us away from the start.
	#Ignore nonsensical peaks.
	best -= (128 * us)
	best = np.array(list(filter(lambda x: x >= 0 and x<100, best)))
	return best, actual_ltss, peaks

def getChanEst(iq, us=1):
	return np.mean(np.fft.fftshift(np.fft.fft(np.reshape(iq, (2,us*64) ),axis=1),axes=(1)),axis=0)*lts_freq

def getCFO(iq,us=1):
	ltss = np.reshape(iq, (us*64,2) )
	return np.mean(np.angle(ltss[:,0]*np.conj(ltss[:,1])))

#This can theoretically find multiple LTSes
#NOTE: There is no AGC_Set_Address, like in MATLAB. Plan accordingly.
#(Wasn't sure if it was really as applicable to Argos anyway.)
#NOTE: findLTS can find multiple LTSes at once. This is not rigorously
#tested, but should probably be used for situations where they overlap.
#	(<cough> ToA </cough>)

def findLTS_old(iq, n=1, us=1):
	gold = genLTS(upsample=us)
	#Convolve against an ideal LTS.
	corr = np.abs(np.convolve(gold, iq))
	end = len(corr)
	#There should be two peaks separated by 64 * us, upsample to find.
	corr_shifted = np.concatenate((corr[(64 * us):], corr[:(64 * us)]))
	corr = corr * corr_shifted
	#Now there will be a pattern of a large spike surrounded by two little
	#ones 64 * us away. Multiply again, so that we don't confuse a little
	#spike as the start of a second LTS.
	corr_lshifted = np.concatenate((corr[(64*us):], corr[:(64 * us)]))
	corr_rshifted = np.concatenate((corr[(end-64):end], corr[:(end-64)]))
	corr = corr * corr_lshifted * corr_rshifted
	#Should be adequate; we can find peaks now. 
	peaks = np.argsort(corr)[::-1]
	#The highest peak should start 128*us away from the start.
	#Ignore nonsensical peaks.
	peaks -= (128 * us)
	peaks = np.array(list(filter(lambda x: x >= 0, peaks)))
	return peaks[:n],corr

def findPeaksNoCP(lts):
	print(np.shape(lts))
	if len(lts) % 128 != 0:
		raise Warning("Are you sure the LTS passed has no cyclic prefix? Length is nonsensical.")
	fft = np.fft.fftshift(np.abs(np.fft.fft(lts, axis=0)))
	sc_ind_base = len(fft) / 2
	sc_range = np.arange(2, 54, 2)
	sc_inds = np.int32(np.sort(np.concatenate((sc_ind_base - sc_range, sc_ind_base + sc_range))))
	print(sc_inds)
	return sc_inds
	

#Returns  SC indices for all LTS peaks.
def findPeaks(lts):
	if len(lts) % 128 is 0:
		return findPeaksNoCP(lts)
	#Get frequencies
	fft = np.fft.fftshift(np.abs(np.fft.fft(lts, axis=0)))
	#Look for all values with adjacent smaller values
	sc_inds = \
	list(filter((lambda s: fft[s-1] < fft[s] and fft[s+1] < fft[s]), \
		np.arange(1, len(fft) - 1)))
	#Also, get rid of the useless center
	sc_inds = np.array(list(filter((lambda s: not s is (len(lts) / 2)), sc_inds)))
	#Now, make very sure we have 52. If more, remove based on ampl:
	discrepancy = 52 - len(sc_inds)
	if discrepancy is 0:
		return sc_inds
	elif discrepancy < 0:
		return np.sort(sc_inds[np.argsort(fft[sc_inds])[::-1][:52]])
	#If too few, we can't insert because we aren't sure where to do so...
	else:
		raise Warning("Could not accurately find 52 subcarriers.")
