%rxdir=['../rxdata/'];
rxdir=['../rxdata/7/'];
fname = "../conf/conf_LTE.json";
filenum=12;

h_all_est = [];

for fileidx=1:filenum
    %if (fileidx<=2) continue; end
    datahandle  %data handle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end

save([rxdir 'csi.mat'],'h_all_est');
