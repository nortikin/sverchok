"""
in   verts_in    v   .=[]   n=0
in   function    s   .=0    n=2
in   smooth      s   .=0.0  n=2
in   number      s   .=25   n=2
in   epsilon     s   .=1.0  n=2
out  verts_out   v
"""

sp = False
try:
    __import__('imp').find_module('scipy')
    sp = True
except ImportError:
    pass

chFunc = ['multiquadric', 'inverse', \
    'gaussian', 'linear', 
    'cubic', 'quintic', 
    'thin_plate'] 
#'multiquadric', \ #: sqrt((r/self.epsilon)**2 + 1)
#'inverse', \ #: 1.0/sqrt((r/self.epsilon)**2 + 1)
#'gaussian', \ #: exp(-(r/self.epsilon)**2)
#'linear',\ #: r
#    'cubic',\ #: r**3
#    'quintic',\ #: r**5
#    'thin_plate'] #: r**2 * log(r)
function = max(min(6,function),0)

import numpy as np
if sp:
    GRID_POINTS = number
    XYZ = np.array(verts_in[0])
    x_min = XYZ[:,0].min()
    x_max = XYZ[:,0].max()
    y_min = XYZ[:,1].min()
    y_max = XYZ[:,1].max()
    xi = np.linspace(x_min, x_max, GRID_POINTS)
    yi = np.linspace(y_min, y_max, GRID_POINTS)
    XI, YI = np.meshgrid(xi, yi)

    from scipy.interpolate import Rbf
    rbf = Rbf(XYZ[:,0],XYZ[:,1],XYZ[:,2],function=chFunc[function],smooth=smooth,epsilon=epsilon)
    ZI = rbf(XI,YI)

    verts_out = np.dstack((XI,YI,ZI)).tolist()
else:
    verts_out = verts_in