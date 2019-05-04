%input: filename, fconf, fileidx, plot_device
addpath('csi');
check = true;
rfo_use = true;


disp(filename);
[rx_all_sig, device_num, refdir,device_list, sig_type] = hsr_rxdata(filename,fconf);          % ref_signal & rx_signal read
load([refdir 'paras.mat']);
pss = csvread([refdir 'pss.csv']);
sig_f = csvread([refdir 'sig_f.csv']);

portnum = size(rx_all_sig,1);
if check % check the signal power
    window_len = cp_symbol_len*2;
    window_num = round(size(rx_all_sig,2)/window_len);
    mean_value = zeros(portnum,window_num);
    maxsig_value = zeros(portnum,window_num);
    for i=1:portnum
        for j=1:window_num
            if (j<window_num)
                sig = rx_all_sig(i,1+(j-1)*window_len:j*window_len);
            else
                sig = rx_all_sig(i,1+(j-1)*window_len:end);
            end
            mean_value(i,j) = mean(sig);
            maxsig_value(i,j) = max(abs(sig-mean(sig)));
        end
        checklist(fileidx,i) = 1;  % signal power is normal
        sig = rx_all_sig(i,:);
        maxiq_value = max([abs(real(sig)) abs(imag(sig))]);
        if (maxiq_value>sig_sat_threshold) checklist(fileidx,i)=-1; end  % signal is saturated
        ratio = sum(maxsig_value(i,:)>sig_detect_threshold)/sum(maxsig_value(i,:)>0);
        if ratio<0.7 checklist(fileidx,i)=0; end % signal power is too small 
    end
end
    
if (sum(checklist(fileidx,:))>0)
    hsr_pss_cfo         % cfo calculation
    % cfo_list
    if (sum(checklist(fileidx,:))<=0) return; end
    
    hsr_csi             % csi calculate
    % h_tx,h_rx,h_est
    if (rfo_use)
        cfo_list(fileidx,:) = rfo_list(fileidx,:);
        hsr_csi  %  cfo compensation according to csi change
    end
    % cfo_list suppose to be similar; rfo_list suppose to be < 1Hz
    
    hsr_snr             % snr calculate & (ber, cir, pdp, ds)     <= ofdm_judge.m
    % snr_list, ber_list, h_full_est
    % CIR, PDP, DS    
    if (checklist(fileidx,plot_device)==1)
            figure; mesh(angle(h_full_est(:,:,plot_device))); title('csi distribution');
            range=max(max(abs(h_est(:,:,plot_device))));
            figure; plot(mean(h_full_est(:,:,plot_device),1)); title('mean csi vs time'); axis([-range range -range range]);
            figure; plot(mean(h_full_est(:,:,plot_device),2)); title('mean csi vs frequency'); axis([-range range -range range]);
    end

    hsr_rxbf            % rxbf employ
    % weight, h_bf_rx, bf_snr    
end