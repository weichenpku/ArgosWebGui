clear;
load('iqbalance.mat');
s=who;

filename='iqbalance.json';
fd=fopen(filename,'w');
fprintf(fd,'{\n');

num=size(s,1);
for i=1:num
    fprintf(fd,'"%s":"%f",\n',s{i},eval(s{i}));
end
fprintf(fd,'}\n');


fclose(fd);