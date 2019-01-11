clear all;
close all;

fileidx=1;
hsr_rxdata          % ref_signal & rx_signal read
% rx_all_sig

hsr_pss_cfo         % cfo calculation
% cfo_list

hsr_csi             % cfo compensation & csi calculate
% h_tx,h_rx,h_est

hsr_snr             % snr calculate & (ber, cir, pdp, ds)     <= ofdm_judge.m
% snr_list, ber_list, h_full_est
% CIR, PDP, DS

hsr_rxbf            % rxbf employ
% weight, h_bf_rx, bf_snr
