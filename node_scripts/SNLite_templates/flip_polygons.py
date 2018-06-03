"""
in   pols    s   .=[[]]   n=0
in   U     s   .=1    n=2
out  pols_out   s
"""

import numpy as np
from numpy import array as ar

if pols:
    po = ar(pols)
    sha = np.shape(po)
    sh = [sha[0],U,int(sha[1]/U),sha[2]]
    pols_after = np.reshape(po,sh)
    pols_out = np.reshape(pols_after.transpose(0,2,1,3),sha).tolist()
else:
    pols_out = [[None]]