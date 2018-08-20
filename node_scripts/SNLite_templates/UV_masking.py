"""
in   pols    s   .=[]   n=0
in   U_mask     s   .=[]    n=0
in   V_mask     s   .=[]    n=0
out  pols_True    s
out  pols_False   s
out  mask   s
"""
# it makes filter ranges of 0 and 1 chains.
# input U is i.e. [[2,10,40,4]]
# will make mask of two 1, ten 0, fourty 1, four 0
# input V is [[3,3]]
# two masks will U or V make third mask
# output will divide UV masked polygons

if not U_mask: U_mask = [[1]]
if not V_mask: V_mask = [[1]]
if not pols: pols = [[[0,1,2]]]
U_ = []
V_ = []
mask = []
tmblr = False
pols_True = pols.copy()
pols_False = [[]]
for i in U_mask[0]:
    U_.extend([tmblr for k in range(i)])
    tmblr = not tmblr
tmblr = False
for j in V_mask[0]:
    V_.extend([tmblr for k in range(j)])
    tmblr = not tmblr
z = 0
l = len(pols[0])
for q in U_:
    for w in V_:
        t = q and w
        z += 1
        mask.append(t)
        if t:
            pols_False[0].append(pols_True[0].pop(l-z))