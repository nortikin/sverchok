"""
in   verts  v          .=[]   n=0
in   x_tapper  s       .=0.0  n=1
in   y_tapper  s       .=0.0  n=1
in   z_tapper  s       .=0.0  n=1
in   scale_tapper  s   .=1.0  n=1
out  overts   v
"""
#A homography transform is a plane-preserving and straight-line preserving matrix transform that produces a perspective effect.
#Normally this is used to generate 2D perspective views, but the 3D transform works too.
# (text from https://github.com/nortikin/sverchok/issues/3518)
# example at https://user-images.githubusercontent.com/10011941/99096524-a49e5100-25d6-11eb-84ea-476575c64282.png

from mathutils import Matrix
from sverchok.data_structure import (
                            zip_long_repeat as zlp,
                            ensure_nesting_level as enl)
import numpy as np

if verts:
    overts = []

    for vs, xt, yt, zt, st in zlp(verts,
                                enl(x_tapper,1),
                                enl(y_tapper,1),
                                enl(z_tapper,1),
                                enl(scale_tapper,1)):
        mat=np.array(Matrix())
        mat[3, 0] = xt
        mat[3, 1] = yt
        mat[3, 2] = zt
        mat[3, 3] = st

        np_verts = np.array(vs)
        np_verts_4d = np.ones((np_verts.shape[0],4))
        np_verts_4d[:, :3] = np_verts

        v_out = mat.dot(np_verts_4d.T)

        sc = v_out[3,:]
        overts.append((v_out[:3,:].T)/sc[:,np.newaxis])
