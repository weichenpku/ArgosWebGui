clear; close all;
path = '../../rxdata/test/';
device = 'RF3E000002'; 

load([path 'I-' device '-0.mat']);
idata = wave;
load([path 'Q-' device '-0.mat']);
qdata = wave;
rxdata = idata+1i*qdata;
load([path 'tx.mat']);
txdata = permute(wave,[2,3,1]);

figure; hold on;
plot(txdata);
plot(rxdata);

figure; hold on;
plot(abs(rxdata));
plot(real(rxdata));
plot(imag(rxdata));