"""
in in_points v
in in_faces s
out out_verts v
out out_faces s
"""

import numpy as np
from sverchok.data_structure import zip_long_repeat

out_verts = []

for verts, faces in zip_long_repeat(in_points, in_faces):
    verts = np.array(verts)
    faces = np.array(faces)
    tris = verts[faces]
    v1s = tris[:,1] - tris[:,0]
    v2s = tris[:,2] - tris[:,1]
    normals = np.cross(v1s, v2s)

    out_verts.append(normals.tolist())
    


