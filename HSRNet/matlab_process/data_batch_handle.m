h_all_est = [];
checklist = [];
cfo_list = [];
ber_list = [];
snr_list = [];
bf_snr_list = [];
max_snr_list = [];

files = dir([rxdir 'rx*']);
filenum = size(files,1);
for fileidx=1:filenum
    filename = [rxdir 'rx' int2str(fileidx) '.mat'];
    datahandle  %data handle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end

% checklist = [];
% cfo_list = [];
% ber_list = [];
% snr_list = [];
% bf_snr_list = [];
% max_snr_list = [];
%save([rxdir 'csi.mat'],'h_all_est');
