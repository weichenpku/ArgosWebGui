f=1920000;
p=2*pi*f*linspace(0,1,f);
p0=pi/6;
df=100;
delta_p=2*pi*df*linspace(0,1,f);
a1=6;


for a2=(0:16)
    s1=a1*exp(1i*p)+a2*exp(1i*-p);
    s2=exp(1i*p0)*s1;
    s3=s2.*exp(1i*delta_p);
    s4=1*real(s3)+2*1i*imag(s3);
    s5=s4*exp(1i*p0);
    plot(s3); title(['a2 = ' int2str(a2)]); axis(2*[-20 20 -20 20]);
end

% a1*e^(wt) + a2*e^(-wt)  => a1+a2 : a1-a2