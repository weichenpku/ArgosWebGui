%% basic parameters
refsig0 = csvread('../../refdata/generation/test_data/dc192000.csv'); 
% refsig0 = csvread('../../refdata/generation/test_data/tone192000_20.csv');


rootpath = '../../rxdata/'; 
load([rootpath file]);

snum = 384000;
srate = 1.92e6;

if period_len_cali
    interp_scale = 16;
else
    interp_scale = 1;
end
snum = snum*interp_scale;
srate = srate*interp_scale;


t = 0:1/srate:(snum-1)/srate;
blf_std = 40e3;
period_len = srate/blf_std;
sigcarrier = exp(-1i*2*pi*blf_std*t);



refsig = [refsig0; refsig0];


idata = eval([device1 '_I']); 
qdata = eval([device1 '_Q']);
iqdata  = idata+1i*qdata;  % original DATA
iqdata_cali = iqdata./refsig.'; 
iqdata_cali=interp(iqdata_cali,interp_scale);

% extended preamble
extended_header = repmat([1 0],1,12);
extended_idx = find(extended_header==1);
preamble = [1 1 0 1 0 0 1 0 0 0 1 1];
preamble_idx = [1,2,4,7,11,12];
preamble_len = size(preamble,2)/2;
extended_preamble = [extended_header preamble];

idata2 = eval([device2 '_I']); 
qdata2 = eval([device2 '_Q']);
gen2_data = abs(idata2+1i*qdata2);
gen2_data = interp(gen2_data,interp_scale);

%% filter1 for iqdata
winsize = period_len/2;
b = (1/winsize)*ones(1,winsize);
a = 1;
y = filter(b,a,iqdata_cali);
iqdata_filter = y(1+winsize/2:end);

%% filter2 for epc_gen2_data
winsize = 4000;
b = (1/winsize)*ones(1,winsize);
a = 1;
y = filter(b,a,gen2_data);
gen2_data1 = gen2_data(1:end-winsize/2) - y(1+winsize/2:end);  % high pass

%% plot figures
if plot_enable
    figure; 
    plot(iqdata_cali); 
    axis([-1 1 -1 1]);
    title('new sig in i-q plane');


    figure; hold on;
    plot(sign(real(sigcarrier(1:interp_scale:end)))*max(abs(gen2_data(1:interp_scale:end))));
    plot(abs(iqdata_cali(1:interp_scale:end)));
    plot(abs(gen2_data(1:interp_scale:end)));
    plot(gen2_data1(1:interp_scale:end));
    title('amplitude of iq signal');
end


%% preamble detect
refidx = refidx*interp_scale;
if data_type_epc
    framelen = period_len*preamble_len*24;
else
    framelen = period_len*preamble_len*8;
end
frame_data = iqdata_filter(refidx:refidx+framelen-1);
frame_rssi = abs(iqdata_filter(refidx:refidx+framelen-1));

dc_part = iqdata_filter(refidx-period_len*5:refidx-1);
dc_val = mean(dc_part);
frame_data = frame_data-dc_val;

if plot_enable
    figure; hold on;
    plot(abs(iqdata_cali(refidx:refidx+framelen-1)));
    plot(abs(iqdata_cali(refidx-period_len*5:refidx-1)));
    plot(abs(gen2_data(refidx:refidx+framelen-1)));
    title('frame data & dc data (original)');
    legend('frame','dc','epc-gen2');

    figure; hold on;
    plot(abs(frame_data)); 
    plot(abs(dc_part-dc_val));
    plot(frame_rssi-mean(frame_rssi));
    legend('frame','dc','rssi');
    title('frame data & dc data (filtered)');
end

% peak detection for sync
sig_corr = [];
for idx = period_len*10+1:period_len*(10+preamble_len*3)
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

if plot_enable
    figure; hold on;
    edges = exp(-1i*2*pi*(1-maxidx:framelen-maxidx)/period_len);
    plot(abs(sig_corr)); plot(abs(frame_data));
    plot(sign(imag(edges))*max(abs(sig_corr)));
    title('Detection before blf cali');
end


%% period len calibration
if period_len_cali
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
else
    period_len2 = period_len;
end



if data_type_epc
    pos_list = period_len2/2*(-24:preamble_len*2*20-1)+maxidx;
else
    pos_list = period_len2/2*(-24:preamble_len*2*4-1)+maxidx;
end

if plot_enable
    figure; hold on;
    plot(frame_data(pos_list(find(extended_preamble==1))),'.','MarkerSize',10);  
    plot(frame_data(pos_list(find(extended_preamble==0))),'.','MarkerSize',10);
    axis([-1 1 -1 1]);
    title('frame data in x-y plane');
end

%% [algorithm1] result output: using positive as h_est
h_est = mean(frame_data(pos_list([extended_idx 24+preamble_idx]))); % use positive as h_est
rawdata = frame_data(pos_list)/h_est;

decode_out = sign(real(rawdata)-0.5);
data_decode = (decode_out+1)/2;
% display(data_decode);

