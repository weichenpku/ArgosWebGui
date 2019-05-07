% get rx_all_sig
% mean_offset = round(mean(mod(offset_list(find(offset_list>0)),frame_len)));
offset_list2 = reshape(offset_list,[2,device_num]);
non_zero_idx = find(min(offset_list2)>0);
offset_range = abs(offset_list2(1,non_zero_idx)-offset_list2(2,non_zero_idx));
% if abs(max(abs(offset_range))-srate/100)<5
%     offset_list2 = mod(offset_list2,srate/100);
%     non_zero_idx = find(min(offset_list2)>0);
%     offset_range = abs(offset_list2(1,non_zero_idx)-offset_list2(2,non_zero_idx));
% end

if (min(size(offset_range))>0)
    assert(max(abs(offset_range))<5);
end
mean_offset(1:device_num) = max(offset_list2);
mean_offset(non_zero_idx) = round(mean(offset_list2(:,non_zero_idx),1));  
offset_all_list(fileidx,:) = mean_offset;

portnum = size(rx_all_sig,1);
samplelen = size(rx_all_sig,2);
num_symbols_frame = capture_symbolnum; 
refsig_len = num_symbols_frame*cp_symbol_len;

rx_all_frame = zeros(portnum,refsig_len);
h_tx = zeros(12*nb_rb,num_symbols_frame,portnum);
h_rx = zeros(12*nb_rb,num_symbols_frame,portnum);
h_est = zeros(12*nb_rb,num_symbols_frame,portnum);

for cur_device = 1:portnum
    device_no = floor((cur_device+1)/2);
    if checklist(fileidx,cur_device)~=1 continue; end
    %% cfo correction
    cfo = cfo_list(fileidx,cur_device);
    
    df = -cfo;
    phase = 2*pi*df*(1:refsig_len)/srate;
    ch = cos(phase)+1i*sin(phase);
    rxframe = rx_all_sig(cur_device,mean_offset(device_no):mean_offset(device_no)+refsig_len-1);
    rxframe = ch.*(rxframe-mean(rxframe));
    rx_all_frame(cur_device,:)=rxframe;

    %% CSI
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

if (checklist(fileidx,plot_device)==1)
    range=max(max(abs(h_est(:,:,plot_device))));
    figure; plot(h_est(:,51,plot_device)); title('csi vs frequency'); axis([-range range -range range]);
    figure; plot(h_est(80,2:end,plot_device)); title('csi vs time');  axis([-range range -range range]);
end


% csi change => rfo
h_sig_est = h_est(:,3:2:end,:);
angle_est = [];
for cur_device=1:portnum
    if checklist(fileidx,cur_device)~=1 
        continue; 
    end
    angle_est(:,:,cur_device) = angle(h_sig_est(:,2:end,cur_device))-angle(h_sig_est(:,1:end-1,cur_device));
    angle_unwrap = angle_est(:,:,cur_device);
    idxlist=find(angle_unwrap>pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap>pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)-pi;
    idxlist=find(angle_unwrap<-pi); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    idxlist=find(angle_unwrap<-pi/2); angle_unwrap(idxlist)=angle_unwrap(idxlist)+pi;
    %mesh(angle_unwrap);
    rfo_cfo_delta = mean(mean(angle_unwrap))*srate/(2*pi*2*cp_symbol_len);
    rfo_list(fileidx,cur_device) = cfo_list(fileidx,cur_device) + rfo_cfo_delta;
end
%disp(rfo_list);