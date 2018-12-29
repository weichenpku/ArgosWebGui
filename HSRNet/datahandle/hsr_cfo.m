fileidx = 1;
rxdevice = 'RF3E000010';
rxdir = '../rxdata/cfo_t5/';
sfidx = 3; % 1-10
cfo = -7; % (Hz) CFO from PSS
hsr_csi; % get est(12*nb_rb,num_symbols_frame,antnum)

% CIR and doppler spread
CIR =ifft(est,[],1); % CIR time, symbol time
PDP = mean(CIR.^2,2); % CIR time
DS = fft(CIR,[],2); % CIR time, spead freq

if (sfidx==1)
    est_sf = est(:,1:11,:);
else
    est_sf = est(:,12*(sfidx-1):12*sfidx-1,:);
end

% deal with subframe
cfo = 0;
cfo_turn = 1;
for idx = 1: cfo_turn
    % cfo correct
    
    % new est
    
    % cfo calculation
    vec_change = est_sf(:,2:end,:)./est_sf(:,1:end-1,:);
    vec_angle = angle(vec_change);
    vec_amp= abs(vec_change);
    doppler_freq = mean(mean(vec_angle))/(2*pi*(1/1000/12));
    
end