% data_bit_decode = [];
% for idx = 37:2:size(data_decode,2)
%     if (data_decode(idx)==data_decode(idx-1))
%         break;
%     end
%     bit = 1-xor(data_decode(idx),data_decode(idx+1));
%     data_bit_decode = [data_bit_decode bit];
% end

check_result = [extended_header preamble] == data_decode(1:36);
error_num = sum(check_result==0);
display(['[ALG1] error num: ' int2str(error_num) ' of 36']);


noise1 = frame_data(pos_list(1:36)) - extended_preamble*h_est;
sinr1 = conj(h_est)*h_est/mean(conj(noise1).*noise1);
sinr1 = log(sinr1)/log(10)*10;
display(sinr1);

phase_detect = angle(h_est)/pi*180;
display(phase_detect);



%% [algorithm2] re-decheck:  use positive-negative as h_est
p_pos = find(extended_preamble==1); p_est = mean(frame_data(pos_list(p_pos)));
n_pos = find(extended_preamble==0); n_est = mean(frame_data(pos_list(n_pos)));
h_est2 = p_est - n_est;  % use positive-negative as h_est
rawdata2 = (frame_data(pos_list)-n_est)/(p_est-n_est);
decode_out2 = sign(real(rawdata2)-0.5);

data_decode2 = (decode_out2+1)/2;
check_result2 = [extended_header preamble] == data_decode2(1:36);
error_num2 = sum(check_result2==0);
display(['[ALG2] (re-decode)error num : ' int2str(error_num2) ' of 36']);

noise2 = frame_data(pos_list(1:36)) - extended_preamble*h_est2 - n_est;
sinr2 = conj(h_est2)*h_est2/mean(conj(noise2).*noise2);
sinr2 = log(sinr2)/log(10)*10;
display(sinr2);

phase_detect2 = angle(h_est2)/pi*180;
display(phase_detect2);


%% [algorithm3] rssi decode: frame_rssi
p_rssi = mean(frame_rssi(pos_list(find(extended_header==1))));
n_rssi = mean(frame_rssi(pos_list(find(extended_header==0))));
rawdata3 = (frame_rssi(pos_list)-n_rssi)/(p_rssi-n_rssi);
data_decode3 = (sign(abs(rawdata3)-0.5)+1)/2;
check_result3 = [extended_header preamble] == data_decode3(1:36);
error_num3 = sum(check_result3==0);
display(['[ALG3] (RSSI-decode)error num : ' int2str(error_num3) ' of 36']);
% figure; hold on;
% plot((1+1i)*frame_rssi(pos_list(find(extended_header==1))),'.','MarkerSize',10);  
% plot((1+1i)*frame_rssi(pos_list(find(extended_header==0))),'.','MarkerSize',10);

% display detection distance
minval1 = min(abs(abs(rawdata(find(check_result==1)))-0.5));
minval2 = min(abs(abs(rawdata2(find(check_result2==1)))-0.5));
minval3 = min(abs(abs(rawdata3(find(check_result3==1)))-0.5));
disp([minval1 minval2 minval3]');

%% plot figures
if plot_enable
    figure; hold on;
    plot(noise1);
    plot(noise2);
    
    figure; hold on;
    edges = exp(-1i*2*pi*(1-maxidx:framelen-maxidx)/period_len2);
    plot(abs(sig_corr)); plot(abs(frame_data));
    plot(sign(imag(edges))*max(abs(sig_corr)));
    title('Detection after blf cali (with dc offset cancel)');

    figure; hold on;
    plot(abs(sig_corr)); plot(frame_rssi-mean(frame_rssi));
    plot(sign(imag(edges))*max(abs(sig_corr)));
    title('Detection after blf cali (without dc offset cancel)');
end

%% data bit decode
data_bit_buffer = data_decode2;
data_bit_decode = [];
for idx = 37:2:size(data_bit_buffer,2)
    if (data_bit_buffer(idx)==data_bit_buffer(idx-1))
        break;
    end
    bit = 1-xor(data_bit_buffer(idx),data_bit_buffer(idx+1));
    data_bit_decode = [data_bit_decode bit];
end

% checksum crc16
if data_type_epc == true
    check_ret = 1;
    check_len = 96;
    if (size(data_bit_decode,2)<check_len)
        check_ret = 0;
    else
        recv_crc = data_bit_decode(check_len-8*2+1:check_len);
        crc = hex2dec('ffff');
        for idx = 1:check_len-8*2
            if xor(bitget(crc,16),data_bit_decode(idx))
                crc = bitand(crc*2,hex2dec('ffff'));
                crc = bitxor(crc,hex2dec('1021'));
            else
                crc = bitand(crc*2,hex2dec('ffff'));
            end
        end
        crc = hex2dec('ffff') - crc;
        recv_crc = recv_crc*(2.^(15:-1:0)');
        if (crc ~= recv_crc)
            check_ret = 0;
        end
    end
    if (check_ret == 1)
        disp('Checksum CORRECT');
    else
        disp('Checksum ERROR');
    end
else
    if size(data_bit_decode,2)>=16
        disp(['rn16 is ' int2str(data_bit_decode(1:16))]);
    else
        disp(['rn16 is ' int2str(data_bit_buffer(36+1:36+32))]);
    end
end
