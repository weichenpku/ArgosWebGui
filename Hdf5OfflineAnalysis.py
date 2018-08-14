"""
parameters:

"""

import GUI, h5py, time, os, lts
import numpy as np

def main_test():  # you could play with this class here
    obj = Hdf5OfflineAnalysis()
    obj.changeFile("ArgosCSI-96x2-2016-03-31-15-59-02_Jian_right_to_left.hdf5")
    print(obj.givemesamples())

class Hdf5OfflineAnalysis:
    def __init__(self, sleepFunc = None):  # provide sleep function to print log information during long time computation
        self.filename = "NOFILE"
        self.info = {}
        self.fileOK = False  # indicate whether the file is OK
        self.antennas = [0]  # showing antennas
        self.showrange = (0,100)  # time range (frame number)
        self.csi = None
        self.channel = 0
        self.sleepFunc = sleepFunc

    def getExtraInfos(self):
        info = {}
        info["list"] = ["overview", "data", "info"]
        info["data"] = {}
        info["data"]["overview"] = [["file analyzed", self.filename]]
        files = os.listdir('./data/')
        info["data"]["data"] = [["%d" % i, files[i]] for i in range(len(files))]
        info["data"]["info"] = [[key, self.info[key]] for key in self.info]
        return info

    def givemesamples(self):
        # show antennas: self.antennas, with range self.showrange
        if self.fileOK:
            struct = []
            data = {}
            for i in range(self.info["num_mob_ant"]):  # multiple mobile receiver
                for j in self.antennas:
                    name = "ant%d-mob%d" % (j, i)
                    struct.append(name)
                    partdat = self.csi[self.showrange[0]:self.showrange[1], i, j, self.channel]
                    data["I-" + name] = [float(ele) for ele in partdat.real]
                    data["Q-" + name] = [float(ele) for ele in partdat.imag]
            sampleData = {"struct": struct, "data": data}
            return sampleData
        return None
    
    def changeFile(self, newfile, fft_size=64):
        self.fileOK = False
        self.info = {}
        GUI.log("hdf5 analysis file change to: " + newfile)
        filename = "NOFILE"
        if os.path.exists(newfile):
            filename = newfile
        elif os.path.exists(os.path.join('data', newfile)):
            filename = os.path.join('data', newfile)
        else:
            GUI.error("file doesn't exist")
            return None
        self.filename = newfile
        f = h5py.File(filename, 'r')
        self.info["samples_per_user"] = int(f.attrs['samples_per_user'])
        self.info["num_mob_ant"] = int(f.attrs['num_mob_ant'])
        self.info["frame_length"] = int(f.attrs['frame_length'])
        print(self.info)
        Pilot_Samples = f['Pilot_Samples']  # (1000, 96, 672, 2)

        # wy: use mapping, to save memory (in case memory is not enough)
        csi = np.memmap(
            os.path.join(os.path.dirname(__file__), 'data', 'temp.mymemmap'), 
            dtype='complex64', 
            mode='w+',
            shape=(Pilot_Samples.shape[0], self.info["num_mob_ant"]+1, Pilot_Samples.shape[1], 52)  # 52 is 64-12, in lts sequence, there're 12 zero, will be then deleted
        )
        self.csi = csi  # save to object
        chunk_num = csi.shape[0] // 1000  # divided into multiple chunks to reduce time waited (will inform user that "computer is not down, but just working hard :) ")
        GUI.log("there're %d chunks to work with, each about 10s, please wait patiently" % chunk_num)

        if self.sleepFunc: self.sleepFunc(0.1)
        for i in range(chunk_num):
            csi[i*1000:i*1000+1000] = np.mean(samps2csi(Pilot_Samples[i*1000:(i*1000+1000),:,:,:], self.info["num_mob_ant"]+1, samps_per_user=self.info["samples_per_user"]),2)
            GUI.log("chunk %d has finished, working on the next..." % i)
            if self.sleepFunc: self.sleepFunc(0.1)
        # dimensions: frames, users, antennas, subcarriers
        csi[chunk_num*1000:] = np.mean(samps2csi(Pilot_Samples[chunk_num*1000:csi.shape[0],:,:,:], self.info["num_mob_ant"]+1, samps_per_user=self.info["samples_per_user"]),2)
        GUI.log("all chunk has finished")

        self.info["timestep"] = float(self.info["frame_length"] / 20e6)	 # wy: a frame is 2ms, then 7664 frame is about 15s
        self.info["total_time"] = float(self.info["timestep"] * Pilot_Samples.shape[0])
        self.info["antenna count"] = int(Pilot_Samples.shape[1])
        self.info["frame count"] = int(Pilot_Samples.shape[0])
        self.info["OFDM channel"] = 52  # just inform user

        newantennacnt = 5
        if self.info["antenna count"] < newantennacnt: newantennacnt = self.info["antenna count"]
        self.antennas = [i for i in range(newantennacnt)]
        newrange = 100
        if self.info["frame count"] < newrange: newrange = self.info["frame count"]
        self.showrange = (0, newrange)
        self.channel = 0

        f.close()  # cannot close when still using Pilot_Samples var
        
        # csi axis are (7664: here are 1000 or under 1000, 3:'num_mob_ant'+1, 96:base station antenna, 64: fft_size, shifted)

        # noise is saved as the last user
        noise = csi[:,-1,:,:] 
        userCSI = csi[:,:-1,:,:]

        self.fileOK = True
    
    def setGains(self, gains):
        for gainKey in gains:
            a = gainKey.find('-')  # find from head, not the same with IrisSimpleRxTxSuperClass
            if a == -1: return None
            title = gainKey[:a]
            key = gainKey[a+1:]
            if title == "overview":
                if key == "hdf5":  # change the hdf5
                    self.changeFile(gains[gainKey])
            elif title == "specific":
                if not self.fileOK:
                    GUI.error("hdf5 file is not ready, cannot set \"specific\" options")
                else:
                    if key == "antennas":
                        splts = gains[gainKey].split(' ')
                        lsts = []
                        for num in splts:
                            try:
                                i = int(num)
                                if i < 0 or i >= self.info["antenna count"]: raise Exception()
                                lsts.append(i)
                            except:
                                GUI.error("set antenna: %d is not a number in range")
                        self.antennas = lsts
                    elif key == "data_range":
                        splts = gains[gainKey].split('-')
                        if len(splts) == 2:
                            try:
                                a = int(splts[0])
                                b = int(splts[1])
                                if a >= b: raise Exception()
                                if a < 0: raise Exception()
                                if b > self.info["frame count"]: raise Exception()
                                self.showrange = (a, b)  # update
                            except:
                                GUI.error("new range from %d to %d is invalid" % (a, b))
                        else:
                            GUI.error("cannot format range: \"%s\" like \"num-num\"" % gains[gainKey])
                    elif key == "OFDM_channel":
                        try:
                            ch = int(gains[gainKey])
                            if ch < 0 or ch >= self.info["OFDM channel"]: raise Exception()
                            self.channel = ch  # set
                        except:
                            GUI.error("cannot set OFDM channel to %s" % gains[gainKey])
    
    def nowGains(self):  # tell user what gains could be adjusted, as well as now values
        ret = {}
        ret["list"] = [["overview", ["hdf5"]], ["specific", ["antennas", "data_range", "OFDM_channel"]]]
        ret["data"] = {
            "overview-hdf5": self.filename,
            "specific-antennas": ' '.join([str(ele) for ele in self.antennas]),
            "specific-data_range": "%d-%d" % (self.showrange[0], self.showrange[1]),
            "specific-OFDM_channel": str(self.channel)
        }
        return ret

    def close(self):
        pass

