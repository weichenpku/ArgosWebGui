"""
this file is to analyze data recorded from LTE_OneRepeator_SyncWatcher_DevFE_RevB_180902
only support the JSON file saved from browser, in ArgosWebGui
"""

# since starting a new engine really consume time, it's recommended to connect to a shared MATLAB session
# to shared the session in MATLAB GUI, just call this in MATLAB ------------------  `matlab.engine.shareEngine`
# I found that if there's no shared sessions, it will automatically create one and then delete, which really consume time (about 5s)

import json, matlab.engine, sys, os
import numpy as np
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import modes.IrisUtil as IrisUtil

sender = "0313-0"
receiver = "0283-0"
fileName = r"C:\users\37754\Desktop\lastgraph_180902_2131.json"
eng = matlab.engine.connect_matlab()

# for better speed, the elements are all stored in MATLAB workspace, so you can jump through some time-consuming steps
steps = {
    "load raw data": True,
    "load correlation seq": True,
    "do correlation": True,  # consume much time
    "show sendcorr": False,
    "show recvcorr": True
}

def main():
    if steps["load raw data"]:
        with open(fileName) as f:
            data = json.load(f)
        senderseq = np.array(data["data"]["I-%s" % sender], dtype=np.complex64) + 1.0j * np.array(data["data"]["Q-%s" % sender], dtype=np.complex64)
        receiverseq = np.array(data["data"]["I-%s" % receiver], dtype=np.complex64) + 1.0j * np.array(data["data"]["Q-%s" % receiver], dtype=np.complex64)
        _sv("senderseq", matlab.double(senderseq.tolist(), is_complex=True))
        _sv("receiverseq", matlab.double(receiverseq.tolist(), is_complex=True))
    
    if steps["load correlation seq"]:
        _eq("corrseq", "senderseq(11:110)")
        _eq("recvcorrseq", "upsample(corrseq, 6)")  # 9Ms/s, 1.5MS/s, so do 6 times upsample
    
    if steps["do correlation"]:
        _eq("sendcorr", "xcorr(senderseq, conj(corrseq))")
        _eq("recvcorr", "xcorr(receiverseq, conj(recvcorrseq))")
    
    if steps["show sendcorr"]:
        _do("plot(abs(sendcorr))")
    
    if steps["show recvcorr"]:
        _do("plot(abs(recvcorr))")

def _sv(name, element):
    eng.workspace[name] = element

def _eq(out, command):
    eng.eval("%s = %s;" % (out, command), nargout=0)

def _do(command):
    eng.eval("%s;" % command, nargout=0)

if __name__ == "__main__":
    main()
