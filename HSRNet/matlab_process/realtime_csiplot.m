function [] = realtime_csiplot(rxdir,fname)
%REALTIME_CSIPLOT Summary of this function goes here
%   Detailed explanation goes here
files = dir([rxdir 'rx*']);
filenum = size(files,1);
h_all_est = [];

for fileidx=1:filenum
    filename = files(fileidx).name;
    if (size(filename,1)<2) continue; end
    if (sum(filename(1:2)=='rx')<2) continue; end
    datahandle(rxdir,filename,fname); 
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end

end

