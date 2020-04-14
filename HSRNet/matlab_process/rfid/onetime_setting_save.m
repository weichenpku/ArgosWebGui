clear; close all;

tx_pos = [-0.5,0];
rx_pos = [3e8/915e6/2,-0.8];
tag_pos = [0,2.27];
freq = 850e6;

save('../../rxdata/test/setting.mat');

txdis = abs((tx_pos - tag_pos)*[1;1i]);
rxdis = abs((rx_pos - tag_pos)*[1;1i]);
trx_phase = (txdis+rxdis)*freq/3e8*360;

