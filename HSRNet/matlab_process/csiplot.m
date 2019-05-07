clear;
rxdir=['../rxdata/5.5/5.5.1/']; filenum=80;
unwrap_able = 1;

trial_check_list = [];
trial_snr_list = [];
trial_port_list = [];
trial_csi_list = [];
trial_ber_list = [];
trial_cfo_list = [];
trial_bf_snr_list = [];
trial_max_snr_list = [];

repeat_num = 15;
csi_idx = [];
for i=1:repeat_num
    csi_idx(1+29*(i-1):29*i) = (1+59*(i-1):29+59*(i-1));
end

for i=1:filenum
    csifile = [rxdir 'epoch' int2str(i-1) '/csi.mat'];
    disp(csifile);
    load(csifile);
    %'h_all_est','checklist','cfo_list','ber_list','snr_list','bf_snr_list','max_snr_list'
    
    
    trial_snr_list(i,:) = max(snr_list);
    trial_ber_list(i,:) = mean(ber_list);
    trial_cfo_list(i,:) = mean(cfo_list);
    trial_bf_snr_list(i) =  max(bf_snr_list);
    trial_max_snr_list(i) = max(max_snr_list);
    
    % port check 
    trial_check_list(i,:) = sum(checklist(find(checklist(:,1)>0),:));
    trial_port_list(i,:) = sum(checklist)+5>max(sum(checklist));
    port_able = find(trial_port_list(i,:)>0);
    
    % h_all_est align
    if (min(checklist(repeat_num,:))<1)
        h_all_est(:,(repeat_num-1)*59+1:repeat_num*59,:) = 0*h_all_est(:,1:59,:);
    end
    
    % csi: h_all_est
    csi_list = h_all_est(:,csi_idx,port_able);
    csi_num = size(csi_list,2);
    trial_csi_list(:,1+15*(i-1):15*i,port_able) = csi_list(:,1:29:end,:);
%   trial_csi_list(:,1+csi_num*(filenum-1):csi_num*filenum,port_able) = csi_list; 
%     csi_delta_list =  csi_list(:,:,1)./csi_list(:,:,2);
%     unwrapped_angle = unwrap(unwrap(angle(csi_delta_list),[],2),[],1);
%     mesh(unwrapped_angle);
end

plot(trial_bf_snr_list); hold on; plot(trial_max_snr_list); plot(trial_snr_list); legend('bf_snr','max_snr');