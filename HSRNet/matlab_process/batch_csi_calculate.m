for i=1:80
    rxdir=['../rxdata/4.30/4.30.0/epoch' int2str(i-1) '/']
    
    fconf = '../conf/conf_LTE.json'; 

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