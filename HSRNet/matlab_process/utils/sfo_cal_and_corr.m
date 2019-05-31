h_sig_est = h_est(:,2:2:end,:);
[carriers, symbols, portnum] = size(h_sig_est);
freq_offset = zeros(carriers,portnum);

freq_slope = zeros(1,portnum);
freq_bias = zeros(1,portnum);

subcarrier_idx = [2:1+12*nb_rb/2 symbol_len-12*nb_rb/2+1:symbol_len];
subcarrier_freq = [-12*nb_rb/2:-1 1:12*nb_rb/2];

for i = 1:portnum
    phase_change = unwrap(angle(h_sig_est(:,:,i)),[],2);
    for j=1:carriers
        x=[ones(symbols,1),(1:symbols)'];
        y=phase_change(j,:)';
        [b,bint,r,rint,stats] = regress(y,x);
        %plot(y); hold on; plot(b(1)+b(2)*(1:symbols));
        freq_offset(j,i) = b(2)*srate/(2*cp_symbol_len)/(2*pi);
    end
    freq_x = [ones(size(subcarrier_freq,2),1) subcarrier_freq'];
    freq_y = fftshift(freq_offset(:,i));
    if (max(freq_y)-min(freq_y)>2*pi) 
        freq_y = unwrap(freq_y);
    end
    [freq_b,bint,r,rint,stats] = regress(freq_y,freq_x);
    %plot(freq_y); hold on; plot(freq_b(1)+freq_b(2)*(1:size(subcarrier_freq,2)));
    freq_slope(i) = freq_b(2);
    freq_bias(i) = freq_b(1);
end

cfo_mean_est = mean(freq_bias); display(cfo_mean_est);
sfo_mean_slope = mean(freq_slope); display(sfo_mean_slope);
if exist('sfo_force')
    sfo_slope_est = sfo_force;
else
    sfo_slope_est = sfo_mean_slope;    
end
display(sfo_slope_est);

%% sfo correlation
sfo_sc_corr = (-symbol_len/2:symbol_len/2-1) * sfo_slope_est;
sfo_corr = fftshift(sfo_sc_corr);
sfo_phase_corr = sfo_corr(subcarrier_idx);

h_sig_corr = exp(-1i*2*pi*sfo_phase_corr'*(2*cp_symbol_len/srate*(1:symbols)+ts/1e9)); % important with ts
%h_sig_corr = exp(-1i*2*pi*sfo_phase_corr'*(2*cp_symbol_len/srate*(1:symbols))); % without ts
%h_sig_corr = exp(-1i*2*pi*sfo_phase_corr'*(0*2*cp_symbol_len/srate*(1:symbols))); % no sfo corr

h_sig_est_corr=[];
for i=1:portnum
    h_sig_est_corr(:,:,i) = h_sig_est(:,:,i) .* h_sig_corr;
end

h_est(:,2:2:end,:) = h_sig_est_corr;
figure; mesh(angle(h_est(:,2:2:end,1)));