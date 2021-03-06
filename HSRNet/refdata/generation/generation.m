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
result_save=false;%true;% 
nb_rb = 75; 
%this can be 6,15,25,50,75 or 100 (150)
%bandwidth  1.08, 2.7               

num_carriers = 0; % fft size
num_symbols_frame = 0; % frame_len < 65536
switch nb_rb
    case 6
        num_carriers = 128;
        num_symbols_frame = 120;
    case 15
        num_carriers = 256;
        num_symbols_frame = 120;
    case 25
        num_carriers = 512; % 384 or 512
        num_symbols_frame = 120;
    case 50
        num_carriers = 768; % 768 or 1024
        num_symbols_frame = 120;
    case 75
        num_carriers = 1024; % 1024 or 1536
        num_symbols_frame = 120;
    case 100
        num_carriers = 1536; % 1536 or 2048
        num_symbols_frame = 120;
    case 150
        num_carriers = 2048;
        num_symbols_frame = 60;
        
end

srate=num_carriers*15*1000;
num_zeros = num_carriers -(12*nb_rb+1);
prefix_length = num_carriers/4; %this is extended CP (6 symbols_per_slot)  15/12-1=1/4


pss0_up = interp(primary_synch1_time,num_carriers/128); % 128 => num_carriers
pss0_up_cp = [pss0_up(num_carriers-prefix_length+1:end) pss0_up];

figure; plot(QAM_MOD(4,0:4));
figure; plot(QAM_MOD(16,0:16));
%% frequency and time wave generate
sig_f = zeros(num_symbols_frame,12*nb_rb);
sig_r = zeros(1,(num_carriers+prefix_length)*num_symbols_frame);
sig_br = zeros(1,(num_carriers+prefix_length)*num_symbols_frame);
sig_brrr = zeros(1,(num_carriers+prefix_length)*num_symbols_frame);
for k=1:num_symbols_frame
    QAM_list = QAM_MOD(4,floor(4*rand(1,12*nb_rb)));
    sig_f(k,:) = QAM_list;
    symbol_f = [0 QAM_list(1:12*nb_rb/2) zeros(1,num_zeros) QAM_list(12*nb_rb/2+1:12*nb_rb)];
    symbol_t = ifft(symbol_f);
    assert(size(symbol_t,2)==num_carriers);
    l=1+(k-1)*(num_carriers+prefix_length);
    r=k*(num_carriers+prefix_length);
    sig_r(l:r)=[symbol_t(num_carriers-prefix_length+1:end) symbol_t];
    sig_br(l:r)=[symbol_t(num_carriers-prefix_length+1:end) symbol_t];
    sig_brrr(l:r)=[symbol_t(num_carriers-prefix_length+1:end) symbol_t];
    if (mod(k,2)==1) sig_br(l:r)=0; end
    if (mod(k,4)==1) sig_brrr(l:r)=0; end
end

scale_down = 0.95/max(max(abs(real(sig_r))),max(abs(imag(sig_r))));
sig_r=sig_r*scale_down;
sig_br=sig_br*scale_down;
sig_brrr=sig_brrr*scale_down;

%% add PSS
pss_t=pss0_up;
plot(abs(conv(pss_t,conj(pss_t)))); %time domain feature of pss_t
figure; plot(fft(pss_t).*conj(fft(pss_t)))              % frequency domain feature of pss_t
scale_down = 0.95/max(max(abs(real(pss0_up_cp))),max(abs(imag(pss0_up_cp))));

sig_r(1:num_carriers+prefix_length) = pss0_up_cp*scale_down;
sig_br(1:num_carriers+prefix_length) = pss0_up_cp*scale_down;
sig_brrr(1:num_carriers+prefix_length) = pss0_up_cp*scale_down;

%% add single tone 
cp_symbol_len = num_carriers + prefix_length;
tone_len = 1920; % one subframe (1ms)
tone_f = 1.92e6/256;
tone_t = linspace(0,1/1000,tone_len);
tone_sig(1:tone_len) = 0.75 * exp(1i*2*pi*tone_f*tone_t);
tone_sig(tone_len+1:tone_len*2) = zeros(1,tone_len);

left=num_symbols_frame*cp_symbol_len+1;
right=left-1+tone_len*2;
sig_r(left:right) = tone_sig;
sig_br(left:right) = tone_sig;
sig_brrr(left:right) = tone_sig;

%% save sig
if (result_save)
    if nb_rb<10
        savedir='1.4m/';
    else
        savedir=[int2str(nb_rb/5),'m/'];
    end
    csvwrite([savedir 'sig_f.csv'],sig_f);
    csvwrite([savedir 'sig_r.csv'],sig_r);
    csvwrite([savedir 'sig_br.csv'],sig_br);
    csvwrite([savedir 'sig_brrr.csv'],sig_brrr);
    csvwrite([savedir 'pss.csv'],pss_t);
    save([savedir 'paras.mat'],'nb_rb','num_carriers','srate','cp_symbol_len','num_symbols_frame');
end

display(max(abs(real(sig_r))))
display(max(abs(imag(sig_r))))

figure; plot(abs(conv(sig_br,conj(pss_t))));