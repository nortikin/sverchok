# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bmesh
from sverchok.data_structure import iterate_process


def bmesh_from_pydata(verts=[], edges=[], faces=[]):
    ''' verts is necessary, edges/faces are optional '''

    bm = bmesh.new()
    add_vert = bm.verts.new

    bm_verts = [add_vert(co) for co in verts]
    bm.verts.index_update()

    if faces:
        add_face = bm.faces.new
        for face in faces:
            add_face([bm_verts[i] for i in face])
        bm.faces.index_update()

    if edges:
        add_edge = bm.edges.new
        for edge in edges:
            edge_seq = bm_verts[edge[0]], bm_verts[edge[1]]
            try:
                add_edge(edge_seq)
            except ValueError:
                # edge exists!
                pass
        bm.edges.index_update()

    return bm


def pydata_from_bmesh(bm):
    v = [v.co[:] for v in bm.verts]
    e = [[i.index for i in e.verts] for e in bm.edges[:]]
    p = [[i.index for i in p.verts] for p in bm.faces[:]]
    return v, e, p

def with_bmesh(method):
    '''Decorator for methods which can work with BMesh.
    Usage:
        @with_bmesh
        def do_something(self, bm, other_args):
            ...
            return new_bmesh, other_results

        This will be transformed to method like

        def do_something(self, verts, edges, faces, other_args):
            bm = bmesh_from_pydata(..)
            ...
            return pydata_from_bmesh(bm), other_results
    '''

    def real_process(*args):
        if len(args) == 2 and isinstance(args[1], bmesh.types.BMesh):
            bm = args[1]
            other_args = []
        elif len(args) >= 4 and all([isinstance(arg, list) for arg in args[1:4]]):
            bm = bmesh_from_pydata(*args[1:4])
            other_args = args[4:]
        else:
            raise TypeError("{} must be called with one BMesh or with at least 3 lists (verts, edges, faces); but called with {}".format(method.__name__, list(map(type, args))))

        method_result = method(args[0], bm, *other_args)
        if method_result is None:
            return None
        elif isinstance(method_result, bmesh.types.BMesh):
            result = pydata_from_bmesh(method_result)
        elif isinstance(method_result, (list,tuple)) and len(method_result) >= 1 and isinstance(method_result[0], bmesh.types.BMesh):
            result_bmesh = pydata_from_bmesh(method_result[0])
            result_other = method_result[1:]
            result = list(result_bmesh) + list(result_other)
            if isinstance(method_result, tuple):
                result = tuple(result)
        else:
            raise ValueError("{} returned unexpected type of result: {}".format(method.__name__, type(method_result)))
        bm.free()

        return result

    real_process.__name__ = method.__name__
    real_process.__doc__ = method.__doc__
    return real_process

