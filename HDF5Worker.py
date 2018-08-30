import os, time

def test():
    # print(HDF5Worker.LsDir())
    worker = HDF5Worker("ArgosCSI-96x2-2016-03-31-15-53-27_Jian_left_to_right.hdf5", mode='r')
    # worker = HDF5Worker("Recorder_BurstRecord_DevFE_RevB_180829_2018-08-29_18-01-51.hdf5", mode='r')
    # worker = HDF5Worker("test.hdf5", mode='r')
    # worker.Write_Attr({"a": "foo", "b": 666})
    worker.printStructure(verbose=True)

    

class HDF5Worker:
    def __init__(self, fileName, mode='r', rPath='data'):
        import h5py  # load run-time, if throw exception, will be caught and print to GUI
        if mode not in {'r', 'w', 'w-'}: raise ValueError("mode not recognized")
        absFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), rPath, fileName)
        if mode == 'r':
            self.h5file = h5py.File(absFilePath, 'r')
            self.attrs = {}  # copy them out
            for key in self.h5file.attrs:
                self.attrs[key] = self.h5file.attrs[key]
            self.keys = [key for key in self.h5file.keys()]
        elif mode == 'w' or mode == 'w-':
            self.h5file = h5py.File(absFilePath, mode)
            self.create_dataset = self.h5file.create_dataset
    
    def __del__(self):
        if hasattr(self, "h5file") and self.h5file is not None:
            self.h5file.close()
    
    def printStructure(self, verbose=False):  # only use in read only mode, otherwise exception will be raised
        print("--- attrs:")
        print([key for key in self.attrs])
        if verbose:
            for key in self.attrs:
                print("    %s:" % key, self.attrs[key])
        print("--- keys:")
        print(self.keys)
        print("--- group info:")
        for key in self.keys:
            print(self.h5file[key])
    
    def Write_Attr(self, attrs: dict):
        for key in attrs:
            self.h5file.attrs[key] = attrs[key]
    
    @staticmethod
    def LsDir(rPath='data'):
        dirinfo = []
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rPath)
        for f in os.listdir(path):
            if f[-5:] == '.hdf5':
                filepath = os.path.join(path, f)
                fsize = os.path.getsize(filepath)
                ct = os.path.getctime(filepath)
                dirinfo.append([f, fsize, ct])
        dirinfo.sort(key = lambda x: -x[2])  # sort by create time, the earliest one at end, latest at head
        for ele in dirinfo:
            ele[2] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ele[2])) 
        return dirinfo
    
    

if __name__ == '__main__':
    test()
