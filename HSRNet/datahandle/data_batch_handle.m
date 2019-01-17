clear all;
close all;

h_all_est = [];
for fileidx=1:9
    %if (fileidx==7) continue; end
    datahandle
    close all;
    h_all_est(:,1+60*(fileidx-1):60*fileidx,:)=fftshift(h_full_est,1);
end
a=[];
a(:,:,1)=mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,2)),2*pi);
a(:,:,2)=mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,3)),2*pi);
a(:,:,3)=mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,4)),2*pi);
a(:,:,4)=mod(angle(h_all_est(:,:,1)),2*pi);
%save('csi1.mat','a');

figure; mesh(angle(h_all_est(:,:,1)));
figure; mesh(angle(h_all_est(:,:,2)));
figure; mesh(mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,2)),2*pi));
figure; mesh(mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,3)),2*pi));
figure; mesh(mod(angle(h_all_est(:,:,1))-angle(h_all_est(:,:,4)),2*pi));

