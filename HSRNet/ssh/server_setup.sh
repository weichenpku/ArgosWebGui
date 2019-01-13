#!bin/bash
ip addr flush dev enp0s31f6
systemctl stop NetworkManager
ip addr add 192.168.1.10/24 dev enp0s31f6
