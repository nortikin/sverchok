# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0301
import ast
from pathlib import Path

import bmesh
from mathutils import Matrix, Vector

from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh


def load_from_geom_modules(filename):

    current_dir = Path(__file__).parent.absolute()
    filepath = str(current_dir / filename)
    try:
        with open(filepath, 'r', encoding='ISO-8859-15') as fileobject:
            return ast.literal_eval(''.join(fileobject.readlines()))
    except Exception as err:
        print('load_from_geom_modules failed..', filepath)
        print(err)
    return {}


base_mesh_dict = {}
base_mesh_dict['cricket'] = load_from_geom_modules("geom_cricket.json")


def create_cricket(as_pydata=False, scale=4.0):

    cricket = base_mesh_dict.get('cricket')

    bm = bmesh_from_pydata(cricket['vert_list'], [], cricket['face_list'])
    bmesh.ops.mirror(bm, geom=(bm.verts[:] + bm.faces[:]), matrix=Matrix(), merge_dist=0.0, axis='X')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bmesh.ops.scale(bm, vec=Vector((scale, -scale, scale)), verts=bm.verts[:])

    if as_pydata:
        verts, edges, faces = pydata_from_bmesh(bm)
        bm.free()
        return verts, edges, faces

    return bm

