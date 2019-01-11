close all;
clear all;
addpath('../openair1/PHY/LTE_REFSIG');

primary_synch;   %PSS 
% primary_synch0,1,2: 3 kinds zadeoff-chu sequence (62+5*2=72)
% primary_synch0_tab
% primary_synch0_mod: scale primary_synch0 from float[-1,1] to int[-32767,32767]
% primary_synch0_mod2: fftshift(pridmary_synch0)  (72+56=128)
% primary_synch0_time: ifft(primary_synch0_mod2)

%% # of resource block
nb_rb = 100; %this can be 6,15,25,50,75 or 100

num_carriers = 2048/100*nb_rb; % fft size
if nb_rb==15
    num_carriers = 256;
end
if nb_rb==6
    num_carriers = 128;
end

srate=num_carriers*15*1000;
num_zeros = num_carriers-(12*nb_rb+1);
prefix_length = num_carriers/4; %this is extended CP (6 symbols_per_slot)  15/12-1=1/4
num_symbols_frame = 120; % 6*2*10

pss0_up = interp(primary_synch1_time,num_carriers/128); % 128 => num_carriers
pss0_up_cp = [pss0_up(num_carriers-prefix_length+1:end) pss0_up];

figure; plot(QAM_MOD(4,0:4));
figure; plot(QAM_MOD(16,0:16));
%% frequency and time wave generate
sig_f = zeros(num_symbols_frame,12*nb_rb);
sig = zeros(1,(num_carriers+prefix_length)*num_symbols_frame);
for k=1:2:num_symbols_frame
    QAM_list = QAM_MOD(4,floor(4*rand(1,12*nb_rb)));
    sig_f(k,:) = QAM_list;
    symbol_f = [0 QAM_list(1:12*nb_rb/2) zeros(1,num_zeros) QAM_list(12*nb_rb/2+1:12*nb_rb)];
    symbol_t = ifft(symbol_f);
    assert(size(symbol_t,2)==num_carriers);
    sig(1+(k-1)*(num_carriers+prefix_length):k*(num_carriers+prefix_length))=[symbol_t(num_carriers-prefix_length+1:end) symbol_t];
end
sig=sig*sqrt(num_carriers);
scale_down = 0.95/max(max(abs(real(sig))),max(abs(imag(sig))));
sig=sig*scale_down;

%% add PSS
pss_t=pss0_up;
plot(abs(conv(pss_t,conj(pss_t)))); %time domain feature of pss_t
figure; plot(fft(pss_t).*conj(fft(pss_t)))              % frequency domain feature of pss_t
scale_down = 0.95/max(max(abs(real(pss0_up_cp))),max(abs(imag(pss0_up_cp))));
sig(1:num_carriers+prefix_length) = pss0_up_cp*scale_down;

if nb_rb<10
    savedir='1.4m/';
else
    savedir=[int2str(nb_rb/5),'m/'];
end

csvwrite([savedir 'sig1_f.csv'],sig_f);
csvwrite([savedir 'sig1.csv'],sig);
%csvwrite([savedir 'pss.csv'],pss_t);
%save([savedir 'paras.mat'],'nb_rb','num_carriers','srate');

display(max(abs(real(sig))))
display(max(abs(imag(sig))))