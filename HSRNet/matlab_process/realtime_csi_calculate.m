function [] = realtime_csiplot(rxdir,fconf)
%REALTIME_CSIPLOT Summary of this function goes here
%   Detailed explanation goes here
 
%rxdir=['../rxdata/4.25/4.25.3/epoch0/'];
%fconf = '../conf/conf_LTE.json';
outdir = '../rxdata/';
cfo_force = 260;

outfile = [outdir 'log.html'];
diary(outfile);
diary on;

data_batch_handle;

diary off;
%end

