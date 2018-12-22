% fileidx from hsr_cfo
hsr_rxdata; % get rx_sig

[antnum, samplenum]= size(rx_all_sig);

%% cfo correction
cfo = 0;
cfo_phase = -2*pi*cfo*(1:samplenum)/samplenum*(20/1000);
rx_sig = rx_sig .* (cos(cfo_phase) +1i*sin(cfo_phase));

%% correlation for sync
offset = 0;
for idx = 1:antnum
    rx_one_sig = rx_all_sig(idx,:);
    corr_t = conv(rx_one_sig,conj(pss_t)); % xcorr is similar with conv
    figure; plot(abs(corr_t));
    [peak, index] = max(abs(corr_t(1:round(end/2))));
    offset = offset + index;
end
offset = round(offset / antnum);

%% Pick the frame
prefix_length = num_carriers/4;
if (offset<=prefix_length + num_carriers) offset=offset+samplenum/2; end
frame_start = offset - prefix_length - num_carriers;
rx_all_frame = rx_all_sig(:,frame_start:frame_start+round(samplenum/2)-1);

%% CSI
symbol_len = prefix_length + num_carriers;
num_symbols_frame = 120; % samplenum/2/symbol_len
est = zeros(12*nb_rb,num_symbols_frame,antnum);
for idx = 1:antnum
    for k = 2:num_symbols_frame
        symbol_start = 1 + (k-1)*symbol_len;
        symbol_end = k*symbol_len; 
        symbol_t = rx_all_frame(idx,symbol_start+prefix_length:symbol_end);
        symbol_f = fft(symbol_t)/sqrt(num_carriers);
        rx_f = [symbol_f(2:1+12*nb_rb/2) symbol_f(end-12*nb_rb/2+1:end)];
        % channel estimation: rx_f vs sig_f(k,:)
        est(:,k,idx) = rx_f./sig_f(k,:);
    end 
end

est=est(:,2:end,:);
