[carriernum, symbolnum, portnum] = size(h_est);

weight_abs = zeros(carriernum, symbolnum); % weight scale
weight = zeros(carriernum, symbolnum, portnum);   % weight calculate
rx_weighted =  zeros(carriernum, symbolnum, portnum);

for i = 1 : carriernum
    for j = 1 : symbolnum
        weight_abs(i,j) = sqrt(sum(abs(h_full_est(i,j,:)).^2,3));
        for k = 1 : portnum
            if checklist(k)~=1 continue; end
            if weight_abs(i,j)>0
                weight(i,j,k) = conj(h_full_est(i,j,k))/weight_abs(i,j);
                rx_weighted(i,j,k) = h_rx(i,j,k).*weight(i,j,k);
            end
        end
    end
end

% receive bf
h_bf_rx = zeros(carriernum, symbolnum);
h_bf_est = zeros(carriernum, symbolnum);
for idx = 1 : symbolnum
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
    
%snr of receive bf
p_bf_sig=zeros(carriernum, symbolnum);
p_bf_noi=zeros(carriernum, symbolnum);
if type_len > 1
   for idx=type_len+1:type_len:symbolnum
       p_bf_sig(:,(idx-1)/type_len) = abs(h_bf_est(:,idx)).^2;
       p_bf_noi(:,(idx-1)/type_len) = abs(h_bf_est(:,idx+1)).^2;
   end
end
bf_snr=log(mean(mean(p_bf_sig,2),1)/mean(mean(p_bf_noi,2),1))/log(10)*10;
display(['snr of bf is ' num2str(bf_snr)]);

bf_snr_ = log(sum(10.^(snr_list/10)))/log(10)*10;
display(bf_snr_);
% snr_list vs bf_snr
% p_sig,p_noi vs p_bf_sig,p_bf_noi