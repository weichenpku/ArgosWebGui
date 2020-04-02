clear; close all;

file = 'test/epoch9/rx0.mat'; 
refsig0 = csvread('../../refdata/generation/test_data/dc192000.csv');

% case 3.31
% file = '3.31/rfid/epoch6/rx0.mat'; 
% refsig0 = csvread('../../refdata/generation/test_data/tone192000_20.csv');

device1 = 'RF3E000006';
device2 = 'RF3E000022';
path = '../../rxdata/'; 
load([path file]);

refidx = 132900;

interp_scale = 16;
snum = 384000; 
srate = 1.92e6;
snum = snum*interp_scale;
srate = srate*interp_scale;

t = 0:1/srate:(snum-1)/srate;

%% need calibrated later
blf_std = 40e3;
period_len = srate/blf_std;
sigcarrier = exp(-1i*2*pi*blf_std*t);



refsig = [refsig0; refsig0];


idata = eval([device1 '_I']); 
qdata = eval([device1 '_Q']);
iqdata  = idata+1i*qdata;
iqdata_cali = iqdata./refsig.';
iqdata_cali=interp(iqdata_cali,interp_scale);

extended_header = repmat([1 0],1,12);
extended_idx = find(extended_header==1);
preamble = [1 1 0 1 0 0 1 0 0 0 1 1];
preamble_idx = [1,2,4,7,11,12];
preamble_len = size(preamble,2)/2;

idata2 = eval([device2 '_I']); 
qdata2 = eval([device2 '_Q']);
epc_data = abs(idata2+1i*qdata2);
epc_data = interp(epc_data,interp_scale);

%% filter1
winsize = period_len/2;
b = (1/winsize)*ones(1,winsize);
a = 1;
y = filter(b,a,iqdata_cali);
iqdata_filter = y(1+period_len/4:end);

%% filter2
winsize = 4000;
b = (1/winsize)*ones(1,winsize);
a = 1;
y = filter(b,a,epc_data);
epc_data1 = epc_data(1:end-winsize/2) - y(1+winsize/2:end);  % high pass

%% plot figures
figure; 
plot(iqdata_cali); 
axis([-1 1 -1 1]);
title('new sig in i-q plane');



figure; hold on;
plot(sign(real(sigcarrier(1:interp_scale:end)))*max(abs(epc_data(1:interp_scale:end))));
plot(abs(iqdata_cali(1:interp_scale:end)));
plot(abs(epc_data(1:interp_scale:end)));
plot(epc_data1(1:interp_scale:end));
title('amplitude of iq signal');

%% preamble detect
refidx = refidx*interp_scale;
framelen = period_len*preamble_len*7;
frame_data = iqdata_filter(refidx:refidx+framelen-1);

dc_part = iqdata_filter(refidx-period_len*5:refidx-1);
dc_val = mean(dc_part);
frame_data = frame_data-dc_val;

figure; hold on;
plot(abs(iqdata_cali(refidx:refidx+framelen-1)));
plot(abs(iqdata_cali(refidx-period_len*5:refidx-1)));
plot(abs(epc_data(refidx:refidx+framelen-1)));
title('frame data & dc data (original)');

figure; hold on;
plot(abs(frame_data)); 
plot(abs(dc_part-dc_val));
%plot(abs(iqdata_cali(refidx:refidx+framelen-1)-dc_val));
title('frame data & dc data (filtered)');

sig_corr = [];
for idx = period_len*10+1:framelen/2
    right = idx+period_len*(preamble_len)-1;
    if (right>size(frame_data,2))
        continue;
    end
    sig0 = frame_data(idx:period_len/2:right);
    sig_corr(idx) = sum(sig0.*conj(preamble));
end
[vallist,idxlist] = findpeaks(abs(sig_corr),'Threshold',0);
%maxidx = idxlist(find(vallist>max(abs(sig_corr))*0.9));
%maxidx = maxidx(1);
maxidx = idxlist(find(vallist==max(vallist)));

%% duration estimate
figure; hold on;
edges = exp(-1i*2*pi*(1-maxidx:framelen-maxidx)/period_len);
plot(abs(sig_corr)); plot(abs(frame_data));
plot(sign(imag(edges))*max(abs(sig_corr)));
title('Detection before blf cali');

min_len = period_len*0.9;
max_len = period_len*1.1;
if (maxidx+round(max_len/2)*-24<1) || (maxidx+round(min_len/2)*(preamble_len*2*4-1) > size(frame_data,2))
    disp('Peak Detection of xcorr failed');
end

energy=[];
for new_halflen = round(min_len/2):1:round(max_len/2)
    idxlist = new_halflen*(-24:preamble_len*2*4-1)+maxidx;
    if (min(idxlist)<1 || max(idxlist)>size(frame_data,2))
        continue;
    end
    energy(new_halflen) = sum(abs(frame_data(idxlist)).^2); % eq. 14
end
period_len2 = 2*find(energy==max(energy));
if min(size(period_len2))>0
    display(['Period len change from ' int2str(period_len) ' to ' int2str(period_len2)]);
end

figure; hold on;
edges = exp(-1i*2*pi*(1-maxidx:framelen-maxidx)/period_len2);
plot(abs(sig_corr)); plot(abs(frame_data));
plot(sign(imag(edges))*max(abs(sig_corr)));
title('Detection after blf cali');


%% result output
pos_list = period_len2/2*(-24:preamble_len*2*4-1)+maxidx;
h_est = mean(frame_data(pos_list([extended_idx 24+preamble_idx]))); 
rawdata = frame_data(pos_list)/h_est;

decode_out = sign(abs(rawdata)-0.5);
data_decode = (decode_out+1)/2;
display(data_decode);

check_result = [extended_header preamble] == data_decode(1:36);
error_num = sum(check_result==0);
if error_num == 0
    display('code detect is CORRECT!');
else
    display('code detect is ERROR!');
    display(['error num: ' int2str(error_num) ' of 36']);
    disp(find(check_result==0));
end

phase_detect = angle(h_est)/pi*180;
display(phase_detect);

%% re-decheck 
extended_preamble = [extended_header preamble];
p_pos = find(extended_preamble==1 & check_result==1); p_est = mean(frame_data(pos_list(p_pos)));
n_pos = find(extended_preamble==0 & check_result==1); n_est = mean(frame_data(pos_list(n_pos)));
h_est2 = p_est - n_est;
rawdata2 = (frame_data(pos_list)-n_est)/(p_est-n_est);
decode_out2 = sign(abs(rawdata2)-0.5);
data_decode2 = (decode_out2+1)/2;
check_result2 = [extended_header preamble] == data_decode2(1:36);
error_num2 = sum(check_result2==0);
display(['(re-decode)error num : ' int2str(error_num2) ' of 36']);