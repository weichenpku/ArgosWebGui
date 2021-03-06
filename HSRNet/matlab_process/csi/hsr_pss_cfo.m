symbol_len = num_carriers;
cp_len = symbol_len/4;
cp_symbol_len = symbol_len+cp_len;
symbol_num = num_symbols_frame;
frame_len = cp_symbol_len*symbol_num;
pss_t = [pss(end-cp_len+1:end) pss];

portnum = size(rx_all_sig,1);
samplelen = size(rx_all_sig,2);
corr_peak_num = 2;
offset_list = zeros(corr_peak_num,portnum);
corr_peak_list = zeros(corr_peak_num,portnum);


frame_tone_len = frame_len + 1920*2;
half_frame_len = frame_len/symbol_num*round(symbol_num/2); % not used now 
capture_symbolnum = num_symbols_frame;
capture_refnum = refnum;
capture_refidx = refidx;
capture_blanknum = blanknum;
capture_blankidx = blankidx;

frame_broken = false; 
half_frame_flag = false; % not used now

for cur_device = 1:portnum 
    if checklist(fileidx,cur_device)~=1 continue; end
    % check whether a whole frame is captured
    tmp_corr = conv(rx_all_sig(cur_device,:),conj(pss));
    corr_threshold = max(abs(tmp_corr))/2;
    
    [corrpeak_list,corridx_list]=findpeaks(abs(tmp_corr(cp_symbol_len+1:end-cp_symbol_len)),'MinPeakHeight',corr_threshold);
    if (size(corridx_list,2)<corr_peak_num)
        frame_broken = true;
    end
    offset_list(:,cur_device)=corridx_list(1:corr_peak_num);
    corr_peak_list(:,cur_device) = corrpeak_list(1:corr_peak_num)/mean(abs(tmp_corr));
end

checkidx = find(checklist==1);
delta_offset = offset_list(2,checkidx)-offset_list(1,checkidx);
assert(abs(max(delta_offset)-frame_tone_len)<10);
assert(abs(min(delta_offset)-frame_tone_len)<10);

offset_list = offset_list(1,:);

% mean_offset = round(mean(mod(offset_list(find(offset_list>0)),frame_len)));
% offset_list2 = reshape(offset_list,[2,device_num]);
% non_zero_idx = find(min(offset_list2)>0);
% offset_range = abs(offset_list2(1,non_zero_idx)-offset_list2(2,non_zero_idx));
% if abs(max(abs(offset_range))-srate/100)<5
%     offset_list2 = mod(offset_list2,srate/100);
%     non_zero_idx = find(min(offset_list2)>0);
%     offset_range = abs(offset_list2(1,non_zero_idx)-offset_list2(2,non_zero_idx));
% end
% if (min(size(offset_range))>0)
%     assert(max(abs(offset_range))<50);
% end
% mean_offset(1:device_num) = max(offset_list2);
% mean_offset(non_zero_idx) = round(mean(offset_list2(:,non_zero_idx),1));  
offset_all_list(fileidx,:) = offset_list;

if (frame_broken == false && min(offset_list)+frame_len>samplelen)
        frame_broken = true;   
end

if (frame_broken == true)
    for cur_device = 1:portnum 
        checklist(fileidx,cur_device) = -2;
    end
    return;
end

ffo_pss_cp=[];
ffo_pss=[];
ffo_all_cp=[];
for cur_device = 1:portnum 
    tmp_idx = offset_list(cur_device);
    rx_pss_t = rx_all_sig(cur_device,tmp_idx:tmp_idx+cp_symbol_len-1);
    rx_pss_t = rx_pss_t - mean(rx_pss_t);

    %% first: IFO
    ifo_idx = [-1,0,1];
    rx_pss_ifo = [];
    corr_list = [];
    maxcorr=0; maxcorr_offset=0; maxcorr_idx=-1;
    for idx = 1:3
        ch = cfo_sig(15e3*ifo_idx(idx), srate, cp_symbol_len, 0);
        rx_pss_ifo(idx,:)=ch.*rx_pss_t;
        corr_list(idx,:)=conv(rx_pss_ifo(idx,:),conj(pss));
        [tmp_peak, tmp_idx]=max(abs(corr_list(idx,:)));
        if tmp_peak > maxcorr
            maxcorr = tmp_peak;
            maxcorr_offset = tmp_idx;
            maxcorr_idx = idx;
        end
    end

    offset = maxcorr_offset;
    if (abs(offset-cp_symbol_len-1)<5)
        offset=cp_symbol_len+1;
    end
    assert(offset==cp_symbol_len+1);
    ifo = ifo_idx(maxcorr_idx)*15e3;
    rx_pss1 = rx_pss_ifo(maxcorr_idx,:);
    %display(['IFO is ',int2str(ifo),'Hz']);

    %% second: FFO  (PSS-CP based)
    rx_pss_cp1 = rx_pss1(offset-cp_symbol_len:offset-symbol_len-1);
    rx_pss_cp2 = rx_pss1(offset-cp_len:offset-1);

    cp_corr=conj(rx_pss_cp1).*rx_pss_cp2;
    ffo_pss_cp(cur_device) = mean(angle(cp_corr))/2/pi*15000;
    %display(['FFO is ',int2str(ffo),'Hz']);
    
    %% second: FFO  (PSS based)
    y1=sum(rx_pss1(offset-symbol_len:offset-symbol_len/2-1).*conj(pss(1:end/2)));
    y2=sum(rx_pss1(offset-symbol_len/2:offset-1).*conj(pss(end/2+1:end)));
    ffo_pss(cur_device) = angle(y2/y1)/pi*15000;


    %% second: FFO (ALL CP based)
    ch = cfo_sig(ifo, srate, cp_symbol_len*capture_symbolnum, 0);
    rxframe = rx_all_sig(cur_device, offset_list(cur_device):offset_list(cur_device)+cp_symbol_len*capture_symbolnum-1);
    rxframe = ch.*(rxframe-mean(rxframe));
    rx_all_cp = zeros(cp_len,capture_symbolnum,2);
    corr_all_cp = zeros(cp_len,capture_symbolnum);
    angle_all_cp = [];
    for idx=1:capture_symbolnum
        if (find(blankidx==idx)>0) continue; end
        rx_all_cp(:,idx,1) = rxframe((idx-1)*cp_symbol_len+1:(idx-1)*cp_symbol_len+cp_len);
        rx_all_cp(:,idx,2) = rxframe(idx*cp_symbol_len+1-cp_len:idx*cp_symbol_len);
        sim=mean(rx_all_cp(:,idx,1)./rx_all_cp(:,idx,2))-1;
        if abs(sim)<0.25  % noise is deleted
            corr_all_cp(:,idx)=conj(rx_all_cp(:,idx,1)).*rx_all_cp(:,idx,2);          
            angle_all_cp = [angle_all_cp  mean(angle(corr_all_cp(:,idx)))/2/pi*15000];
        end
    end
    ffo_all_cp(cur_device) = mean(angle_all_cp);
    
    %display(['FFO2 is ',int2str(ffo2),'Hz']);

    % ffo compensation
    ffo_list(fileidx,cur_device) = ifo+ffo_all_cp(cur_device);
end
