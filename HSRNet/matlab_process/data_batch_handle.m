%rxdir=['../rxdata/'];
rxdir=['../rxdata/4.25.3/epoch0/'];
fname = "../conf/conf_LTE.json";
filenum=15;

h_all_est = [];

for fileidx=1:filenum
    %if (fileidx==1) continue; end
    datahandle  %data handle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end

save([rxdir 'csi.mat'],'h_all_est');
