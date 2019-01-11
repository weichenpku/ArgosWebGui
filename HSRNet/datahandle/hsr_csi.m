% get rx_all_sig
mean_offset = round(mean(offset_list(find(offset_list>0))))

portnum = size(rx_all_sig,1);
samplelen = size(rx_all_sig,2);
num_symbols_frame = frame_len/cp_symbol_len;

rx_all_frame = zeros(portnum,frame_len);
h_tx = zeros(12*nb_rb,num_symbols_frame,portnum);
h_rx = zeros(12*nb_rb,num_symbols_frame,portnum);
h_est = zeros(12*nb_rb,num_symbols_frame,portnum);
for cur_device = 1:2:portnum
    %% cfo correction
    cfo = cfo_list(cur_device);
    
    df = -cfo;
    phase = 2*pi*df*(1:frame_len)/srate;
    ch = cos(phase)+1i*sin(phase);
    rxframe = rx_all_sig(cur_device,mean_offset:mean_offset+frame_len-1);
    rxframe = ch.*(rxframe-mean(rxframe));
    rx_all_frame(cur_device,:)=rxframe;

    %% CSI
    num_symbols_frame = 120; 
    cp_symbol_len = cp_len + symbol_len; 
    for k = 2:num_symbols_frame
            symbol_start = 1 + (k-1)*cp_symbol_len;
            symbol_end = k*cp_symbol_len; 
            symbol_t = rxframe(symbol_start+cp_len:symbol_end);
            symbol_f = fft(symbol_t)/sqrt(num_carriers);
            rx_f = [symbol_f(2:1+12*nb_rb/2) symbol_f(end-12*nb_rb/2+1:end)];
            % channel estimation: rx_f vs sig_f(k,:)
            h_tx(:,k,cur_device) = sig_f(k,:); 
            h_rx(:,k,cur_device) = rx_f;
            h_est(:,k,cur_device) = rx_f./sig_f(k,:);
    end 

    %est=est(:,2:end,:);
end

figure; plot(h_est(:,3,1)); % frequency
figure; plot(h_est(1,:,1)); % time
