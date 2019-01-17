
%fileidx=2;
rxdir=['../rxdata/'];
fname = "../conf/conf2.json";


check = true;
rfo_use = true;
threshold = 0.01;

hsr_rxdata          % ref_signal & rx_signal read
% rx_all_sig

portnum = size(rx_all_sig,1);
if check
    checklist=ones(1,portnum);
    for idx=1:portnum
        sig=rx_all_sig(idx,:);
        peak1=max([abs(real(sig)) abs(imag(sig))]);
        peak2=max([abs(real(sig-mean(sig))) abs(imag(sig-mean(sig)))]);
        if (peak1>0.9)
            checklist(idx)=-1;
        end
        if (peak2<threshold)
            checklist(idx)=0;
        end
    end
    display(checklist);
end
    

hsr_pss_cfo         % cfo calculation
% cfo_list

hsr_csi             % cfo compensation & csi calculate
% h_tx,h_rx,h_est

hsr_snr             % snr calculate & (ber, cir, pdp, ds)     <= ofdm_judge.m
% snr_list, ber_list, h_full_est
% CIR, PDP, DS


if (rfo_use)
    cfo_list = rfo;
    hsr_csi
    hsr_snr
    figure; mesh(angle(h_full_est(:,:,plot_device))); title('csi distribution');
    figure; plot(mean(h_full_est(:,:,plot_device),1)); title('mean csi vs time');
    figure; plot(mean(h_full_est(:,:,plot_device),2)); title('mean csi vs frequency');
end

hsr_rxbf            % rxbf employ
% weight, h_bf_rx, bf_snr

snr_freq = log(mean(p_sig(:,:,:),2)./mean(p_noi(:,:,:),2))/log(10)*10;
snr_bf_freq_ = log(sum(10.^(snr_freq/10),3))/log(10)*10;
snr_bf_freq = log(mean(p_bf_sig,2)./mean(p_bf_noi,2))/log(10)*10;
figure; hold on;
plot(snr_freq(:,1,1)); plot(snr_freq(:,1,2)); plot(snr_bf_freq); plot(snr_bf_freq_);