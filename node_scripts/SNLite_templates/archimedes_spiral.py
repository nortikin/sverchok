"""
in vecs        v  d=[]   n=1
in split       s  d=[]   n=1
out ovecs       v
"""
from sverchok.data_structure import match_long_cycle

ovecs = []
if split:
    vecs, split = match_long_cycle([vecs,split])
    i = 0
    ovecs_ = []
    for v in vecs:
        i += 1
        if i == split[-1]-1:
            print(i,split[-1])
            i = 0
            split.pop()
            ovecs.append(ovecs_)
            ovecs_ = []
            print(len(ovecs_))
        ovecs_.append(v)
