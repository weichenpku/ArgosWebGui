clear;
for epoch_num=3:5
    %fconf = '../conf/conf_LTE_2.5m.json'; rxdir=['../rxdata/5.5/5.5.1/epoch' int2str(epoch_num-1) '/']; cfo_force = 260;
    %fconf = '../conf/conf_LTE_r.json'; rxdir=['../rxdata/4.30/4.30.0/epoch' int2str(epoch_num-1) '/']
    %fconf = '../conf/conf_LTE_30m.json'; rxdir=['../rxdata/5.11/5.11.0/epoch' int2str(epoch_num-1) '/']; cfo_force = 260;
    fconf = '../conf/conf_LTE_streaming_30m.json'; rxdir=['../rxdata/5.16/5.16.3/epoch' int2str(epoch_num-1) '/']; cfo_force = 260;
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
