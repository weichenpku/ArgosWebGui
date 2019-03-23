fid = fopen(fname); 
raw = fread(fid,inf); 
str = char(raw'); 
fclose(fid); 
val = jsondecode(str);

nb_rb = str2num(val.nrb); %this can be 6,15,25,50,75 or 100
rxdevicenum = str2num(val.receivernum);
rxdevice = [];
rxdevice(1,:)=val.receiver_master.serial;
for idx=1:rxdevicenum-1
    rxdevice(idx+1,:)=val.receiver(idx).serial;
end



%% load reference signal
path='../../refdata/generation/';
% nb_rb
if nb_rb<10
    savedir=[path '1.4m/'];
else
    savedir=[path int2str(nb_rb/5) 'm/'];
end

load([savedir 'paras.mat']);
pss = csvread([savedir 'pss.csv']);
sig_f = csvread([savedir 'sig_f.csv']);


%% load recv signal
% rxdir
rxfile = dir([rxdir 'rx*']);
rxnum = size(rxfile,1);
file_list=[""];
for file = 1:rxnum
    tmpname = rxfile(file).name;
    file_list(file+1)=tmpname;
end
filename = ['rx' int2str(fileidx) '.mat'];
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
    devicestr=char(rxdevice(idx,:));
    rx_all_sig(2*idx-1,:) = eval([devicestr '_0_I'])+1i*eval([devicestr '_0_Q']);
    rx_all_sig(2*idx,:) = eval([devicestr '_1_I'])+1i*eval([devicestr '_1_Q']);
end



