#!bin/bash
systemctl stop NetworkManager
ip addr add 192.168.1.12/24 dev enp0s31f6
ssh soar@192.168.1.10 
