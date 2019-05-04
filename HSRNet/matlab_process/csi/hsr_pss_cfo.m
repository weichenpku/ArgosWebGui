symbol_len = num_carriers;
cp_len = symbol_len/4;
cp_symbol_len = symbol_len+cp_len;
symbol_num = 2*6*10;  duration_time=0.01;
frame_len = cp_symbol_len*symbol_num;
pss_t = [pss(end-cp_len+1:end) pss];

portnum = size(rx_all_sig,1);
samplelen = size(rx_all_sig,2);
offset_list = zeros(1,portnum);

frame_broken = false;
for cur_device = 1:portnum 
    if checklist(fileidx,cur_device)~=1 continue; end
    % check whether a whole frame is captured
    tmp_corr = conv(rx_all_sig(cur_device,:),conj(pss));
    [tmp_peak,tmp_idx]=max(abs(tmp_corr(cp_symbol_len+1:end-cp_symbol_len)));
    
    frame_tone_len = frame_len + frame_len/10*2;
    if (tmp_idx-frame_tone_len>0) tmp_idx = tmp_idx-frame_tone_len; end
    if (tmp_idx+frame_len-1>size(rx_all_sig,2))
        frame_broken = true;
        break;
    end
    offset_list(cur_device)=tmp_idx;
    
    rx_pss_t = rx_all_sig(cur_device,tmp_idx:tmp_idx+cp_symbol_len-1);
    rx_pss_t = rx_pss_t - mean(rx_pss_t);

    %% first: IFO
    ifo_idx = [-1,0,1];
    rx_pss_ifo = [];
    corr_list = [];
    maxcorr=0; maxcorr_offset=0; maxcorr_idx=-1;
    for idx = 1:3
        df = 15e3*ifo_idx(idx);
        phase = 2*pi*df*(1:cp_symbol_len)/srate;
        ch = cos(phase)+1i*sin(phase);
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
    ifo = ifo_idx(maxcorr_idx)*15000*-1;
    rx_pss1 = rx_pss_ifo(maxcorr_idx,:);
    %display(['IFO is ',int2str(ifo),'Hz']);

    %% second: FFO  (PSS CP based)
    rx_pss_cp1 = rx_pss1(offset-cp_symbol_len:offset-symbol_len-1);
    rx_pss_cp2 = rx_pss1(offset-cp_len:offset-1);

    cp_corr=conj(rx_pss_cp1).*rx_pss_cp2;
    ffo = mean(angle(cp_corr))/2/pi*15000;
    %display(['FFO is ',int2str(ffo),'Hz']);
    
        % ffo compensation
        df = -ffo;
        phase = 2*pi*df*(1:cp_symbol_len)/srate;
        ch = cos(phase)+1i*sin(phase);
        rx_pss2 = ch.*rx_pss1;
        % PSS based
        y1=sum(rx_pss2(offset-symbol_len:offset-symbol_len/2-1).*conj(pss(1:end/2)));
        y2=sum(rx_pss2(offset-symbol_len/2:offset-1).*conj(pss(end/2+1:end)));
        ffo2=angle(y2/y1)/pi*15000;


    %% third: FFO (ALL CP based)
    df = -ifo-ffo;
    phase = 2*pi*df*(1:frame_len)/srate;
    rxframe = rx_all_sig(cur_device, offset_list(cur_device):offset_list(cur_device)+frame_len-1);
    rxframe = exp(1i*phase).*(rxframe-mean(rxframe));
    rx_all_cp = zeros(cp_len,frame_len/cp_symbol_len,2);
    corr_all_cp = zeros(cp_len,frame_len/cp_symbol_len);
    angle_all_cp = [];
    for idx=1:frame_len/cp_symbol_len
        rx_all_cp(:,idx,1) = rxframe((idx-1)*cp_symbol_len+1:(idx-1)*cp_symbol_len+cp_len);
        rx_all_cp(:,idx,2) = rxframe(idx*cp_symbol_len+1-cp_len:idx*cp_symbol_len);
        sim=mean(rx_all_cp(:,idx,1)./rx_all_cp(:,idx,2))-1;
        if abs(sim)<0.25
            corr_all_cp(:,idx)=conj(rx_all_cp(:,idx,1)).*rx_all_cp(:,idx,2);          
            angle_all_cp = [angle_all_cp  mean(angle(corr_all_cp(:,idx)))/2/pi*15000];
        end
    end
    ffo_all_cp = mean(angle_all_cp);
    
    %display(['FFO2 is ',int2str(ffo2),'Hz']);

    % ffo compensation
    cfo=ifo+ffo_all_cp;
    cfo_list(fileidx,cur_device) = cfo;
end

if (frame_broken == true)
    for cur_device = 1:portnum 
        checklist(fileidx,cur_device) = -2;
    end
end
%display(cfo_list);