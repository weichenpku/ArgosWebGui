fileidx % read fileidx
nb_rb = 6; %this can be 6,15,25,50,75 or 100
rxdir = '../../rxdata/hsr_1/';
rxdevice = ['RF3E000022'];

%% load reference signal
% nb_rb
if nb_rb<10
    savedir='../generation/1.4m/';
else
    savedir=['../generation/',int2str(nb_rb/5),'m/'];
end

load([savedir 'paras.mat']);
pss_t = csvread([savedir 'pss.csv']);
sig = csvread([savedir 'sig.csv']);
sig_f = csvread([savedir 'sig_f.csv']);


%% load recv signal
% rxdir
rxfile = dir([rxdir 'rx*']);
rxnum = size(rxfile,1);
for file = 1:rxnum
    filename = rxfile(rxnum).name;
end
filename = rxfile(fileidx).name;

%% load transmit signal
% load([rxdir,filename])
% tx_dir = '../../rxdata/';
% tx_port = 'RF3E000006-1'; 
% load([tx_dir 'I-' tx_port '.mat'])
% tx_i=wave;
% load([tx_dir 'Q-' tx_port '.mat'])
% tx_q=wave;
% tx_t=tx_i+1i*tx_q;
% figure; plot(real(tx_t));


%% load receive signal
load([rxdir filename]);
device_num = size(rxdevice,1);
rx_all_sig=[];
for idx = 1:device_num
    rx_all_sig(2*idx-1,:) = eval([rxdevice(idx,:) '_0_I'])+1i*eval([rxdevice(idx,:) '_0_Q']);
    rx_all_sig(2*idx,:) = eval([rxdevice(idx,:) '_1_I'])+1i*eval([rxdevice(idx,:) '_1_Q']);
end



