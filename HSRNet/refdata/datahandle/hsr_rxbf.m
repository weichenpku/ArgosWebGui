fileidx = 1;

num_refsig_frame = num_symbols_frame - 1;
hsr_csi; % get est(12*nb_rb,num_refsig_frame,antnum)

% weight scale
h_abs = zeros(12*nb_rb,num_refsig_frame);
% weight calculate
h_weight = zeros(12*nb_rb,num_refsig_frame,antnum);
% weight to rx
est_weighted =  zeros(12*nb_rb,num_refsig_frame,antnum);
for i = 1 : 12*nb_rb
    for j = 1 : num_refsig_frame
        h_abs(i,j) = sqrt(sum(abs(est(i,j,:)).^2,3));
        for k = 1 : antnum
            h_weight(i,j,k) = conj(est(i,j,k))/h_abs(i,j);
            est_weighted(i,j,k) = est(i,j,k).*h_weight(i,j,k);
        end
    end
end

