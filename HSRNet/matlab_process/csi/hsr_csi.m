% get rx_all_sig

portnum = size(rx_all_sig,1);
samplelen = size(rx_all_sig,2);
refsig_len = capture_symbolnum*cp_symbol_len;

rx_all_frame = zeros(portnum,refsig_len);
h_tx = zeros(12*nb_rb,capture_symbolnum,portnum);
h_rx = zeros(12*nb_rb,capture_symbolnum,portnum);
h_est = zeros(12*nb_rb,capture_symbolnum,portnum);

for cur_device = 1:portnum
    device_no = floor((cur_device+1)/2);
    if checklist(fileidx,cur_device)~=1 continue; end
    %% cfo correction
    ch = cfo_sig(cfo_list(fileidx,cur_device),srate,refsig_len,0);
    rxframe = rx_all_sig(cur_device,offset_list(cur_device):offset_list(cur_device)+refsig_len-1);
    rxframe = ch.*(rxframe-mean(rxframe));
    rx_all_frame(cur_device,:)=rxframe;

    %% CSI
    cp_symbol_len = cp_len + symbol_len; 
    for k = 2:capture_symbolnum
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

if (checklist(fileidx,plot_device)==1)
    plotrange=max(max(abs(h_est(:,:,plot_device))));
    if (plotrange==0) plotrange=1; end
    figure; plot(h_est(:,2,plot_device)); title('csi vs frequency'); axis([-plotrange plotrange -plotrange plotrange]);
    figure; plot(h_est(80,2:end,plot_device)); title('csi vs time');  axis([-plotrange plotrange -plotrange plotrange]);
end


% csi change => rfo
delta_idx = find(capture_refidx(2:end)-capture_refidx(1:end-1)>1); % for brrr
if (strcmp(sig_type,'br'))
    delta_idx = [];
end
h_sig_est = h_est(:,capture_refidx,:);
delta_angle = angle(h_sig_est(:,2:end,:))-angle(h_sig_est(:,1:end-1,:));
delta_angle(:,delta_idx,:)=[];


angle_est = delta_angle;
for cur_device=1:portnum
    if checklist(fileidx,cur_device)~=1 
        continue; 
    end
    angle_unwrap = angle_est(:,:,cur_device);
    idxlist=find(angle_unwrap>pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap>pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap<-pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    idxlist=find(angle_unwrap<-pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    %mesh(angle_unwrap);
    if (strcmp(sig_type,'br'))
        rfo_cfo_delta = mean(mean(angle_unwrap))*srate/(2*pi*2*cp_symbol_len);
    end
    if (strcmp(sig_type,'brrr'))
        rfo_cfo_delta = mean(mean(angle_unwrap))*srate/(2*pi*cp_symbol_len);
    end 
    rfo_list(fileidx,cur_device) = cfo_list(fileidx,cur_device) + rfo_cfo_delta;
end
%disp(rfo_list);