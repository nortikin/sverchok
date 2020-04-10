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
from bmesh.types import BMVert, BMEdge, BMFace
import mathutils
import numpy as np
import math

from sverchok.utils.logging import info, debug

def bmesh_from_pydata(verts=None, edges=[], faces=[], markup_face_data=False, markup_edge_data=False, markup_vert_data=False, normal_update=False):
    ''' verts is necessary, edges/faces are optional
        normal_update, will update verts/edges/faces normals at the end
    '''

    bm = bmesh.new()
    bm_verts = bm.verts
    add_vert = bm_verts.new

    py_verts = verts.tolist() if type(verts) == np.ndarray else verts

    for co in py_verts:
        add_vert(co)

    bm_verts.index_update()
    bm_verts.ensure_lookup_table()

    if len(faces) > 0:
        add_face = bm.faces.new
        py_faces = faces.tolist() if type(faces) == np.ndarray else faces
        for face in py_faces:
            add_face(tuple(bm_verts[i] for i in face))

        bm.faces.index_update()

    if len(edges) > 0:
        if markup_edge_data:
            initial_index_layer = bm.edges.layers.int.new("initial_index")

        add_edge = bm.edges.new
        get_edge = bm.edges.get
        py_faces = edges.tolist() if type(edges) == np.ndarray else edges
        for idx, edge in enumerate(edges):
            edge_seq = tuple(bm_verts[i] for i in edge)
            bm_edge = get_edge(edge_seq)
            if not bm_edge:
                bm_edge = add_edge(edge_seq)
            if markup_edge_data:
                bm_edge[initial_index_layer] = idx

        bm.edges.index_update()

    if markup_vert_data:
        bm_verts.ensure_lookup_table()
        layer = bm_verts.layers.int.new("initial_index")
        for idx, vert in enumerate(bm_verts):
            vert[layer] = idx

    if markup_face_data:
        bm.faces.ensure_lookup_table()
        layer = bm.faces.layers.int.new("initial_index")
        for idx, face in enumerate(bm.faces):
            face[layer] = idx

    if normal_update:
        bm.normal_update()
    return bm

def numpy_data_from_bmesh(bm, out_np, face_data=None):
    if out_np[0]:
        verts = np.array([v.co[:] for v in bm.verts])
    else:
        verts = [v.co[:] for v in bm.verts]
    if out_np[1]:
        edges = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
    else:
        edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
    if out_np[2]:
        faces = np.array([[i.index for i in p.verts] for p in bm.faces])
    else:
        faces = [[i.index for i in p.verts] for p in bm.faces]

    if face_data:
        if out_np[3]:
            face_data_out = np.array(face_data_from_bmesh_faces(bm, face_data))
        else:
            face_data_out = face_data_from_bmesh_faces(bm, face_data)
            return verts, edges, faces, face_data_out
    else:
        return verts, edges, faces, []

def pydata_from_bmesh(bm, face_data=None):

    verts = [v.co[:] for v in bm.verts]
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
    faces = [[i.index for i in p.verts] for p in bm.faces]

    if face_data is None:
        return verts, edges, faces
    else:
        face_data_out = face_data_from_bmesh_faces(bm, face_data)
        return verts, edges, faces, face_data_out

def get_partial_result_pydata(self, geom):
    '''used by the subdivide node to get new and old verts/edges/pols'''

    new_verts = [v for v in geom if isinstance(v, BMVert)]
    new_edges = [e for e in geom if isinstance(e, BMEdge)]
    new_faces = [f for f in geom if isinstance(f, BMFace)]

    new_verts = [tuple(v.co) for v in new_verts]
    new_edges = [[edge.verts[0].index, edge.verts[1].index] for edge in new_edges]
    new_faces = [[v.index for v in face.verts] for face in new_faces]

    return new_verts, new_edges, new_faces

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

