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

files = dir([rxdir 'rx*']);
filenum = size(files,1);
plot_device = 2;
symbol_num = 120;
refnum = symbol_num/2-1;
for fileidx=1:filenum
    filename = [rxdir 'rx' int2str(fileidx) '.mat'];
    capture_symbolnum = symbol_num;
    datahandle  %data handle
    capture_refnum = capture_symbolnum/2-1;
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
