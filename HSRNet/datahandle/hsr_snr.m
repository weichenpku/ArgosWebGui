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
    sig_list=[];
    noi_list=[];
    snr_list=[];
    for cur_device=1:2:portnum
        p_sig=[];
        p_noi=[];
        for idx=type_len+1:type_len:symbolnum
            p_sig = [p_sig  mean(abs(h_rx(:,idx,cur_device)).^2)];
            p_noi = [p_noi  mean(abs(h_rx(:,idx+1,cur_device)).^2)];
        end
        sig_list(cur_device)=mean(p_sig);
        noi_list(cur_device)=mean(p_noi);
        snr_list(cur_device)=log(mean(p_sig)/mean(p_noi))/log(10)*10;
    end
end

% ber calculate => get ber_list
if type_len ~= 2
    ber_list=[];
    for cur_device=1:2:portnum
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
end

% csi insert
h_full_est=[];
for cur_device=1:2:portnum
    for idx=type_len+1:type_len:symbolnum
        for k=1:type_len
            cur_idx=idx+k-1;
            if type(k)==1
                h_full_est(:,cur_idx,cur_device) = h_est(:,cur_idx,cur_device);
            else
                h_full_est(:,cur_idx,cur_device) = (h_est(:,cur_idx-1,cur_device)+h_est(:,cur_idx+1,cur_device))/2;
            end
        end
    end
end

% CIR and doppler spread
CIR=ifft(h_full_est,[],1); % CIR time, symbol time
figure; mesh(abs(fftshift(CIR(:,:,1),1)));

PDP = mean(CIR.^2,2); % CIR time
figure; plot(fftshift((abs(PDP(:,:)))));

DS = fft(CIR,[],2); % CIR time, spead freq
figure; mesh(abs(fftshift(fftshift(DS(:,:,1),1),2)));



