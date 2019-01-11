function [errnum] = ofdm_judge(vec1,vec2,modulate,num)
%OFDM_JUDGE Summary of this function goes here
%   Detailed explanation goes here
errnum = 0;
if modulate=='QAM'
    for idx=1:num
        if sign(real(vec1(idx)))~=sign(real(vec2(idx)))
            errnum=errnum+1;
            continue;
        end
        if sign(imag(vec1(idx)))~=sign(imag(vec2(idx)))
            errnum=errnum+1;
            continue;
        end
    end
end

end

