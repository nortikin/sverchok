# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0301

import bmesh
from mathutils import Matrix, Vector

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.utils.modules.geom_cricket import cricket



def create_cricket(as_pydata=False, scale=4.0):

    bm = bmesh_from_pydata(cricket['vert_list'], [], cricket['face_list'])
    bmesh.ops.mirror(bm, geom=(bm.verts[:] + bm.faces[:]), matrix=Matrix(), merge_dist=0.0, axis='X')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.scale(bm, vec=Vector((scale, scale, scale)), verts=bm.verts[:])

    if as_pydata:
        verts, edges, faces = pydata_from_bmesh(bm)
        bm.free()
        return verts, edges, faces

    return bm

