function [rx_all_sig,device_num,refdir,device_list,sig_type,nb_rb,ts] = hsr_rxdata(filename,fconf)
% input:  filename,fconf
% output:  rx_all_sig,device_num,refdir,device_list,sig_type,nb_rb,ts

%% read configure
fid = fopen(fconf); 
raw = fread(fid,inf); 
str = char(raw'); 
fclose(fid); 
val = jsondecode(str);

nb_rb = str2num(val.nrb);   %this can be 6,15,25,50,75 or 100
rxdevicenum = str2num(val.receivernum);
rxdevice = [];
rxdevice(1,:)=val.receiver_master.serial;
for idx=1:rxdevicenum-1
    rxdevice(idx+1,:)=val.receiver(idx).serial;
end
device_list = char(rxdevice);

sig_type = '';
if (strcmp(val.sig_type,'sig_r.csv')==1) sig_type = 'r'; end
if (strcmp(val.sig_type,'sig_br.csv')==1) sig_type = 'br'; end
if (strcmp(val.sig_type,'sig_brrr.csv')==1) sig_type = 'brrr'; end



%% load reference signal
path='../refdata/generation/';
% nb_rb
if nb_rb<10
    refdir=[path '1.4m/'];
else
    refdir=[path int2str(nb_rb/5) 'm/'];
end


%% load receive signal
ts = 0; % for default
load(filename);
device_num = size(rxdevice,1);
rx_all_sig=[];
for idx = 1:device_num
    devicestr=char(rxdevice(idx,:));
    rx_all_sig(2*idx-1,:) = eval([devicestr '_0_I'])+1i*eval([devicestr '_0_Q']);
    rx_all_sig(2*idx,:) = eval([devicestr '_1_I'])+1i*eval([devicestr '_1_Q']);
end

end



