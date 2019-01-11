[carriernum, symbolnum, portnum] = size(h_est);

weight_abs = zeros(carriernum, symbolnum); % weight scale
weight = zeros(carriernum, symbolnum, portnum);   % weight calculate
rx_weighted =  zeros(carriernum, symbolnum, portnum);

for i = 1 : carriernum
    for j = 1 : symbolnum
        weight_abs(i,j) = sqrt(sum(abs(h_full_est(i,j,:)).^2,3));
        for k = 1 : 2 : portnum
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

%snr of receive bf
p_bf_sig=[];
p_bf_noi=[];
if type_len > 1
   for idx=type_len+1:type_len:symbolnum
       p_bf_sig = [p_bf_sig  mean(abs(h_bf_est(:,idx)).^2)];
       p_bf_noi = [p_bf_noi  mean(abs(h_bf_est(:,idx+1)).^2)];
   end
end
bf_snr=log(mean(p_bf_sig/p_bf_noi))/log(10)*10;
display(['snr of bf is ' num2str(bf_snr)]);

