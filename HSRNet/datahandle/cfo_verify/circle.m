p=linspace(1,10*pi,1000);
a1=6;
for a2=(0:16)
    s=a1*exp(1i*p)+exp(1+1i)*a2*exp(1i*-p);
    plot(s); title(['a2 = ' int2str(a2)]); axis(2*[-20 20 -20 20]);
end

% a1*e^(wt) + a2*e^(-wt)  => a1+a2 : a1-a2