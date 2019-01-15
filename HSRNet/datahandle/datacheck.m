clear all;
close all;

rxdir=['../rxdata/'];
fname = "../conf/conf2.json";
threshold = 0.01;
for fileidx=1:10
    hsr_rxdata  % rx_all_sig
    portnum = size(rx_all_sig,1);
    checklist=ones(1,portnum);
    for idx=1:portnum
        sig=rx_all_sig(idx,:);
        peak1=max([abs(real(sig)) abs(imag(sig))]);
        peak2=max([abs(real(sig-mean(sig))) abs(imag(sig-mean(sig)))]);
        if (peak1>0.9)
            checklist(idx)=-1;
        end
        if (peak2<threshold)
            checklist(idx)=0;
        end
    end
    display(checklist);
end