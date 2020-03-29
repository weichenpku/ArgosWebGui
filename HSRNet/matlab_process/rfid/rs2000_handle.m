clear; close all;
device = 'RF3E000006';
file = 'test/epoch0/rx0.mat';
path = '../../rxdata/'; 
load([path file]);

snum = 384000;
srate = 1.92e6;
blf = 40e3;
t = 0:1/srate:(snum-1)/srate;
sigcarrier = exp(-1i*2*pi*blf*t);

% original sig (idata,qdata)
idata = eval([device '_I']);
qdata = eval([device '_Q']);
iqdata = (idata+1i*qdata);

figure; 
plot(idata,qdata);

figure;
plot(idata); hold on; plot(qdata);


% orignal sig + blf sig
figure; hold on;
plot(t*1e3,sign(real(sigcarrier)));
plot(t*1e3,abs(iqdata)); 
xlabel('ms');

% preamble
preamble = [1 1 0 1 0 0 1 0 0 0 1 1];
sig_preamble = reshape(ones(srate/blf/2,1)*preamble,[1,24*12]);

sig_xcorr = xcorr(sig_preamble,abs(iqdata));

figure; 
plot(abs(sig_xcorr)/max(sig_xcorr));
hold on; plot(abs(iqdata));