def edge_data_from_bmesh_edges(bm, edge_data):
    initial_index = bm.edges.layers.int.get("initial_index")
    if initial_index is None:
        raise Exception("bmesh has no initial_index layer")
    edge_data_out = []
    n_edge_data = len(edge_data)
    for edge in bm.edges:
        idx = edge[initial_index]
        if idx < 0 or idx >= n_edge_data:
            debug("Unexisting edge_data[%s] [0 - %s]", idx, n_edge_data)
            edge_data_out.append(None)
        else:
            edge_data_out.append(edge_data[idx])
    return edge_data_out

def vert_data_from_bmesh_verts(bm, vert_data):
    initial_index = bm.verts.layers.int.get("initial_index")
    if initial_index is None:
        raise Exception("bmesh has no initial_index layer")
    vert_data_out = []
    n_vert_data = len(vert_data)
    for vert in bm.verts:
        idx = vert[initial_index]
        if idx < 0 or idx >= n_vert_data:
            debug("Unexisting vert_data[%s] [0 - %s]", idx, n_vert_data)
            vert_data_out.append(None)
        else:
            vert_data_out.append(vert_data[idx])
    return vert_data_out

def bmesh_edges_from_edge_mask(bm, edge_mask):
    initial_index = bm.edges.layers.int.get("initial_index")
    if initial_index is None:
        raise Exception("bmesh has no initial_index layer")
    bm_edges = []
    n_edge_mask = len(edge_mask)
    for bm_edge in bm.edges:
        idx = bm_edge[initial_index]
        if idx < 0 or idx >= n_edge_mask:
            debug("Unexisting edge_mask[%s] [0 - %s]", idx, n_edge_mask)
        else:
            mask = edge_mask[idx]
            if mask:
                bm_edges.append(bm_edge)
    return bm_edges

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

def remove_doubles(vertices, edges, faces, d, face_data=None, vert_data=None):
    """
    This is a wrapper for bmesh.ops.remove_doubles.

    vertices, edges, faces: standard sverchok formatted description of the mesh.
    d: the threshold for the merge procedure.
    face_data: arbitrary data per mesh face.
    vert_data: arbitrary data per mesh vertex.

    output:
        if face_data or vert_data was specified, this outputs 4-tuple:
            * vertices
            * edges
            * faces
            * data: a dictionary with following keys:
                * 'vert_init_index': indexes of the output vertices in the original mesh
                * 'face_init_index': indexes of the output faces in the original mesh
                * 'faces': correctly reordered face_data (if present)
                * 'verts': correclty reordered vert_data (if present)
    """
    has_face_data = bool(face_data)
    has_vert_data = bool(vert_data)
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True, markup_face_data = True, markup_vert_data = True)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=d)
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    verts, edges, faces = pydata_from_bmesh(bm)
    if has_face_data or has_vert_data:
        data = dict()
        vert_layer = bm.verts.layers.int.get("initial_index")
        face_layer = bm.faces.layers.int.get("initial_index")
        if vert_layer:
            data['vert_init_index'] = [vert[vert_layer] for vert in bm.verts]
        if face_layer:
            data['face_init_index'] = [face[face_layer] for face in bm.faces]
        if has_face_data:
            data['faces'] = face_data_from_bmesh_faces(bm, face_data)
        if has_vert_data:
            data['verts'] = vert_data_from_bmesh_verts(bm, vert_data)
        bm.free()
        return verts, edges, faces, data
    else:
        bm.free()
        return verts, edges, faces

def dual_mesh(bm, recalc_normals=True):
    # Make vertices of dual mesh by finding
    # centers of original mesh faces.
    new_verts = dict()
    for face in bm.faces:
        new_verts[face.index] = face.calc_center_median()

    new_faces = []

    def calc_angle(co, orth, co_orth, face_idx):
        face_center = new_verts[face_idx]
        direction = face_center - co
        dx = direction.dot(orth)
        dy = direction.dot(co_orth)
        return math.atan2(dy, dx)

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
        normal = vert.normal
        orth = normal.orthogonal()
        co_orth = normal.cross(orth)
        face_idxs = [face.index for face in vert.link_faces]
        new_face = sorted(face_idxs, key = lambda idx : calc_angle(vert.co, orth, co_orth, idx))
        new_face = list(new_face)

        m = len(new_face)
        if m > 2:
            new_faces.append(new_face)

    vertices = [new_verts[idx] for idx in sorted(new_verts.keys())]
    return vertices, new_faces