def samps2csi(samps, num_users,samps_per_user=224, fft_size=64):
    offset = 15+32  # todo: use findlts
    chunkstart = time.time()

    # number of frames, number of antennas, number of samples in each frame, number of users, IQ
    usersamps = np.reshape(samps, (samps.shape[0],samps.shape[1],num_users,samps_per_user, 2) )	
    iq = np.empty((samps.shape[0],samps.shape[1],num_users,2,fft_size),dtype='complex64')
    for i in range(2): #2 seperate estimates
        iq[:,:,:,i,:]=(usersamps[:,:,:,offset+i*fft_size:offset+(i+1)*fft_size,0] + usersamps[:,:,:,offset+i*fft_size:offset+(i+1)*fft_size,1]*1j) * 2**-15
    # now iq's axis are (7664: here are 1000 or under 1000, 96:base station antenna, 3:'num_mob_ant'+1, 2: seperate estimates, 64: fft_size time scale)
    iq = iq.swapaxes(1,2)
    iq = iq.swapaxes(2,3)
    # now axis are (7664: here are 1000 or under 1000, 3:'num_mob_ant'+1, 2: seperate estimates, 96:base station antenna, 64: fft_size time scale)

    fftstart = time.time()
    csi = np.fft.fftshift(np.fft.fft(iq, fft_size, 4), 4) * lts.lts_freq  # * signal_max		
    endtime = time.time()
    print("chunk time: %f fft time: %f" % (fftstart - chunkstart, endtime -fftstart) )
    csi = np.delete(csi, [0,1,2,3,4,5,32,59,60,61,62,63], 4) #remove zero subcarriers
    return csi  # axis are (7664: here are 1000 or under 1000, 3:'num_mob_ant'+1, 2: seperate estimates, 96:base station antenna, 64: fft_size, shifted)

if __name__=='__main__':
    main_test()

