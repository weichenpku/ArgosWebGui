clear; close all;
device = 'RF3E000006';
file = 'test/epoch7/rx0.mat';
path = '../../rxdata/'; 
load([path file]);

snum = 384000;
srate = 1.92e6;
t = 0:1/srate:(snum-1)/srate;

blf = 40e3;
sigcarrier = exp(-1i*2*pi*blf*t);

refsig0 = csvread('../../refdata/generation/test_data/tone192000_20.csv');
%refsig0 = csvread('../../refdata/generation/test_data/dc192000.csv');
refsig = [refsig0; refsig0];

idata = eval([device '_I']);
qdata = eval([device '_Q']);
iqdata  = idata+1i*qdata;
iqdata_cali = iqdata./refsig.';

preamble = [1 1 0 1 0 0 1 0 0 0 1 1];
sig_preamble = reshape(ones(srate/blf/2,1)*preamble,[1,24*12]);
sig_xcorr = xcorr(iqdata_cali,sig_preamble);

%% plot figures
figure;
axis([-1 1 -1 1]);
plot(idata,qdata); title('orignal sig in i-q plane');

figure;
plot(idata); hold on; plot(qdata); title('orignal i-sig and q-sig');


figure; 
plot(iqdata_cali); 
axis([-1 1 -1 1]);
title('new sig in i-q plane');

figure;

plot(real(iqdata_cali)); hold on; plot(imag(iqdata_cali));
title('new i-sig and q-sig');

figure; hold on;
plot(sign(real(sigcarrier)));
plot(abs(iqdata_cali));
title('amplitude of iq signal');

figure; hold on;
plot(abs(sig_xcorr));
title('xcorr result');