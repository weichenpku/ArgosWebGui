rxdir=['../rxdata/5.4/5.4.0/'];
unwrap_able = 1;

trial_check_list = [];
trial_snr_list = [];
trial_port_list = [];
for i=1:1
    csifile = [rxdir 'epoch' int2str(i-1) '/csi.mat'];
    disp(csifile);
    load(csifile);
    %'h_all_est','checklist','cfo_list','ber_list','snr_list','bf_snr_list','max_snr_list'
    
    % port check 
    trial_check_list(i,:) = sum(checklist);
    trial_snr_list(i,:) = max(snr_list);
    trial_port_list(i,:) = sum(checklist)+5>max(sum(checklist));
    port_able = find(trial_port_list(i,:)>0);
    
    % csi: h_all_est
    csi_list = h_all_est(:,:,port_able);
    csi_delta_list =  csi_list(:,:,1)./csi_list(:,:,2);
    unwrapped_angle = unwrap(unwrap(angle(csi_delta_list),1),2);
    mesh(unwrapped_angle);
    a=1;
end