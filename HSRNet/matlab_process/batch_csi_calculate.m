clear;
for epoch_num=1:1
    fconf = '../conf/conf_LTE_rb.json'; rxdir=['../rxdata/5.5/5.5.3/epoch' int2str(epoch_num-1) '/']; cfo_force = 260;
    %fconf = '../conf/conf_LTE_r.json'; rxdir=['../rxdata/4.30/4.30.0/epoch' int2str(epoch_num-1) '/']
    
    outdir = '../rxdata/';
    
    outfile = [outdir 'log.html'];
    if (exist('outfile')>0)
        diary(outfile);
        diary on;
        data_batch_handle;
        diary off;
    else
        data_batch_handle;
    end

end