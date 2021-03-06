close all;
clear all;

%% paras
fname = "../../conf/conf_single.json";
fileidx= 3;
rx_ant = 1;  
rxdir='../../rxdata/';

%% processing
cd ../csi; 
hsr_rxdata; 
cd ../cfo_verify; % rx_all_sig

tx_t = csvread('../../refdata/generation/test_data/tone.csv');
tx = tx_t;
rx = rx_all_sig(rx_ant+1,1:19200);
tx_f = fftshift(fft(tx));
rx_f = fftshift(fft(rx));



srate = 3.84e6;
fx = linspace(0,srate, 19200); fx=fx-fx(end/2+1);
figure; plot(fx,log(abs(tx_f))/log(10)*10); hold on; plot(fx,log(abs(rx_f))/log(10)*10);
% plot frequency domain of tx & rx signal
% check cfo

[~,idx_tx] = max(abs(tx_f));
tx_freq = freq_cal(tx_f, srate, idx_tx, 1);
[~,idx_rx] = max(abs(rx_f(idx_tx-100:idx_tx+100)));
rx_freq = freq_cal(rx_f, srate, idx_tx-101+idx_rx, 1);
% calculate freq of tx & rx signal

delta_f = tx_freq - rx_freq; % delta frequency
delta_p = 2*pi*delta_f*linspace(0,19200/srate,19200);
delta_s = cos(delta_p)+1i*sin(delta_p);

rx_cfo = (rx-mean(rx)).*delta_s;  %cfo compensation
rx_cfo_f = fftshift(fft(rx_cfo));
figure; plot(fx,log(abs(tx_f))/log(10)*10); hold on; plot(fx,log(abs(rx_cfo_f))/log(10)*10);
% plot frequency domain of tx & cfo_rx signal

figure; plot(rx); hold on; plot((rx_cfo)); title('IQ before/after cfo'); axis([-1 1 -1 1]);
figure; plot(real(rx)); hold on; plot(imag(rx)); title('I & Q before cfo');
figure; plot(real(rx_cfo)); hold on; plot(imag(rx_cfo)); title('I & Q after cfo');
display(['Frequency shift is ',int2str(delta_f),' Hz']);




% t=linspace(0,19200/srate,19200);
% delta_f = 0;
% delta_p = 2*pi*delta_f*linspace(0,19200/srate,19200);
% figure; hold on; plot(rx_cfo2); plot(rx_cfo2.*exp(1i*delta_p)); 
% figure; hold on; plot(t,real(rx_cfo2.*exp(1i*delta_p))); plot(t,imag(rx_cfo2.*exp(1i*delta_p)));

mask=0*ones(1,19200);
idx=idx_tx-100:idx_tx+100;
mask(idx)=1;
rx_cfo1=ifft(fftshift(fftshift(fft(rx_cfo)).*mask));
figure; hold on; plot(rx_cfo); plot(rx_cfo1);
% compare rx_cfo with circle(filtered rx_cfo)