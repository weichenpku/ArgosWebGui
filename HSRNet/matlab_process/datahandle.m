%% input: filename, fconf, fileidx, plot_device
addpath('csi');
addpath('utils');
check = true;
cfo_use = false; % we use cfo_force to compensate
                % cfo_use will introduce large phase shift between frames

%% rxdata lod
disp(filename);
[rx_all_sig, device_num, refdir, device_list, sig_type, nb_rb, ts] = hsr_rxdata(filename,fconf);    
rx_all_sig(1,:)=rx_all_sig(2,:);
rx_ori_sig = rx_all_sig;

load([refdir 'paras.mat']);
pss = csvread([refdir 'pss.csv']);
sig_f = csvread([refdir 'sig_f.csv']);

figure; plot(real(rx_all_sig(1,:)));
if (exist('cfo_force'))
    ch = ones(size(rx_all_sig,1),1) * cfo_sig(cfo_force,srate,size(rx_all_sig,2),ts);
    rxframe = rx_all_sig.*ch;
    rx_all_sig = rxframe;
    hold on; plot(real(rx_all_sig(1,:)));
end
figure; plot(rx_all_sig(1,:)); axis([-1 1 -1 1]);

%% ref & blank idx 
[num_symbols_frame,refnum,refidx,blanknum,blankidx] = ref_blank_idx(sig_type,nb_rb);

%% checklist
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
    % cfo calculation
    hsr_pss_cfo
    
    % cfo_list
    if (sum(checklist(fileidx,:))<=0) return; end
    
    if (cfo_use)
        cfo_list(fileidx,:) = ffo_list(fileidx,:);
        hsr_csi
        old_h_est = h_est;
        cfo_list(fileidx,:) = rfo_list(fileidx,:);
        hsr_csi  
        %  cfo compensation according to csi change
        %  the csi phase change is equal to 2*pi*(rfo-old_csi)*t(0.01)
    else
        cfo_list(fileidx,:) = zeros(1,portnum);
        hsr_csi
    end
    
    % sfo calculate and correlated 
    sfo_cal_and_corr;
    
    hsr_snr             % snr calculate & (ber, cir, pdp, ds)     <= ofdm_judge.m
    % snr_list, ber_list, h_full_est
    % CIR, PDP, DS    
    if (checklist(fileidx,plot_device)==1)
            figure; mesh(angle(h_full_est(:,:,plot_device))); title('csi distribution');
            plotrange=max(max(abs(h_est(:,:,plot_device))));
            if (plotrange==0) plotrange=1; end
            figure; plot(mean(h_full_est(:,:,plot_device),1)); title('mean csi vs time'); axis([-plotrange plotrange -plotrange plotrange]);
            figure; plot(mean(h_full_est(:,:,plot_device),2)); title('mean csi vs frequency'); axis([-plotrange plotrange -plotrange plotrange]);
    end

    hsr_rxbf            % rxbf employ
    % weight, h_bf_rx, bf_snr    
end
