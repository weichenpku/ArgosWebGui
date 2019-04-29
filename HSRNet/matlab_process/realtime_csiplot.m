%function [] = realtime_csiplot(rxdir,fname)
%REALTIME_CSIPLOT Summary of this function goes here
%   Detailed explanation goes here
 
rxdir=['../rxdata/4.25/4.25.3/epoch0/'];
fconf = '../conf/conf_LTE.json';
outfile = '../rxdata/log.txt';
outfigure = '../rxdata/log.jpg';

diary(outfile);
diary on;

data_batch_handle;

diary off;
%end