def diamond_mesh(bm):
    new_bm = bmesh.new()
    copied_verts = dict()
    for vert in bm.verts:
        co = vert.co
        copied_verts[vert.index] = new_bm.verts.new(co)

    # Make vertices of dual mesh by finding
    # centers of original mesh faces.
    center_verts = dict()
    for face in bm.faces:
        co = face.calc_center_median()
        center_verts[face.index] = new_bm.verts.new(co)

    for edge in bm.edges:
        edge_faces = edge.link_faces
        n_faces = len(edge_faces)
        if not n_faces:
            continue
        if n_faces > 2:
            continue
        if n_faces == 1:
            face = edge_faces[0]
            ev1, ev2 = edge.verts
            face_verts = copied_verts[ev1.index], copied_verts[ev2.index], center_verts[face.index]
            new_normal = mathutils.geometry.normal(*[vert.co for vert in face_verts])
            old_normal = face.normal
            if new_normal.dot(old_normal) < 0:
                face_verts = list(reversed(face_verts))
            new_bm.faces.new(face_verts)
        else: # n_faces == 2
            face1, face2 = edge_faces
            ev1, ev2 = edge.verts
            face_verts = copied_verts[ev1.index], center_verts[face1.index], copied_verts[ev2.index], center_verts[face2.index]
            new_normal = mathutils.geometry.normal(*[vert.co for vert in face_verts])
            old_normal = face1.normal + face2.normal
            if new_normal.dot(old_normal) < 0:
                face_verts = list(reversed(face_verts))
            new_bm.faces.new(face_verts)
    new_bm.verts.index_update()
    new_bm.edges.index_update()
    new_bm.faces.index_update()

    return new_bm

def truncate_vertices(bm):

    def calc_angle(co, orth, co_orth, vert):
        direction = vert.co - co
        dx = direction.dot(orth)
        dy = direction.dot(co_orth)
        return math.atan2(dy, dx)

    new_bm = bmesh.new()
    edge_centers = dict()
    for edge in bm.edges:
        center_co = (edge.verts[0].co + edge.verts[1].co) / 2.0
        edge_centers[edge.index] = new_bm.verts.new(center_co)
    for face in bm.faces:
        new_face = [edge_centers[edge.index] for edge in face.edges]
        old_normal = face.normal
        new_normal = mathutils.geometry.normal(*[vert.co for vert in new_face])
        if new_normal.dot(old_normal) < 0:
            new_face = list(reversed(new_face))
        new_bm.faces.new(new_face)
    for vertex in bm.verts:
        new_face = [edge_centers[edge.index] for edge in vertex.link_edges]
        if len(new_face) > 2:
            old_normal = vertex.normal
            orth = old_normal.orthogonal()
            co_orth = old_normal.cross(orth)
            new_face = sorted(new_face, key = lambda edge_center : calc_angle(vertex.co, orth, co_orth, edge_center))
            new_face = list(new_face)
            new_bm.faces.new(new_face)

    new_bm.verts.index_update()
    new_bm.edges.index_update()
    new_bm.faces.index_update()

    return new_bm

def get_neighbour_faces(face, by_vert = True):
    """
    Get neighbour faces of the given face.

    face : BMFace
    by_vert: True if by "neighbour" you mean having any common vertex;
             or False, if by "neighbour" you mean having any common edge.

    result: set of BMFace.
    """
    result = set()
    if by_vert:
        for vert in face.verts:
            for other_face in vert.link_faces:
                if other_face == face:
                    continue
                result.add(other_face)
    else:
        for edge in face.edges:
            for other_face in edge.link_faces:
                if other_face == face:
                    continue
                result.add(other_face)
    return result

