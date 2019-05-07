clear;
%rxdir=['../rxdata/5.5/5.5.0/']; filenum=80; ref_port = 8;
rxdir=['../rxdata/5.5/5.5.1/']; filenum=80; ref_port = 8;
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

for i=76:filenum
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

    %display(snr_list)
    port1 = 5; port2 = 6;
    plot_csi = csi_list(:,:,port1)./csi_list(:,:,port2).*abs(csi_list(:,:,port2));
    figure; mesh(angle(plot_csi));
    % CIR and doppler spread
    CIR=ifft(plot_csi,[],1); % CIR time, symbol time
    figure; mesh(abs(fftshift(CIR))); title('CIR');
    PDP = mean(CIR.^2,2); % CIR time
    figure; plot(fftshift((abs(PDP(:,:))))); title('PDP');
    DS = fft(CIR,[],2); % CIR time, spead freq
    figure; mesh(abs(fftshift(fftshift(DS(:,:),1),2))); title('Doppler Spread');
    
    close all;
end


% rxbf_snr
plot(trial_bf_snr_list); hold on; plot(trial_max_snr_list); plot(trial_snr_list); legend('bf_snr','max_snr');

% ber vs snr
figure; subplot(2,1,1); semilogy(trial_ber_list); title('ber');
    subplot(2,1,2); plot(trial_snr_list); title('snr');

% cfo vs snr
figure; subplot(2,1,1); plot(trial_cfo_list); title('cfo');
    subplot(2,1,2); plot(trial_snr_list); title('snr');

% csi plot
trial_delta_csi_list = [];
for i=1:size(trial_csi_list,3)
    if (i==ref_port) continue; end
    trial_delta_csi_list(:,:,i) = trial_csi_list(:,:,i)./trial_csi_list(:,:,ref_port);
end

save([rxdir 'result.mat']);