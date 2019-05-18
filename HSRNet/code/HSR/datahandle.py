#!/usr/bin/python3
import matlab.engine, sys, os
import numpy as np


eng = matlab.engine.connect_matlab()

def test():
    argc = len(sys.argv)
    if (argc<3):
        print('[ERROR] arg is not enough')
        print('[ERROR] arg1: name of rxdir; arg2: name of configure file')
        return 0    
    path = '../../matlab_process/'
    cmd = 'cd ' + path + ';'
    print(cmd) 
    _do(cmd)
    cmd = "realtime_csi_calculate(\'%s\',\'%s\');" % (sys.argv[1],sys.argv[2])
    print(cmd)
    _do(cmd)

def _sv(name, element):
    eng.workspace[name] = element

def _eq(out, command):
    eng.eval("%s = %s;" % (out, command), nargout=0)

def _do(command):
    eng.eval("%s;" % command, nargout=0)

if __name__ == "__main__":
    test()