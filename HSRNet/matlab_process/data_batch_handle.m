%rxdir=['../rxdata/'];
rxdir=['../rxdata/4.25/4.25.3/epoch0/'];
fconf = "../conf/conf_LTE.json";

h_all_est = [];
files = dir([rxdir 'rx*']);
filenum = size(files,1);

for fileidx=1:filenum
    filename = [rxdir 'rx' int2str(fileidx) '.mat'];
    datahandle(filename,fconf)  %data handle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end

%save([rxdir 'csi.mat'],'h_all_est');