def get_neighbour_verts(vert, by_edge = True):
    """
    Get neighbour vertices of the given vertex.

    vert : BMVert
    returns: set of BMVert.
    """
    result = set()
    if by_edge:
        for edge in vert.link_edges:
            other_vert = edge.other_vert(vert)
            result.add(other_vert)
    else:
        for face in vert.link_faces:
            for other_vert in face.verts:
                if other_vert == vert:
                    continue
                result.add(other_vert)
    return result

def fill_faces_layer(bm, face_mask, layer_name, layer_type, value, invert_mask = False):
    if layer_type == int:
        layers = bm.faces.layers.int
    elif layer_type == float:
        layers = bm.faces.layers.float
    elif layer_type == str:
        layers = bm.faces.layers.str
    else:
        raise Exception("Unsupported layer data type")

    if not isinstance(value, layer_type):
        raise TypeError("Value type does not correspond to layer data type")

    layer = layers.get(layer_name)
    if layer is None:
        raise Exception("Specified layer does not exist")

    for face, mask in zip(bm.faces, face_mask):
        if mask != invert_mask:
            face[layer] = value

def fill_verts_layer(bm, vert_mask, layer_name, layer_type, value, invert_mask = False):
    if layer_type == int:
        layers = bm.verts.layers.int
    elif layer_type == float:
        layers = bm.verts.layers.float
    elif layer_type == str:
        layers = bm.verts.layers.str
    else:
        raise Exception("Unsupported layer data type")

    if not isinstance(value, layer_type):
        raise TypeError("Value type does not correspond to layer data type")

    layer = layers.get(layer_name)
    if layer is None:
        raise Exception("Specified layer does not exist")

    for vert, mask in zip(bm.verts, vert_mask):
        if mask != invert_mask:
            vert[layer] = value

def wave_markup_faces(bm, init_face_mask, neighbour_by_vert = True, find_shortest_path = False):
    """
    Given initial faces, markup all mesh faces by wave algorithm:
    initial faces get index of 1, their neighbours get index of 2, and so on.

    bm : BMesh
    init_face_mask : Mask for faces to start from.
    neighbour_by_vert : True if by "neighbour" you mean having any common vertex;
             or False, if by "neighbour" you mean having any common edge.
    find_shortest_path : if set to True, markup enough information to trace the shortest
            path from each face of the mesh to the initially selected faces.

    result : Distance from initial faces, in steps, for each face of the mesh.

    This uses the following custom data layers on mesh faces:

    * wave_front : int, output; the distance from initially selected faces (starting with 1
      for initially selected faces).
    * wave_start_index : int, output; the index of the initial face to which this face is nearest.
      Filled only if find_shortest_path is set to True.
    * wave_path_prev_index : int, output; the index of the face, to which you
      should step to follow the shortest path to initial faces. Filled only if
      find_shortest_path is set to True.
    * wave_path_prev_distance : float, output; the euclidian distance to the
      face mentioned in wave_path_prev_index. Filled only if find_shortest_path
      is set to True.
    * wave_path_distance: float, output; total length of the shortest to the
      init faces area (sum of all wave_path_prev_distance along that path).
      Filled only if find_shortest_path is set to True.
    * wave_obstacle : int, input, optional; set to non-zero value to indicate
      that this face is an obstacle (wave can not pass through it).

    """
    if not isinstance(init_face_mask, (list, tuple)):
        raise TypeError("Face mask is specified incorrectly")

    index = bm.faces.layers.int.new("wave_front")
    if find_shortest_path:
        init_index = bm.faces.layers.int.new("wave_start_index")
        path_prev_index = bm.faces.layers.int.new("wave_path_prev_index")
        path_prev_distance = bm.faces.layers.float.new("wave_path_prev_distance")
        path_distance = bm.faces.layers.float.new("wave_path_distance")
    obstacles = bm.faces.layers.int.get("wave_obstacle")
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    if obstacles is None:
        n_total = len(bm.faces)
    else:
        n_total = len([face for face in bm.faces if face[obstacles] == 0])

    if find_shortest_path:
        face_center = dict([(face.index, face.calc_center_median()) for face in bm.faces])
    else:
        face_center = None

    init_faces = [face for face, mask in zip(bm.faces[:], init_face_mask) if mask]
    if not init_faces:
        raise Exception("Initial faces set is empty")

    def is_obstacle(face):
        if obstacles is None:
            return False
        else:
            return face[obstacles]

    done = set(init_faces)
    wave_front = set(init_faces)
    step = 0
    if find_shortest_path:
        for face in init_faces:
            face[init_index] = face.index
    while len(done) < n_total:
        step += 1
        new_wave_front = set()
        for face in wave_front:
            face[index] = step
        for face in wave_front:
            if find_shortest_path:
                this_center = face_center[face.index]
            for other_face in get_neighbour_faces(face, neighbour_by_vert):
                if is_obstacle(other_face):
                    continue
                if other_face[index] == 0:
                    new_wave_front.add(other_face)
                    if find_shortest_path:
                        other_center = face_center[other_face.index]
                        distance = (this_center - other_center).length
                        new_distance = face[path_distance] + distance
                        prev_distance = other_face[path_distance]
                        if prev_distance == 0 or prev_distance > new_distance:
                            other_face[path_prev_distance] = distance
                            other_face[path_distance] = new_distance
                            other_face[path_prev_index] = face.index
                            other_face[init_index] = face[init_index]
        #debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    return [face[index] for face in bm.faces]

