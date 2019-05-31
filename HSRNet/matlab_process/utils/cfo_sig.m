function sig = cfo_sig(cfo_freq, srate, length, ts)
%   input: cfo_freq, srate, length, ts
%   output: sig
    df = -cfo_freq;
    t=(0:length-1)/srate+ts/1e9; % second
    phase = 2*pi*df*t;
    sig = exp(1i*phase);
end

