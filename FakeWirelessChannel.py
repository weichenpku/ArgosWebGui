"""
this is for simulate any wireless channel, so that you can do experiments here
simply you can use "rxStreamFromSimpleTxAndOtherReceive_wy180805" and comment others in "rxStreamFromAllChannel"
or write other channel model by yourself!
"""

import numpy as np

Direction_RX = 0
Direction_TX = 1

# you can simulate channel in here, with all tx/rx streams known, you can build any channel here!
def rxStreamFromAllChannel(stream, devices, npobj, length):
    # return rxStreamFromConstantReceive_wy180805(stream, devices, npobj, length)
    return rxStreamFromSimpleTxAndOtherReceive_wy180805(stream, devices, npobj, length)

""" below are user-defined channel model """

# constant receive, this is a template function, you can grab information like this
def rxStreamFromConstantReceive_wy180805(stream, devices, npobj, length):
    serial = stream.serial  # this is the device serial number of this stream
    fakeDevice = devices[serial]  # this is FakeSoapySDR object
    for i in range(length): npobj[i] = 0  # set all to zero
    for this_serial in devices:  # traversal through all FakeSoapySDR devices initialized
        device = devices[this_serial]  # use this device's serial number to get FakeSoapySDR object
        for stream in device.streams:  # all FakeStream instants
            direction = stream.direction  # can be Direction_RX or Direction_TX
            data = stream.data  # data of this stream
            if direction == Direction_TX and data is not None:
                for i in range(min(length, len(data))):  # add data to rx, with 0 phase difference
                    npobj[i] = 0.666 + 0.233j

def rxStreamFromSimpleTxAndOtherReceive_wy180805(stream, devices, npobj, length):
    serial = stream.serial  # this is the device serial number of this stream
    fakeDevice = devices[serial]  # this is FakeSoapySDR object
    for i in range(length): npobj[i] = 0  # set all to zero
    for this_serial in devices:  # traversal through all FakeSoapySDR devices initialized
        device = devices[this_serial]  # use this device's serial number to get FakeSoapySDR object
        for stream in device.streams:  # all FakeStream instants
            direction = stream.direction  # can be Direction_RX or Direction_TX
            data = stream.data  # data of this stream
            if direction == Direction_TX and data is not None:
                for i in range(min(length, len(data))):  # add data to rx, with 0 phase difference
                    npobj[i] += data[i]  # simply add the together
