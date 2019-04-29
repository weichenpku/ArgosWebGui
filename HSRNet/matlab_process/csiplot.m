rxdir=['../rxdata/4.25/4.25.3/epoch0/'];
fconf = '../conf/conf_LTE.json';

data_batch_handle;

rxdir=['../rxdata/4.3.2/3/'];
unwrap_able = 1;
ref_port = 3;


load([rxdir 'csi.mat']);

% csi insert
h_all_est(:,1:60:end) = h_all_est(:,2:60:end).^2./h_all_est(:,3:60:end);
h_all_angle = angle(h_all_est);
h_shape=size(h_all_est);


if unwrap_able
    disp('unwrap_able');
    angle_unwrap=unwrap(h_all_angle,[],1);
    angle_unwrap=unwrap(angle_unwrap,[],2);
    angle_unwrap=unwrap(angle_unwrap,[],1);
else
    disp('unwrap_disable');
    angle_unwrap=h_all_angle;
end

for i=1:h_shape(3)
    figure; mesh(angle_unwrap(:,:,i)); title(['angle of port' int2str(i)]);
end


figure;
for i=1:h_shape(3)
    if i==ref_port continue; end
     mesh(angle_unwrap(:,:,i)-angle_unwrap(:,:,ref_port));  hold on; figure;
end