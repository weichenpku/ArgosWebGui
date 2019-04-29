%get rx_all_frame, h_est
[carriernum, symbolnum, portnum] = size(h_est);


% snr calculate => get snr_list
h_sig=zeros(carriernum,portnum);
p_sig=zeros(carriernum,portnum);
h_noi=zeros(carriernum,symbolnum,portnum);
p_noi=zeros(carriernum,portnum);
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


% ber calculate => get ber_list
for cur_device=1:portnum
    if checklist(fileidx,cur_device)~=1 continue; end
    total_symbol=0;
    error_symbol=0;
    for sn=2:symbolnum
        h_vec = h_sig(:,cur_device);
        rx_vec = h_rx(:,idx,cur_device)./h_vec;
        tx_vec = h_tx(:,idx,cur_device);
        total_symbol=total_symbol+carriernum;
        error_symbol=error_symbol+ofdm_judge(rx_vec,tx_vec,'QAM',carriernum);
    end
    ber_list(fileidx,cur_device)=error_symbol/total_symbol;
end



% csi insert and unwrap
h_full_est = [];
angle_full_est = [];
for cur_device=1:portnum
    if checklist(fileidx,cur_device)~=1 
        continue; 
    end
    % h_est => h_full_est
    h_full_est = fftshift(h_est,1);
    h_full_est(:,1) = (h_full_est(:,2).^2)./h_full_est(:,3);
    angle_full_est(:,3:symbolnum,cur_device) = angle(h_full_est(:,3:end,cur_device))-angle(h_full_est(:,2:end-1,cur_device));
    angle_unwrap = angle_full_est;
    idxlist=find(angle_unwrap>pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap>pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap<-pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    idxlist=find(angle_unwrap<-pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    
    rfo_list(fileidx,cur_device) = cfo_list(fileidx,cur_device) + mean(mean(angle_unwrap(:,3:end,cur_device)))*srate/(2*pi*cp_symbol_len);
end

% CIR and doppler spread
CIR=ifft(h_full_est,[],1); % CIR time, symbol time
figure; mesh(abs(fftshift(CIR(:,:,plot_device),1))); title('CIR');

PDP = mean(CIR.^2,2); % CIR time
figure; plot(fftshift((abs(PDP(:,:))))); title('PDP');

DS = fft(CIR,[],2); % CIR time, spead freq
figure; mesh(abs(fftshift(fftshift(DS(:,:,plot_device),1),2))); title('Doppler Spread')



