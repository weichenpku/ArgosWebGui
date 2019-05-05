[33mcommit a6b528f7e4f7e91df024d8041b3def4c1f119171[m
Author: weichen <pkuweichen@gmail.com>
Date:   Sat May 4 21:01:59 2019 +0800

    5.4.3

[1mdiff --git a/HSRNet/matlab_process/batch_csi_calculate.m b/HSRNet/matlab_process/batch_csi_calculate.m[m
[1mindex 21f1069..54dbf60 100644[m
[1m--- a/HSRNet/matlab_process/batch_csi_calculate.m[m
[1m+++ b/HSRNet/matlab_process/batch_csi_calculate.m[m
[36m@@ -1,5 +1,5 @@[m
 clear;[m
[31m-for i=1:1[m
[32m+[m[32mfor i=4:4[m
     fconf = '../conf/conf_LTE_rb.json'; rxdir=['../rxdata/5.4/5.4.1/epoch' int2str(i-1) '/'][m
     %fconf = '../conf/conf_LTE_r.json'; rxdir=['../rxdata/4.30/4.30.0/epoch' int2str(i-1) '/'][m
     [m
[1mdiff --git a/HSRNet/matlab_process/csi/hsr_pss_cfo.m b/HSRNet/matlab_process/csi/hsr_pss_cfo.m[m
[1mindex 78995ef..66be3ec 100644[m
[1m--- a/HSRNet/matlab_process/csi/hsr_pss_cfo.m[m
[1m+++ b/HSRNet/matlab_process/csi/hsr_pss_cfo.m[m
[36m@@ -16,6 +16,8 @@[m [mfor cur_device = 1:portnum[m
     tmp_corr = conv(rx_all_sig(cur_device,:),conj(pss));[m
     [tmp_peak,tmp_idx]=max(abs(tmp_corr(cp_symbol_len+1:end-cp_symbol_len)));[m
     [m
[32m+[m[32m    frame_tone_len = frame_len + frame_len/10*2;[m
[32m+[m[32m    if (tmp_idx-frame_tone_len>0) tmp_idx = tmp_idx-frame_tone_len; end[m
     if (tmp_idx+frame_len-1>size(rx_all_sig,2))[m
         frame_broken = true;[m
         break;[m
[1mdiff --git a/HSRNet/matlab_process/csi/hsr_pss_cfo.m~ b/HSRNet/matlab_process/csi/hsr_pss_cfo.m~[m
[1mindex a262cf8..da87ed1 100644[m
[1m--- a/HSRNet/matlab_process/csi/hsr_pss_cfo.m~[m
[1m+++ b/HSRNet/matlab_process/csi/hsr_pss_cfo.m~[m
[36m@@ -1,7 +1,7 @@[m
 symbol_len = num_carriers;[m
 cp_len = symbol_len/4;[m
 cp_symbol_len = symbol_len+cp_len;[m
[31m-symbol_num = 6*10;  duration_time=0.005;[m
[32m+[m[32msymbol_num = 2*6*10;  duration_time=0.01;[m
 frame_len = cp_symbol_len*symbol_num;[m
 pss_t = [pss(end-cp_len+1:end) pss];[m
 [m
[36m@@ -16,14 +16,15 @@[m [mfor cur_device = 1:portnum[m
     tmp_corr = conv(rx_all_sig(cur_device,:),conj(pss));[m
     [tmp_peak,tmp_idx]=max(abs(tmp_corr(cp_symbol_len+1:end-cp_symbol_len)));[m
     [m
[31m-    if (tmp_idx+frame)[m
[31m-    rx_tmp = rx_all_sig(cur_device,1:end-frame_len);[m
[31m-    tmp_corr = conv(rx_tmp,conj(pss));[m
[31m-    [tmp_peak,tmp_idx]=max(abs(tmp_corr(cp_symbol_len+1:end-cp_symbol_len)));[m
[31m-    [m
[32m+[m[32m    frame_tone_len = frame_len + frame_len;[m
[32m+[m[32m    if (tmp_idx-frame_len)[m
[32m+[m[32m    if (tmp_idx+frame_len-1>size(rx_all_sig,2))[m
[32m+[m[32m        frame_broken = true;[m
[32m+[m[32m        break;[m
[32m+[m[32m    end[m
     offset_list(cur_device)=tmp_idx;[m
     [m
[31m-    rx_pss_t = rx_tmp(tmp_idx:tmp_idx+cp_symbol_len-1);[m
[32m+[m[32m    rx_pss_t = rx_all_sig(cur_device,tmp_idx:tmp_idx+cp_symbol_len-1);[m
     rx_pss_t = rx_pss_t - mean(rx_pss_t);[m
 [m
     %% first: IFO[m
[36m@@ -98,4 +99,10 @@[m [mfor cur_device = 1:portnum[m
     cfo=ifo+ffo_all_cp;[m
     cfo_list(fileidx,cur_device) = cfo;[m
 end[m
[32m+[m
[32m+[m[32mif (frame_broken == true)[m
[32m+[m[32m    for cur_device = 1:portnum[m[41m [m
[32m+[m[32m        checklist(fileidx,cur_device) = -2;[m
[32m+[m[32m    end[m
[32m+[m[32mend[m
 %display(cfo_list);[m
\ No newline at end of file[m
[1mdiff --git a/HSRNet/matlab_process/csiplot.m b/HSRNet/matlab_process/csiplot.m[m
[1mindex 121acab..294c0c1 100644[m
[1m--- a/HSRNet/matlab_process/csiplot.m[m
[1m+++ b/HSRNet/matlab_process/csiplot.m[m
[36m@@ -1,10 +1,10 @@[m
[31m-rxdir=['../rxdata/4.30/4.30.0/'];[m
[32m+[m[32mrxdir=['../rxdata/5.4/5.4.0/'];[m
 unwrap_able = 1;[m
 [m
 trial_check_list = [];[m
 trial_snr_list = [];[m
 trial_port_list = [];[m
[31m-for i=1:80[m
[32m+[m[32mfor i=1:1[m
     csifile = [rxdir 'epoch' int2str(i-1) '/csi.mat'];[m
     disp(csifile);[m
     load(csifile);[m
[1mdiff --git a/HSRNet/matlab_process/data_batch_handle.m b/HSRNet/matlab_process/data_batch_handle.m[m
[1mindex 84f69d0..e65e28f 100644[m
[1m--- a/HSRNet/matlab_process/data_batch_handle.m[m
[1m+++ b/HSRNet/matlab_process/data_batch_handle.m[m
[36m@@ -14,6 +14,7 @@[m [moffset_all_list = [];[m
 files = dir([rxdir 'rx*']);[m
 filenum = size(files,1);[m
 plot_device = 2;[m
[32m+[m[32msymbolnum = 120;[m
 refnum = symbolnum/2-1;[m
 for fileidx=1:filenum[m
     filename = [rxdir 'rx' int2str(fileidx) '.mat'];[m
[1mdiff --git a/HSRNet/matlab_process/datahandle.m b/HSRNet/matlab_process/datahandle.m[m
[1mindex 80ea3bf..b42dbf2 100644[m
[1m--- a/HSRNet/matlab_process/datahandle.m[m
[1m+++ b/HSRNet/matlab_process/datahandle.m[m
[36m@@ -6,6 +6,7 @@[m [mrfo_use = true;[m
 [m
 disp(filename);[m
 [rx_all_sig, device_num, refdir,device_list, sig_type] = hsr_rxdata(filename,fconf);          % ref_signal & rx_signal read[m
[32m+[m[32mfigure; plot(real(rx_all_sig(1,:)));[m
 load([refdir 'paras.mat']);[m
 pss = csvread([refdir 'pss.csv']);[m
 sig_f = csvread([refdir 'sig_f.csv']);[m
