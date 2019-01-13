clear all;
close all;

fileidx=10;
rxdir=['../rxdata/nclk/'];


check=true;

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
        if (peak2<0.1)
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

hsr_rxbf            % rxbf employ
% weight, h_bf_rx, bf_snr
