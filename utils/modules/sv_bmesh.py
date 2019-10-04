# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bmesh
from mathutils import Matrix

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def create_cricket(bm):


    bm = bmesh_from_pydata(vert_list, [], face_list)
    bmesh.ops.mirror(bm, geom=(bm.verts[:] + bm.faces[:]), matrix=Matrix(), merge_dist=0.0, axis='X')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])




# use these interfaces options.

ops = lambda: None
ops.create_cricket = lambda bm: create_cricket(bm)