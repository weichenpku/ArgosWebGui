data_dir='1.4m/';
matfile=[data_dir 'paras.mat'];
load(matfile);
sig = csvread([data_dir 'sig.csv']);
slot_len = size(sig,2)/120;

for i=(1:120)
    if mod(i,120)==1
        sig_pss(1+(i-1)*slot_len:i*slot_len) = sig(1:slot_len); 
    else
        sig_pss(1+(i-1)*slot_len:i*slot_len) = sig(1:slot_len)*0; 
    end
end
sig_tx=sig_pss(1:1920);
csvwrite([data_dir 'sig_pss.csv'],sig_tx);



ns=srate/100
phase = 2*pi*15000*2*(1:ns)/srate;
tone = (cos(phase)+1i*sin(phase));
% tone(end-1920*5+1:end)=0*tone(end-1920*5+1:end);
csvwrite([data_dir '../test_data/tone.csv'],tone);


tone_tx = tone(1:2400);
csvwrite([data_dir '../test_data/tone2400.csv'],tone_tx*0.8);
