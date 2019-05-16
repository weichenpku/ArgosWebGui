#!/bin/sh

# use this file to set rmem_max parameter of Ubuntu16.04 system, since it's 208kb by default
cat /proc/sys/net/core/rmem_default
cat /proc/sys/net/core/rmem_max

# 16MB
# sudo sysctl -w net.core.rmem_max=16777216

# 67MB = 0x4000000
sudo sysctl -w net.core.rmem_max=67108864 
