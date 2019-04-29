%input: filename, fconf, fileidx, plot_device
addpath('csi');
check = true;
rfo_use = true;
threshold = 0.01;

disp(filename);
[rx_all_sig, device_num, refdir] = hsr_rxdata(filename,fconf);          % ref_signal & rx_signal read
load([refdir 'paras.mat']);
pss = csvread([refdir 'pss.csv']);
sig_f = csvread([refdir 'sig_f.csv']);

portnum = size(rx_all_sig,1);
if check % check the signal power
    for idx=1:portnum
        sig=rx_all_sig(idx,:);
        peak1=max([abs(real(sig)) abs(imag(sig))]);
        peak2=max([abs(real(sig-mean(sig))) abs(imag(sig-mean(sig)))]);
        checklist(fileidx,idx) = 1;
        if (peak1>0.9)
            checklist(fileidx,idx) = -1; % gain is too large
        end
        if (peak2<threshold)
            checklist(fileidx,idx) = 0; % rx signal power is too small 
        end
    end
end
    

hsr_pss_cfo         % cfo calculation
% cfo_list

hsr_csi             % cfo compensation & csi calculate
% h_tx,h_rx,h_est

hsr_snr             % snr calculate & (ber, cir, pdp, ds)     <= ofdm_judge.m
% snr_list, ber_list, h_full_est
% CIR, PDP, DS


if (rfo_use)
    cfo_list(fileidx,:) = rfo_list(fileidx,:);
    hsr_csi
    hsr_snr
    %display(ber_list);
    %display(snr_list);
    
    figure; mesh(angle(h_full_est(:,:,plot_device))); title('csi distribution');
    range=max(max(abs(h_est(:,:,plot_device))));
    figure; plot(mean(h_full_est(:,:,plot_device),1)); title('mean csi vs time'); axis([-range range -range range]);
    figure; plot(mean(h_full_est(:,:,plot_device),2)); title('mean csi vs frequency'); axis([-range range -range range]);
end

hsr_rxbf            % rxbf employ
% weight, h_bf_rx, bf_snr