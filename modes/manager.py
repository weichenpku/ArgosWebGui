"""
this file is to manage all modes automatically, and import utilities for these modes
"""

import os, sys, importlib

def main():
    print("If you run this file, it will list all available mode")
    loadModeFiles()
    global modefiles
    print("import files are: [%d]" % len(modefiles))
    for f in modefiles:
        print('----', f, "(mode class is: \"%s\")" % modefiles[f][0])
    print("avaliable list is:", makelist())

modefiles = {}
def loadModeFiles(prefix=''):
    global modefiles
    for key in modefiles:
        importlib.reload(modefiles[key][1])
    modefiles = {}  # clear the older one
    for f in os.listdir(os.path.dirname(os.path.abspath(__file__))):  # get all files in this folder
        if f[-3:] == '.py' and f != "manager.py":
            Name = f[:-3]
            ModeFile = __import__(prefix + Name)
            if prefix != '':  # I don't know why it's like this... otherwise this will be <module 'modes' (namespace)>
                ModeFile = getattr(ModeFile, Name)
            if not hasattr(ModeFile, Name): Mode = None  # for utilization file, this could be None
            else: Mode = getattr(ModeFile, Name)
            modefiles[Name] = (Mode, ModeFile)

def getModeByName(name):
    return modefiles[name][1]

def import2main():  # only called by main.py
    modefiles = loadModeFiles(prefix='modes.')

def makelist():
    ret = []
    global modefiles
    for key in modefiles:
        if modefiles[key][0] is not None:
            ret.append(key)
    return ret

if __name__ == "__main__":
    main()
