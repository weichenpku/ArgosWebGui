clear all;
close all;

h_all_est = [];
filenum=31;
for fileidx=1:filenum
    %if (fileidx<=2) continue; end
    datahandle  %data handle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end
a=[];
a(:,:,1)=mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,2)),2*pi);
a(:,:,2)=mod(angle(h_all_est(:,:,1)),2*pi);
a(:,:,3)=mod(angle(h_all_est(:,:,2)),2*pi);
%save('csi1.mat','a');

figure; mesh(a(:,:,1));
figure; mesh(a(:,:,2));
figure; mesh(a(:,:,3));