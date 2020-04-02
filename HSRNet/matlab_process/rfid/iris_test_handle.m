clear; close all;
device1 = 'RF3E000022'; 
device2 = 'RF3E000006';
freq1 = 0.91e9;
freq2 = 0.905e9;
file = 'test/epoch2/rx0.mat';
path = '../../rxdata/';     
load([path file]);

snum = 384000;
if exist('srate','var')==0
    srate = 0.48e6;
end

t = 0:1/srate:(snum-1)/srate;

blf = 40e3;
sigcarrier = exp(-1i*2*pi*blf*t);

refsig0 = csvread('../../refdata/generation/test_data/tone192000_20.csv');
%refsig0 = csvread('../../refdata/generation/test_data/dc192000.csv');
refsig = [refsig0; refsig0];

idata1 = eval([device1 '_I']);
qdata1 = eval([device1 '_Q']);
iqdata1  = idata1+1i*qdata1;

idata2 = eval([device2 '_I']);
qdata2 = eval([device2 '_Q']);
iqdata2 = idata2+1i*qdata2;

%% plot figures
figure;
plot(iqdata1); axis([-1 1 -1 1]);
title('orignal sig in i-q plane');


figure;
plot(iqdata2); axis([-1 1 -1 1]);
title('orignal sig in i-q plane');


figure;
plot(idata1); hold on; plot(qdata1);  plot(abs(iqdata1)); title('orignal i-sig and q-sig');
legend('i','q','amp');

figure;
plot(idata1-mean(idata1)); hold on; plot(qdata1-mean(qdata1));  plot(abs(iqdata1-mean(iqdata1))); title('orignal i-sig and q-sig');
legend('i','q','amp');

figure;
plot(idata2); hold on; plot(qdata2); plot(abs(iqdata2)); title('orignal i-sig and q-sig');
legend('i','q','amp');

figure;
plot(idata2-mean(idata2)); hold on; plot(qdata2-mean(qdata2)); plot(abs(iqdata2-mean(iqdata2))); title('orignal i-sig and q-sig');
legend('i','q','amp');

figure; hold on;
 plot(abs(iqdata1));   plot(abs(iqdata2));
 
figure; hold on;
plot(abs(iqdata1-mean(iqdata1)));   plot(abs(iqdata2-mean(iqdata2)));
 
fs = (-snum/2:snum/2-1)/snum*srate;
fft1 = abs(fftshift(fft(iqdata1)));
fft2 = abs(fftshift(fft(iqdata2)));
figure; hold on;
plot(fs+freq1,2*10*log(fft1)/log(10)); plot(fs+freq2,2*10*log(fft2)/log(10));

