"""
in   verts  v   .=[]   n=0
in   faces  s   .=[]   n=0
out  overts   v
out  ofaces   s
"""

from mathutils.geometry import interpolate_bezier as bezlerp
from mathutils import Vector, Euler
import numpy as np

Verts = []
Edges = []

for ov, of in zip(verts, faces):
    lv = len(ov)
    overts_ = ov
    ofaces_ = []
    fcs = []
    for f in of:
        vrts = [ov[i] for i in f]
        nv  = np.array(vrts)
        vrt  = nv.sum(axis=0)/len(f)
        fcs = [[i,k,lv] for i,k in zip(f,f[-1:]+f[:-1])]
        overts_.append(vrt.tolist())
        ofaces_.extend(fcs)
        lv += 1
    overts.append(overts_)
    ofaces.append(ofaces_)
