function [num_symbols_frame,refnum,refidx,blanknum,blankidx] = ref_blank_idx(sig_type,nb_rb)

if (strcmp(sig_type,'brrr') && nb_rb==150) 
    num_symbols_frame = 15;
    refnum = 11;
    refidx = [2:4 6:8 10:12 14:15];
    blanknum = 3;
    blankidx = [5,9,13];
end

if (strcmp(sig_type,'br') && nb_rb==15)
    num_symbols_frame = 120;
    refnum = 60;
    refidx = (2:2:120);
    blanknum = 59;
    blankidx = (3:2:120);
end

if (strcmp(sig_type,'rb') && nb_rb==15)
    num_symbols_frame = 120;
    refnum = 59;
    refidx = (3:2:120);
    blanknum = 60;
    blankidx = (2:2:120);
end

assert(num_symbols_frame == refnum+blanknum+1);
assert(refnum==size(refidx,2));
assert(blanknum==size(blankidx,2));

end

