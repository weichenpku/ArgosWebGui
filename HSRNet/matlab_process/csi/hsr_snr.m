%get rx_all_frame, h_est
[carriernum, symbolnum, portnum] = size(h_est);


% snr calculate => get snr_list
h_sig=zeros(carriernum,portnum);
p_sig=zeros(carriernum,portnum);
h_noi=zeros(carriernum,symbolnum,portnum);
p_noi=zeros(carriernum,portnum);
snr_cur=zeros(carriernum,portnum);
if (strcmp(sig_type,'r')) % noise estimation algorithm is not right for 'sig_r'
    for cur_device=1:portnum
            if checklist(fileidx,cur_device)~=1 continue; end
            h_sig(:,cur_device) = mean(h_est(:,2:end,cur_device),2);
            p_sig(:,cur_device) = abs(h_sig(:,cur_device)).^2;
            for sn = 2:symbolnum
                h_noi(:,sn,cur_device) = h_est(:,sn,cur_device)-h_sig(:,cur_device);              
            end
            p_noi(:,cur_device) = mean(abs(h_noi(:,2:end,cur_device)).^2,2);
            snr_list(fileidx,cur_device)=log(mean(p_sig(:,cur_device),1)/mean(p_noi(:,cur_device),1))/log(10)*10;
    end
end
if (strcmp(sig_type,'r')==0)
    for cur_device = 1:portnum
        if checklist(fileidx,cur_device)~=1 continue; end
        h_sig_vec = mean(h_est(:,capture_refidx,cur_device),2);
        h_sig(:,cur_device) = h_sig_vec;
        p_sig(:,cur_device) = abs(h_sig_vec).^2;
        p_noi(:,cur_device) = mean(abs(h_est(:,capture_blankidx,cur_device)).^2,2);
        snr_cur(:,cur_device) = p_sig(:,cur_device)./p_noi(:,cur_device);
        snr_list(fileidx,cur_device) = log(mean(snr_cur(:,cur_device)))/log(10)*10;
    end
end


% ber calculate => get ber_list
for cur_device=1:portnum
    if checklist(fileidx,cur_device)~=1 continue; end
    total_symbol=0;
    error_symbol=0;
    for idx=1:capture_refnum
        tidx = capture_refidx(idx);
        h_vec = h_sig(:,cur_device);
        rx_vec = h_rx(:,tidx,cur_device)./h_vec;
        tx_vec = h_tx(:,tidx,cur_device);
        total_symbol=total_symbol+carriernum;
        error_symbol=error_symbol+ofdm_judge(rx_vec,tx_vec,'QAM',carriernum);
    end
    ber_list(fileidx,cur_device)=error_symbol/total_symbol;
end

h_full_est = h_est(:,capture_refidx,:);
% CIR and doppler spread
CIR=ifft(h_full_est,[],1); % CIR time, symbol time
figure; mesh(abs(fftshift(CIR(:,:,plot_device),1))); title('CIR');

PDP = mean(CIR.^2,2); % CIR time
figure; plot(fftshift((abs(PDP(:,:))))); title('PDP');

DS = fft(CIR,[],2); % CIR time, spead freq
figure; mesh(abs(fftshift(fftshift(DS(:,:,plot_device),1),2))); title('Doppler Spread')



