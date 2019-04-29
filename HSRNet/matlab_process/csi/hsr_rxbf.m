[carriernum, symbolnum, portnum] = size(h_est);

weight_abs = zeros(carriernum); % weight scale
weight = zeros(carriernum, portnum);   % weight calculate
rx_weighted =  zeros(carriernum, symbolnum, portnum);

weight_abs = sqrt(sum(abs(h_sig).^2,2));
for k = 1 : portnum
    if checklist(k)~=1 continue; end
    weight(:,k) = conj(h_sig(:,k))./weight_abs;
    for sn = 2:symbolnum
        rx_weighted(:,sn,k) = h_rx(:,sn,k).*weight(:,k); 
    end
end
    
% receive bf
h_bf_rx = zeros(carriernum, symbolnum);
h_bf_est = zeros(carriernum, symbolnum);
for idx = 2 : symbolnum
    symbol_t = ifft(rx_weighted(:,idx,:),[],1);
    symbol_bf_t = sum(symbol_t,3);
    symbol_bf_f = fft(symbol_bf_t);
    h_bf_rx(:,idx)=symbol_bf_f;
    h_bf_est(:,idx)=symbol_bf_f./h_tx(:,idx,1);
end
figure; hold on; 
for idx = 1 : portnum
    plot(real(symbol_t(:,1,idx))); title('Rx Beamforming');
end
    
% snr of receive bf
h_bf_sig = mean(h_bf_est(:,2:end),2);
p_bf_sig = abs(h_bf_sig).^2;
h_bf_noi = h_bf_est-h_bf_sig;
p_bf_noi = mean(abs(h_bf_noi(:,2:end)).^2,2);
bf_snr=log(mean(p_bf_sig)/mean(p_bf_noi))/log(10)*10;
bf_snr_list(fileidx) = bf_snr;
%display(['snr of bf is ' num2str(bf_snr)]);

bf_snr_ = log(sum(10.^(snr_list(fileidx,:)/10)))/log(10)*10;
max_snr_list(fileidx) = bf_snr_;
%display(['Upper bound of snr is ' num2str(bf_snr_)]);


% snr vs freq
snr_freq = log(p_sig./p_noi)/log(10)*10;
snr_bf_freq_ = log(sum(10.^(snr_freq/10),2))/log(10)*10;
snr_bf_freq = log(p_bf_sig./p_bf_noi)/log(10)*10;
figure; hold on;
plot(snr_freq(:,1)); plot(snr_freq(:,2)); plot(snr_bf_freq); plot(snr_bf_freq_); 
legend('ant1','ant2','real bf','supposed bf');