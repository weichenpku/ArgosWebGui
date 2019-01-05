function [ f_test ] = freq_cal(sig_f, srate, idx, neighbor)

%% frequency calculation
[size1, size2] = size(sig_f);
if size2==1
    sig_f = sig_f';
    [size1, size2] = size(sig_f);
end
mask = zeros(1,size2);
mask(idx-neighbor:idx+neighbor) = ones(1,neighbor*2+1);
%mask(19202-idx-neighbor:19202-idx+neighbor) = ones(1,neighbor*2+1);

rx_f_new = sig_f.*mask;
rx_t_new = ifft(fftshift(rx_f_new));
figure; plot(real(rx_t_new)); hold on; plot(imag(rx_t_new));

ang = angle(conj(rx_t_new'));  % ' represent transpose & conjugate 
offset=0;
[size1,size2]=size(ang);
for i=(2:size1)
    ang(i)=ang(i)+offset;
    if ang(i)<ang(i-1) - pi
        ang(i)=ang(i)+2*pi;
        offset=offset+2*pi;
    end
    if ang(i)>ang(i-1)+pi;
        ang(i)=ang(i)-2*pi;
        offset=offset-2*pi;
    end
end
x=[ones(size1,1),(1:size1)'];
y=ang;
[b, bint,r,rint,stats]=regress(y,x);
f_test = b(2)/(2*pi)*srate; 
% figure; plot(ang);  hold on; plot(b(1)+b(2)*(1:size1));

end

