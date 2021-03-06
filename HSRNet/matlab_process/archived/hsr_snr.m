%get rx_all_frame, h_est
[carriernum, symbolnum, portnum] = size(h_est);
type = [];
if val.sig_type=='sig_rbrr.csv'
    type = [1, 0, 1, 1];
elseif val.sig_type=='sig_rb.csv'
    type = [1, 0];
elseif val.sig_type=='sig_rbrr.csv'
    type = [1];
end

type_len=size(type,2);
% snr calculate => get snr_list
if type_len > 1
    snr_list=zeros(1,portnum);
    p_sig=zeros(carriernum,symbolnum/4-1,portnum);
    p_noi=zeros(carriernum,symbolnum/4-1,portnum);
    for cur_device=1:portnum
        if checklist(cur_device)~=1 continue; end
        for idx=type_len+1:type_len:symbolnum
            p_sig(:,(idx-1)/type_len,cur_device) = abs(h_rx(:,idx,cur_device)).^2;
            p_noi(:,(idx-1)/type_len,cur_device) = abs(h_rx(:,idx+1,cur_device)).^2;
        end
        snr_list(cur_device)=log(mean(mean(p_sig(:,:,cur_device),2),1)/mean(mean(p_noi(:,:,cur_device),2),1))/log(10)*10;
    end
    display(snr_list);
end

% ber calculate => get ber_list
if type_len ~= 2
    ber_list=[];
    for cur_device=1:portnum
        if checklist(cur_device)~=1 continue; end
        total_symbol=0;
        error_symbol=0;
        for idx=type_len+1:type_len:symbolnum
            h_vec = h_est(:,idx-1,cur_device); % use the last Hest
            rx_vec = h_rx(:,idx,cur_device)./h_vec;
            tx_vec = h_tx(:,idx,cur_device);
            total_symbol=total_symbol+carriernum;
            error_symbol=error_symbol+ofdm_judge(rx_vec,tx_vec,'QAM',carriernum);
        end
        ber_list(cur_device)=error_symbol/total_symbol;
    end
    display(ber_list);
end

% csi insert
h_full_est = [];
angle_full_est = [];
rfo = [];
for cur_device=1:portnum
    if checklist(cur_device)~=1 
        continue; 
    end
    plot_device = cur_device;
    for idx=type_len+1:type_len:symbolnum
        for k=1:type_len
            cur_idx=idx+k-1;
            if type(k)==1
                h_full_est(:,cur_idx,cur_device) = h_est(:,cur_idx,cur_device);
            else
                h_full_est(:,cur_idx,cur_device) = (h_est(:,cur_idx-1,cur_device)+h_est(:,cur_idx+1,cur_device))/2;
            end
            angle_full_est(:,cur_idx,cur_device) = angle(h_full_est(:,cur_idx,cur_device))-angle(h_full_est(:,cur_idx-1,cur_device));
        end
    end
    angle_unwrap = angle_full_est;
    idxlist=find(angle_unwrap>pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap>pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap<-pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    idxlist=find(angle_unwrap<-pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    
    rfo(cur_device) = cfo_list(cur_device) + mean(mean(angle_unwrap(:,6:end,cur_device)))*srate/(2*pi*cp_symbol_len);
end

% CIR and doppler spread
CIR=ifft(h_full_est,[],1); % CIR time, symbol time
figure; mesh(abs(fftshift(CIR(:,:,plot_device),1))); title('CIR');

PDP = mean(CIR.^2,2); % CIR time
figure; plot(fftshift((abs(PDP(:,:))))); title('PDP');

DS = fft(CIR,[],2); % CIR time, spead freq
figure; mesh(abs(fftshift(fftshift(DS(:,:,plot_device),1),2))); title('Doppler Spread')



