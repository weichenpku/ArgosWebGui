close all;
clear all;

fileidx=10;
rxdir='../rxdata/';
txdevice = 'RF3E000006';
rxdevice = 'RF3E000021';
cd ..; hsr_rxdata; cd cfo_verify; % rx_all_sig

symbol_len = 256;
cp_len = symbol_len/4;
pss_t = [pss(end-cp_len+1:end) pss];

rx_t = rx_all_sig(1,:);

tmp_corr = conv(rx_t,conj(pss));
[tmp_peak,tmp_idx]=max(abs(tmp_corr(1:round(end/2))));

rx_pss_t = rx_t(tmp_idx-symbol_len-cp_len:tmp_idx-1);
if tmp_idx-symbol_len-cp_len+38400-1<60000
    rx_tone_t = rx_t(tmp_idx-symbol_len-cp_len+19200:tmp_idx-symbol_len-cp_len+38400-1);
else
    rx_tone_t = rx_t(tmp_idx-symbol_len-cp_len-19200:tmp_idx-symbol_len-cp_len-1);
end

%% rx_tone_t =>
%% Ground truth from single tone
tx_t = csvread('../../refdata/generation/test_data/sig_tone_3m.csv');
tx_tone_t = tx_t(end/2+1:end);
tx_f = fftshift(fft(tx_tone_t));
rx_f = fftshift(fft(rx_tone_t));
srate = 3.84e6;
fx = linspace(0,srate, 19200); fx=fx-fx(end/2+1);
figure; plot(fx,log(abs(tx_f))); hold on; plot(fx,log(abs(rx_f)));

[~, idx] = max(abs(tx_f));
tx_freq = freq_cal(tx_f, srate, idx, 1);
[~, idx] = max(abs(rx_f));
rx_freq = freq_cal(rx_f, srate, idx, 1);

delta_f = tx_freq - rx_freq;
delta_p = 2*pi*delta_f*linspace(0,19200/srate,19200);
delta_s = cos(delta_p)+1i*sin(delta_p);

rx_cfo = rx_tone_t.*delta_s;
rx_cfo_f = fftshift(fft(rx_cfo));
figure; plot(fx,log(abs(tx_f))); hold on; plot(fx,log(abs(rx_cfo_f)));
display(['Ground frequency shift is ', int2str(rx_freq-tx_freq),'Hz']);
figure; plot(rx_tone_t); hold on; plot((rx_cfo));


%% rx_pss_t
%% first: IFO
ifo_idx = [-1,0,1];
rx_pss_ifo = [];
corr_list = [];
maxcorr=0; maxcorr_offset=0; maxcorr_idx=-1;
for idx = 1:3
    df = 15e3*ifo_idx(idx);
    phase = 2*pi*df*(1:320)/srate;
    ch = cos(phase)+1i*sin(phase);
    rx_pss_ifo(idx,:)=ch.*rx_pss_t;
    corr_list(idx,:)=conv(rx_pss_ifo(idx,:),conj(pss));
    [tmp_peak, tmp_idx]=max(abs(corr_list(idx,:)));
    if tmp_peak > maxcorr
        maxcorr = tmp_peak;
        maxcorr_offset = tmp_idx;
        maxcorr_idx = idx;
    end
end

offset = maxcorr_offset; assert(offset==321);
ifo = ifo_idx(maxcorr_idx)*15000*-1;
rx_pss1 = rx_pss_ifo(maxcorr_idx,:);
display(['IFO is ',int2str(ifo),'Hz']);

%% second: FFO  (CP based)
rx_pss_cp1 = rx_pss1(offset-320:offset-256-1);
rx_pss_cp2 = rx_pss1(offset-64:offset-1);

cp_corr=conj(rx_pss_cp1).*rx_pss_cp2;
ffo = mean(angle(cp_corr))/2/pi*15000;
display(['FFO is ',int2str(ffo),'Hz']);

% ffo compensation
df = -ffo;
phase = 2*pi*df*(1:320)/srate;
ch = cos(phase)+1i*sin(phase);
rx_pss2 = ch.*rx_pss1;


%% third: FFO (PSS based)
y1=sum(rx_pss2(offset-256:offset-128-1).*conj(pss(1:end/2)));
y2=sum(rx_pss2(offset-128:offset-1).*conj(pss(end/2+1:end)));
ffo2=angle(y2/y1)/pi*15000;
display(['FFO2 is ',int2str(ffo2),'Hz']);

% ffo compensation
df = -ffo2;
phase = 2*pi*df*(1:320)/srate;
ch = cos(phase)+1i*sin(phase);
rx_pss3 = ch.*rx_pss2;

cfo=ifo+ffo;
display(['CFO is ',int2str(cfo),'Hz']);