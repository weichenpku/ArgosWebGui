sig_detect_threshold = 0.01;
sig_sat_threshold = 0.9;

h_all_est = [];
checklist = []; % -2, -1, 0 , 1 
cfo_list = [];
ber_list = [];
snr_list = [];
bf_snr_list = [];
max_snr_list = [];
rfo_list = [];
offset_all_list = [];
rss_list = [];

num_symbols_frame = 0;
refnum = 0;
refidx = [];
blanknum = 0;
blankidx = [];
capture_symbolnum = 0;
capture_refnum = 0;
capture_refidx = [];
capture_blanknum = 0;
capture_blankidx = [];

files = dir([rxdir 'rx*']);
filenum = size(files,1);
plot_device = 2;
for fileidx=1:filenum
    %filename = [rxdir 'rx' int2str(fileidx) '.mat'];
    filename = [rxdir 'rx0.mat'];
    datahandle  %data handle
    close all;
    if (sum(checklist(fileidx,:))>0)
        h_all_est(:,1+refnum*(fileidx-1):capture_refnum+refnum*(fileidx-1),:)=h_full_est;
    end
end

figure; mesh(angle(h_all_est(:,:,1)./h_all_est(:,:,2))); title('all time csi distribution');
if (exist('outdir')>0) saveas(gcf,[outdir 'log.jpg']); end

display(checklist);
display(cfo_list);
display(ber_list);
display(snr_list);
display(bf_snr_list);
display(max_snr_list);

rfo_list = rfo_list - cfo_list;
display(rfo_list);

save([rxdir 'csi.mat'],'h_all_est','checklist','cfo_list','ber_list','snr_list',  ...
'bf_snr_list','max_snr_list','offset_all_list','rss_list','device_list');
