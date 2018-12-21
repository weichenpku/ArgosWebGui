close all;
clear all;

nb_rb = 6; %this can be 6,15,25,50,75 or 100
if nb_rb<10
    savedir='1.4m/';
else
    savedir=[int2str(nb_rb/5),'m/'];
end

%% load reference signal
load([savedir 'paras.mat']);
pss_t = csvread([savedir 'pss.csv']);
sig = csvread([savedir 'sig.csv']);
sig_f = csvread([savedir 'sig_f.csv']);

%% load transmit signal
tx_dir = '../../rxdata/';
tx_port = 'RF3E000006-1'; 
load([tx_dir 'I-' tx_port '.mat'])
tx_i=wave;
load([tx_dir 'Q-' tx_port '.mat'])
tx_q=wave;
tx_t=tx_i+1i*tx_q;
figure; plot(real(tx_t));


%% load receive signal
rx_dir = '../../rxdata/';
rx_port = 'RF3E000022-1';
load([rx_dir 'I-' rx_port '.mat'])
rx_i=wave;
load([rx_dir 'Q-' rx_port '.mat'])
rx_q=wave;
rx_t=rx_i+1i*rx_q;
figure; plot(imag(rx_t));

% save(['../../rxdata/tx_test/' tx_port '_test2.mat'],'rx_t');

% rx_t=tx_t;
% sig_len = size(sig,2);
% rx_t = sig*0.5*exp(1i*pi/4);

%% correlation
corr_t = conv(rx_t,conj(pss_t)); % xcorr is similar with conv
figure; plot(abs(corr_t));
[peak, index] = max(abs(corr_t));


prefix_length = num_carriers/4;
frame_start = index - prefix_length - num_carriers;

symbol_len = prefix_length + num_carriers;
num_symbols_frame = 120;
est = zeros(12*nb_rb,num_symbols_frame);
for k = 2:num_symbols_frame
    symbol_start = frame_start + (k-1)*symbol_len;
    symbol_end = frame_start + k*symbol_len - 1; 
    symbol_t = rx_t(symbol_start+prefix_length:symbol_end);
    symbol_f = fft(symbol_t)/sqrt(num_carriers);
    rx_f = [symbol_f(2:1+12*nb_rb/2) symbol_f(end-12*nb_rb/2+1:end)];
    % channel estimation: rx_f vs sig_f(k,:)
    est(:,k) = rx_f./sig_f(k,:);
end

