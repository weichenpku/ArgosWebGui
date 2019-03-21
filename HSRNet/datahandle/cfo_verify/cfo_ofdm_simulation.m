close all;
clear all;

load('../../refdata/generation/1.4m/paras.mat');
pss = csvread('../../refdata/generation/1.4m/pss.csv');

%% transmit signal: pss_t
cp_len = 128/4;
pss_t = [pss(end-cp_len+1:end) pss];

% self correlation
self_corr = conv(pss_t,conj(pss));
figure; plot(abs(self_corr));


%% receive signal: rx_pss
df0 = 8000;
phase0 = pi/3;
phase = 2*pi*df0*(1:160)/srate + phase0;   
ch0 = cos(phase)+1i*sin(phase);   % channel simulation

rx_pss_t = ch0.*pss_t;

%% first: IFO
ifo_idx = [-1,0,1];
rx_pss_ifo = [];
corr_list = [];
maxcorr=0; maxcorr_offset=0; maxcorr_idx=-1;
for idx = 1:3
    df = 15e3*ifo_idx(idx);
    phase = 2*pi*df*(1:160)/srate;
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

offset = maxcorr_offset
ifo = ifo_idx(maxcorr_idx)*15000*-1;
rx_pss1 = rx_pss_ifo(maxcorr_idx,:);
display(['IFO is ',int2str(ifo),'Hz']);

%% second: FFO  (CP based)
rx_pss_cp1 = rx_pss1(offset-160:offset-128-1);
rx_pss_cp2 = rx_pss1(offset-32:offset-1);

cp_corr=conj(rx_pss_cp1).*rx_pss_cp2;
ffo = mean(angle(cp_corr))/2/pi*15000;
display(['FFO is ',int2str(ffo),'Hz']);

% ffo compensation
df = -ffo;
phase = 2*pi*df*(1:160)/srate;
ch = cos(phase)+1i*sin(phase);
rx_pss2 = ch.*rx_pss1;


%% third: RFO (PSS based)
y1=sum(rx_pss2(offset-128:offset-65).*conj(pss(1:end/2)));
y2=sum(rx_pss2(offset-64:offset-1).*conj(pss(end/2+1:end)));
rfo=angle(y2/y1)/pi*15000;
display(['RFO is ',int2str(rfo),'Hz']);

% rfo compensation
df = -rfo;
phase = 2*pi*df*(1:160)/srate;
ch = cos(phase)+1i*sin(phase);
rx_pss3 = ch.*rx_pss2;

%% result
% suppose ifo+ffo+rfo =  df0