clear;
for i=1:4
    fconf = '../conf/conf_LTE_rb.json'; rxdir=['../rxdata/5.5/5.5.0/epoch' int2str(i-1) '/']
    %fconf = '../conf/conf_LTE_r.json'; rxdir=['../rxdata/4.30/4.30.0/epoch' int2str(i-1) '/']
    
    outfile = '../rxdata/log.html';
    outfigure = '../rxdata/log.jpg';

    if (exist('outfile')>0)
        diary(outfile);
        diary on;
        data_batch_handle;
        diary off;
    else
        data_batch_handle;
    end

end