def wave_markup_verts(bm, init_vert_mask, neighbour_by_edge = True, find_shortest_path = False):
    """
    Given initial vertices, markup all mesh vertices by wave algorithm:
    initial vertices get index of 1, their neighbours get index of 2, and so on.
    """
    if not isinstance(init_vert_mask, (list, tuple)):
        raise TypeError("Verts mask is specified incorrectly")

    index = bm.verts.layers.int.new("wave_front")
    if find_shortest_path:
        init_index = bm.verts.layers.int.new("wave_start_index")
        path_prev_index = bm.verts.layers.int.new("wave_path_prev_index")
        path_prev_distance = bm.verts.layers.float.new("wave_path_prev_distance")
        path_distance = bm.verts.layers.float.new("wave_path_distance")
    obstacles = bm.verts.layers.int.get("wave_obstacle")
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    if obstacles is None:
        n_total = len(bm.verts)
    else:
        n_total = len([vert for vert in bm.verts if vert[obstacles] == 0])

    init_verts = [vert for vert, mask in zip(bm.verts[:], init_vert_mask) if mask]
    if not init_verts:
        raise Exception("Initial vertices set is empty")

    def is_obstacle(vert):
        if obstacles is None:
            return False
        else:
            return vert[obstacles]

    done = set(init_verts)
    wave_front = set(init_verts)
    step = 0
    if find_shortest_path:
        for vert in init_verts:
            vert[init_index] = vert.index
    while len(done) < n_total:
        step += 1
        new_wave_front = set()
        for vert in wave_front:
            vert[index] = step
        for vert in wave_front:
            for other_vert in get_neighbour_verts(vert, neighbour_by_edge):
                if is_obstacle(other_vert):
                    continue
                if other_vert[index] == 0:
                    new_wave_front.add(other_vert)
                    if find_shortest_path:
                        distance = (vert.co - other_vert.co).length
                        new_distance = vert[path_distance] + distance
                        prev_distance = other_vert[path_distance]
                        if prev_distance == 0 or prev_distance > new_distance:
                            other_vert[path_prev_distance] = distance
                            other_vert[path_distance] = new_distance
                            other_vert[path_prev_index] = vert.index
                            other_vert[init_index] = vert[init_index]
        #debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    return [vert[index] for vert in bm.verts]
