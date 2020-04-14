clear; close all;
path = '4.3/pos3_2.5m/990/';
%path = 'simu/restart_tx0/';
path = 'phase_dis/distance2/';

file = [path 'epoch30/rx0.mat']; 

refidx = 200000;

device1 = 'RF3E000022';
device2 = 'RF3E000002';

data_type_epc = 0; % 1 for epc, 0 for rn16max
period_len_cali = 0;

plot_enable = 1;

iris_handle;