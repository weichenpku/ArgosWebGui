"""
this file is to manage all modes automatically, and import utilities for these modes
"""

import os, sys

def main():
    print("If you run this file, it will list all available mode")
    loadModeFiles()
    global modefiles
    print("import files are: [%d]" % len(modefiles))
    for f in modefiles:
        print(f, "(shown mode as: \"%s\")" % modefiles[f][0])

modefiles = None
def loadModeFiles(prefix=''):
    global modefiles
    modefiles = {}  # clear the older one
    print(os.path.dirname(__file__))
    for f in os.listdir(os.path.dirname(__file__)):  # get all files in this folder
        print(f)
        if f[-3:] == '.py' and f != "manager.py":
            Name = f[:-3]
            if Name[-4:] == 'Util': continue # it's util files
            ModeFile = __import__(prefix + Name)
            if prefix != '':  # I don't know why it's like this... otherwise this will be <module 'modes' (namespace)>
                ModeFile = getattr(ModeFile, Name)
            if not hasattr(ModeFile, Name): continue
            Mode = getattr(ModeFile, Name)
            print(ModeFile)
            print(Mode)
            print(dir(Mode))
            if not hasattr(Mode, 'Title'): continue
            Title = getattr(Mode, 'Title')
            print("title: ", Title)
            modefiles[Name] = (Title, Mode)

def getModeByName(name):
    return modefiles[name][1]

def import2main():  # only called by main.py
    modefiles = loadModeFiles(prefix='modes.')


if __name__ == "__main__":
    main()
