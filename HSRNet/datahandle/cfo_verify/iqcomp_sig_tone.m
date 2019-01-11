%input: rx_t
tmp_corr = conv(rx_t,conj(pss));
[tmp_peak,tmp_idx]=max(abs(tmp_corr(1:round(end/2))));
rx_sig = rx_t(tmp_idx-symbol_len-cp_len-19200:tmp_idx-symbol_len-cp_len-1+19200);

%input: cfo
len=size(rx_sig,2);
df = -cfo;
phase = 2*pi*df*(1:len)/srate;
ch = cos(phase)+1i*sin(phase);
rx_sig1 = ch.*rx_sig;

%input: rx_cfo
rx_cfo_f = fftshift(fft(rx_cfo));
[value,freq_idx] = max(abs(rx_cfo_f));
z1=rx_cfo_f(19202-freq_idx);
z2=rx_cfo_f(freq_idx);
rot = (angle(z1)+angle(z2))/2; % rotate angle
scale = (abs(z1)+abs(z2))/abs(abs(z1)-abs(z2));  % scale of ellipse
display([rot; scale]);