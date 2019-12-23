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
from sverchok.utils.logging import info, debug

def bmesh_from_pydata(verts=None, edges=None, faces=None, markup_face_data=False, normal_update=False):
    ''' verts is necessary, edges/faces are optional
        normal_update, will update verts/edges/faces normals at the end
    '''

    bm = bmesh.new()
    add_vert = bm.verts.new

    for co in verts:
        add_vert(co)

    bm.verts.index_update()
    bm.verts.ensure_lookup_table()

    if faces:
        add_face = bm.faces.new
        for face in faces:
            add_face(tuple(bm.verts[i] for i in face))

        bm.faces.index_update()

    if edges:
        add_edge = bm.edges.new
        for edge in edges:
            edge_seq = tuple(bm.verts[i] for i in edge)
            try:
                add_edge(edge_seq)
            except ValueError:
                # edge exists!
                pass

        bm.edges.index_update()

    if markup_face_data:
        bm.faces.ensure_lookup_table()
        layer = bm.faces.layers.int.new("initial_index")
        for idx, face in enumerate(bm.faces):
            face[layer] = idx

    if normal_update:
        bm.normal_update()
    return bm


def pydata_from_bmesh(bm, face_data=None):
    verts = [v.co[:] for v in bm.verts]
    edges = [[i.index for i in e.verts] for e in bm.edges]
    faces = [[i.index for i in p.verts] for p in bm.faces]
    if face_data is None:
        return verts, edges, faces
    else:
        face_data_out = face_data_from_bmesh_faces(bm, face_data)
        return verts, edges, faces, face_data_out

def face_data_from_bmesh_faces(bm, face_data):
    initial_index = bm.faces.layers.int.get("initial_index")
    if initial_index is None:
        raise Exception("bmesh has no initial_index layer")
    face_data_out = []
    n_face_data = len(face_data)
    for face in bm.faces:
        idx = face[initial_index]
        if idx < 0 or idx >= n_face_data:
            debug("Unexisting face_data[%s] [0 - %s]", idx, n_face_data)
            face_data_out.append(None)
        else:
            face_data_out.append(face_data[idx])
    return face_data_out

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


def bmesh_join(list_of_bmeshes, normal_update=False):
    """ takes as input a list of bm references and outputs a single merged bmesh

    allows an additional 'normal_update=True' (default False) to force normal calculations

    """

    bm = bmesh.new()
    add_vert = bm.verts.new
    add_face = bm.faces.new
    add_edge = bm.edges.new

    for bm_to_add in list_of_bmeshes:
        offset = len(bm.verts)

        for v in bm_to_add.verts:
            add_vert(v.co)

        bm.verts.index_update()
        bm.verts.ensure_lookup_table()

        if bm_to_add.faces:
            for face in bm_to_add.faces:
                add_face(tuple(bm.verts[i.index+offset] for i in face.verts))
            bm.faces.index_update()

        if bm_to_add.edges:
            for edge in bm_to_add.edges:
                edge_seq = tuple(bm.verts[i.index+offset] for i in edge.verts)
                try:
                    add_edge(edge_seq)
                except ValueError:
                    # edge exists!
                    pass
            bm.edges.index_update()

    if normal_update:
        bm.normal_update()

    return bm

def remove_doubles(vertices, edges, faces, d):
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=d)
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    v, e, p =pydata_from_bmesh(bm)
    bm.free()
    return v, e, p

def dual_mesh(bm, recalc_normals=True):
    # Make vertices of dual mesh by finding
    # centers of original mesh faces.
    new_verts = dict()
    for face in bm.faces:
        new_verts[face.index] = face.calc_center_median()

    #new_edges = []
    new_faces = []

    # For each vertex of original mesh,
    # find all connected faces and connect
    # corresponding vertices of the dual mesh
    # with a face.
    # The problem is, that the order of edges in
    # vert.link_edges (or faces in vert.link_faces)
    # is undefined, so we have to sort them somehow.
    for vert in bm.verts:
        if not vert.link_faces:
            continue
        face0 = vert.link_faces[0]
        new_face = [face0.index]
        other_faces = set(vert.link_faces[:])
        n = len(vert.link_faces)
        while other_faces:
            n = n-1
            if n <= 0:
                break
            for edge in vert.link_edges:
                if face0 in edge.link_faces:
                    fcs = [face for face in edge.link_faces if face != face0]
                    if not fcs:
                        continue
                    other_face = fcs[0]
                    if other_face in other_faces:
                        face0 = other_face
                        other_faces.remove(face0)
                        if face0.index not in new_face:
                            new_face.append(face0.index)

        if len(new_face) > 2:
            new_faces.append(new_face)

    vertices = [new_verts[idx] for idx in sorted(new_verts.keys())]
    # We cannot guarantee that our sorting above gave us faces
    # of original mesh in counterclockwise order each time.
    # So if we want normals of dual mesh to be consistent,
    # we have to call bmesh.ops.recalc_face_normals.
    if not recalc_normals:
        return vertices, new_faces
    else:
        bm2 = bmesh_from_pydata(vertices, [], new_faces, normal_update=True)
        bmesh.ops.recalc_face_normals(bm2, faces=bm2.faces)
        new_vertices, new_edges, new_faces = pydata_from_bmesh(bm2)
        bm2.free()
        return new_vertices, new_faces

def wave_markup_faces(bm, face_mask, neighbour_by_vert = True):
    """
    Given initial faces, markup all mesh faces by wave algorithm:
    initial faces get index of 1, their neighbours get index of 2, and so on.
    """
    if not isinstance(face_mask, (list, tuple)):
        raise TypeError("Face mask is specified incorrectly")

    index = bm.faces.layers.int.new("wave_front")
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    n_total = len(bm.faces)

    init_faces = [face for face, mask in zip(bm.faces[:], face_mask) if mask]
    if not init_faces:
        raise Exception("Initial faces set is empty")

    done = set(init_faces)
    wave_front = set(init_faces)
    step = 0
    while len(done) < n_total:
        step += 1
        new_wave_front = set()
        for face in wave_front:
            face[index] = step
        for face in wave_front:
            for edge in face.edges:
                for other_face in edge.link_faces:
                    if other_face == face:
                        continue
                    if other_face[index] == 0:
                        new_wave_front.add(other_face)
            if neighbour_by_vert:
                for vert in face.verts:
                    for other_face in vert.link_faces:
                        if other_face == face:
                            continue
                        if other_face[index] == 0:
                            new_wave_front.add(other_face)
        #debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    return [face[index] for face in bm.faces]

def wave_markup_verts(bm, vert_mask):
    """
    Given initial vertices, markup all mesh vertices by wave algorithm:
    initial vertices get index of 1, their neighbours get index of 2, and so on.
    """
    if not isinstance(vert_mask, (list, tuple)):
        raise TypeError("Verts mask is specified incorrectly")

    index = bm.verts.layers.int.new("wave_front")
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    n_total = len(bm.verts)

    init_verts = [vert for vert, mask in zip(bm.verts[:], vert_mask) if mask]
    if not init_verts:
        raise Exception("Initial vertices set is empty")

    done = set(init_verts)
    wave_front = set(init_verts)
    step = 0
    while len(done) < n_total:
        step += 1
        new_wave_front = set()
        for vert in wave_front:
            vert[index] = step
        for vert in wave_front:
            for edge in vert.link_edges:
                other_vert = edge.other_vert(vert)
                if other_vert[index] == 0:
                    new_wave_front.add(other_vert)
        #debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    return [vert[index] for vert in bm.verts]

