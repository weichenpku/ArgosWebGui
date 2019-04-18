systemctl stop NetworkManager
ip link set dev enp2s0f0 up
ip link set dev enp2s0f1 up
ip link set dev enp2s0f2 up
ip link set dev enp2s0f3 up
ip link set dev enp1s0f0 up
ip link set dev enp1s0f1 up
ip link set dev enp1s0f2 up
ip link set dev enp1s0f3 up
ip link set dev enp0s31f6 up
SoapySDRUtil --find
