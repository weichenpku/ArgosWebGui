sig_detect_threshold = 0.05;
sig_sat_threshold = 0.9;

h_all_est = [];
checklist = [];
cfo_list = [];
ber_list = [];
snr_list = [];
bf_snr_list = [];
max_snr_list = [];
rfo_list = [];

files = dir([rxdir 'rx*']);
filenum = size(files,1);
plot_device = 1;
for fileidx=1:filenum
    filename = [rxdir 'rx' int2str(fileidx) '.mat'];
    datahandle  %data handle
    close all;
    if (sum(checklist(fileidx,:))>0)
        h_all_est(:,1+59*(fileidx-1):59*fileidx,:)=h_full_est(:,2:end,:);
    end
end

figure; mesh(angle(h_all_est(:,:,1)./h_all_est(:,:,2))); title('all time csi distribution');
if (exist('outfigure')>0) saveas(gcf,outfigure); end

display(checklist);
display(cfo_list);
display(ber_list);
display(snr_list);
display(bf_snr_list);
display(max_snr_list);

rfo_list = rfo_list - cfo_list;
display(rfo_list);
%save([rxdir 'csi.mat'],'h_all_est');
