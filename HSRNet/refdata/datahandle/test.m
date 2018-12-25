load('I-RF3E000006-0.mat')
tx_i = wave;
load('Q-RF3E000006-0.mat')
tx_q = wave;
load('I-RF3E000022-1.mat')
rx_i = wave;
load('Q-RF3E000022-1.mat')
rx_q = wave;

tx = tx_i + 1i*tx_q;
tx_f = fftshift(fft(tx));
rx0 = rx_i + 1i*rx_q;
rx = rx0(10001:29200);
rx_f = fftshift(fft(rx));
srate = 1.92e6;
fx = linspace(-srate/2,srate/2, 19200);
plot(fx,log(abs(tx_f))); hold on; plot(fx,log(abs(rx_f)));

tx_freq = freq_cal(tx_f, 1.92e6, 1);
rx_freq = freq_cal(rx_f, 1.92e6, 1);

delta_f = tx_freq - rx_freq;
delta_p = 2*pi*delta_f*linspace(0,19200/1.92e6,19200);
delta_s = cos(delta_p)+1i*sin(delta_p);

rx_cfo = rx.*delta_s;
rx_cfo_f = fftshift(fft(rx_cfo));
figure;
plot(fx,log(abs(tx_f))); hold on; plot(fx,log(abs(rx_cfo_f)));

dc=mean(rx_cfo);

plot(abs(rx_cfo-dc));