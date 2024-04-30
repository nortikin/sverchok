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

from contextlib import contextmanager
import math
from operator import setitem, getitem
from itertools import count
from typing import ContextManager

import numpy as np

import bmesh
from bmesh.types import BMVert, BMEdge, BMFace
import mathutils

from sverchok.data_structure import zip_long_repeat, has_element
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.math import np_dot

@contextmanager
def empty_bmesh(use_operators=True):
    """
    Usage:
    with empty_bmesh() as bm:
        generate_mesh(bm)
        bm.do_something
        ...
    """
    error = None
    bm = bmesh.new(use_operators=use_operators)
    try:
        yield bm
    except Exception as Ex:
        error = Ex
    finally:
        bm.free()
    if error:
        raise error


class EmptyBmesh:
    """It's a bit faster than empty_bmesh because there is need to generate
    new manager class each call"""
    def __init__(self, use_operators=True):
        """:suppress: if True any errors during node execution will be suppressed"""
        self._use_operators = use_operators
        self._bm = bmesh.new(use_operators=use_operators)

    def __enter__(self):
        return self._bm

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._bm.free()
        if exc_val:
            raise


@contextmanager
def bmesh_from_edit_mesh(mesh) -> ContextManager[bmesh.types.BMesh]:
    """Returns bmesh from given mesh in edit mode. All bmesh changes will effect the mesh"""
    bm = bmesh.from_edit_mesh(mesh)
    try:
        yield bm
    except Exception:
        raise
    finally:
        bmesh.update_edit_mesh(mesh)

def bmesh_from_pydata(
        verts=None, edges=[], faces=[],
        markup_face_data=False, markup_edge_data=False, markup_vert_data=False,
        normal_update=False, index_edges=False):

    """
    verts              : necessary
    edges / faces      : optional
    normal_update      : optional - will update verts/edges/faces normals at the end
    index_edges (bool) : optional - will make it possible for users of the bmesh to manually 
                         iterate over any edges or do index lookups
    """

    bm = bmesh.new()
    bm_verts = bm.verts
    add_vert = bm_verts.new

    py_verts = verts.tolist() if type(verts) == np.ndarray else verts

    for co in py_verts:
        add_vert(co)

    bm_verts.index_update()
    bm_verts.ensure_lookup_table()

    if has_element(faces):
        add_face = bm.faces.new
        py_faces = faces.tolist() if type(faces) == np.ndarray else faces
        for face in py_faces:
            add_face(tuple(bm_verts[i] for i in face))

        bm.faces.index_update()

    if has_element(edges):
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

    if has_element(edges) or index_edges:
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


def add_mesh_to_bmesh(bm, verts, edges=None, faces=None, sv_index_name=None, update_indexes=True, update_normals=True):
    new_vert = bm.verts.new
    new_edge = bm.edges.new
    new_face = bm.faces.new
    bm_verts = [new_vert(co) for co in verts]

    #[new_edge((bm_verts[i1], bm_verts[i2])) for i1, i2 in edges or []] # не надо так делать
    if edges is not None:
        for i1, i2 in edges:
            new_edge((bm_verts[i1], bm_verts[i2]))
    else:
        new_edges = []
    #[new_face([bm_verts[i] for i in face]) for face in faces or []] # не надо так делать
    if faces is not None:
        # remove double faces. Some times get faces with same verts but with another order: [62,103,102] and [102,103,62].
        # this is not compatible with mesh and only one of that faces can be used. So convert this faces indices into dictionary.
        # this remove faces with the same vertices but same or different orders. This may happens on some of Voronoi if
        # it slice self intersected mesh.
        dict_faces = { tuple(sorted(f)): f for f in list(faces) }
        for face in dict_faces.values():
            new_face([bm_verts[i] for i in face])
    else:
        new_face = []

    if update_normals:
        bm.normal_update()

    if sv_index_name:
        for sequence in [bm.verts, bm.edges, bm.faces]:
            lay = sequence.layers.int.get(sv_index_name, sequence.layers.int.new(sv_index_name))
            [setitem(el, lay, el.index) for el in sequence]
        loop_lay = bm.loops.layers.int.get(sv_index_name, bm.loops.layers.int.new(sv_index_name))
        loop_indexes = count()
        [setitem(l, loop_lay, next(loop_indexes)) for face in bm.faces for l in face.loops]

    # update mesh
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    if update_indexes:
        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()


def numpy_data_from_bmesh(bm, out_np, face_data=None):
    if out_np[0]:
        verts = np.array([v.co for v in bm.verts])
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

def pydata_from_bmesh(bm, face_data=None, ret_verts=True, ret_edges=True, ret_faces=True):

    verts = [v.co[:] for v in bm.verts] if ret_verts==True and face_data is None else None
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges] if ret_edges==True and face_data is None else None
    faces = [[i.index for i in p.verts] for p in bm.faces] if ret_faces==True and face_data is None else None

    if face_data is None:
        return verts, edges, faces
    else:
        face_data_out = face_data_from_bmesh_faces(bm, face_data)
        return verts, edges, faces, face_data_out


def mesh_indexes_from_bmesh(bm, layer_name):
    # returns python mesh and old indexes of mesh elements
    verts = [v.co[:] for v in bm.verts]
    edges = [[e.verts[0].index, e.verts[1].index] for e in bm.edges]
    faces = [[i.index for i in p.verts] for p in bm.faces]

    old_elements_indexes = []
    for sequence in [bm.verts, bm.edges, bm.faces]:
        lay = sequence.layers.int.get(layer_name, None)
        old_elements_indexes.append([getitem(el, lay) for el in sequence] if lay else [])

    loop_lay = bm.loops.layers.int.get(layer_name, None)
    old_elements_indexes.append(
        [getitem(l, loop_lay) for face in bm.faces for l in face.loops] if loop_lay else [])

    verts_indexes, edges_indexes, faces_indexes, loops_indexes = old_elements_indexes
    return verts, edges, faces, verts_indexes, edges_indexes, faces_indexes, loops_indexes


def get_partial_result_pydata(geom):
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
            sv_logger.debug("Unexisting face_data[%s] [0 - %s]", idx, n_face_data)
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
            sv_logger.debug("Unexisting edge_data[%s] [0 - %s]", idx, n_edge_data)
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
            sv_logger.debug("Unexisting vert_data[%s] [0 - %s]", idx, n_vert_data)
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
            sv_logger.debug("Unexisting edge_mask[%s] [0 - %s]", idx, n_edge_mask)
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

def remove_doubles(vertices, edges, faces, d, face_data=None, vert_data=None, edge_data=None):
    """
    This is a wrapper for bmesh.ops.remove_doubles.

    vertices, edges, faces: standard sverchok formatted description of the mesh.
    d: the threshold for the merge procedure.
    face_data: arbitrary data per mesh face.
    vert_data: arbitrary data per mesh vertex.

    output:
        if face_data, vert_data or edge_data was specified, this outputs 4-tuple:
            * vertices
            * edges
            * faces
            * data: a dictionary with following keys:
                * 'vert_init_index': indexes of the output vertices in the original mesh
                * 'edge_init_index': indexes of the output edges in the original mesh
                * 'face_init_index': indexes of the output faces in the original mesh
                * 'verts': correctly reordered vert_data (if present)
                * 'edges': correctly reordered edge_data (if present)
                * 'faces': correctly reordered face_data (if present)
    """
    has_vert_data = bool(vert_data)
    has_edge_data = bool(edge_data)
    has_face_data = bool(face_data)
    bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True,
                           markup_face_data=has_face_data,
                           markup_edge_data=has_edge_data,
                           markup_vert_data=has_vert_data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=d)
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    verts, edges, faces = pydata_from_bmesh(bm)
    if not (has_face_data or has_vert_data or has_edge_data):
        bm.free()
        return verts, edges, faces

    data = dict()
    vert_layer = bm.verts.layers.int.get("initial_index")
    edge_layer = bm.edges.layers.int.get("initial_index")
    face_layer = bm.faces.layers.int.get("initial_index")
    if vert_layer:
        data['vert_init_index'] = [vert[vert_layer] for vert in bm.verts]
    if edge_layer:
        data['edge_init_index'] = [edge[edge_layer] for edge in bm.edges]
    if face_layer:
        data['face_init_index'] = [face[face_layer] for face in bm.faces]
    if has_vert_data:
        data['verts'] = vert_data_from_bmesh_verts(bm, vert_data)
    if has_edge_data:
        data['edges'] = edge_data_from_bmesh_edges(bm, vert_data)
    if has_face_data:
        data['faces'] = face_data_from_bmesh_faces(bm, face_data)
    bm.free()
    return verts, edges, faces, data



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
    new_bm_add_vert = new_bm.verts.new
    new_bm_add_face = new_bm.faces.new
    copied_verts = dict()
    for vert in bm.verts:
        co = vert.co
        copied_verts[vert.index] = new_bm_add_vert(co)

    # Make vertices of dual mesh by finding
    # centers of original mesh faces.
    center_verts = dict()
    for face in bm.faces:
        co = face.calc_center_median()
        center_verts[face.index] = new_bm_add_vert(co)

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
            new_bm_add_face(face_verts)
        else: # n_faces == 2
            face1, face2 = edge_faces
            ev1, ev2 = edge.verts
            face_verts = copied_verts[ev1.index], center_verts[face1.index], copied_verts[ev2.index], center_verts[face2.index]
            new_normal = mathutils.geometry.normal(*[vert.co for vert in face_verts])
            old_normal = face1.normal + face2.normal
            if new_normal.dot(old_normal) < 0:
                face_verts = list(reversed(face_verts))
            new_bm_add_face(face_verts)
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
    new_bm_add_vert = new_bm.verts.new
    new_bm_add_face = new_bm.faces.new
    edge_centers = dict()

    for edge in bm.edges:
        center_co = (edge.verts[0].co + edge.verts[1].co) / 2.0
        edge_centers[edge.index] = new_bm_add_vert(center_co)
 
    for face in bm.faces:
        new_face = [edge_centers[edge.index] for edge in face.edges]
        old_normal = face.normal
        new_normal = mathutils.geometry.normal(*[vert.co for vert in new_face])
        if new_normal.dot(old_normal) < 0:
            new_face = list(reversed(new_face))
        new_bm_add_face(new_face)

    for vertex in bm.verts:
        new_face = [edge_centers[edge.index] for edge in vertex.link_edges]
        if len(new_face) > 2:
            old_normal = vertex.normal
            orth = old_normal.orthogonal()
            co_orth = old_normal.cross(orth)
            new_face = sorted(new_face, key = lambda edge_center : calc_angle(vertex.co, orth, co_orth, edge_center))
            new_face = list(new_face)
            new_bm_add_face(new_face)

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
    * wave_path_prev_distance : float, output; the euclidean distance to the
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
    is_reached = bm.faces.layers.int.new("is_reached")  # True for painted faces
    obstacles = bm.faces.layers.int.get("wave_obstacle")
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()

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
    while wave_front:
        step += 1
        new_wave_front = set()
        for face in wave_front:
            face[index] = step
            face[is_reached] = 1
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
        # sv_logger.debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    # fix values for unpainted faces
    for face in bm.faces:
        if not face[is_reached] and not is_obstacle(face):
            # is obstacle can be removed in next version to be consistent with
            # unreached parts of the mesh
            face[index] = -1
            if find_shortest_path:
                face[path_distance] = -1
                face[init_index] = -1

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
    is_reached = bm.verts.layers.int.new("is_reached")  # True for painted verts
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()

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
    while wave_front:
        step += 1
        new_wave_front = set()
        for vert in wave_front:
            vert[index] = step
            vert[is_reached] = 1
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
        # sv_logger.debug("Front #%s: %s", step, len(new_wave_front))
        done.update(wave_front)
        wave_front = new_wave_front

    # fix values for unpainted vertices
    for vert in bm.verts:
        if not vert[is_reached] and not is_obstacle(vert):
            # is obstacle can be removed in next version to be consistent with
            # unreached parts of the mesh
            vert[index] = -1
            if find_shortest_path:
                vert[path_distance] = -1
                vert[init_index] = -1

    return [vert[index] for vert in bm.verts]


def bmesh_bisect(bm, point, normal, fill):
    bm.normal_update()
    geom_in = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(
        bm, geom=geom_in, dist=0.00001,
        plane_co=point, plane_no=normal, use_snap_center=False,
        clear_outer=True, clear_inner=False)
    if fill:
        fres = bmesh.ops.edgenet_prepare(
            bm, edges=[e for e in res['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        )
        bmesh.ops.edgeloop_fill(bm, edges=fres['edges'])
    bm.verts.index_update()
    bm.edges.index_update()
    bm.faces.index_update()
    return bm

def bmesh_clip(bm, bounds, fill):
    x_min, x_max, y_min, y_max, z_min, z_max = bounds

    bmesh_bisect(bm, (x_min, 0, 0), (-1, 0, 0), fill)
    bmesh_bisect(bm, (x_max, 0, 0), (1, 0, 0), fill)
    bmesh_bisect(bm, (0, y_min, 0), (0, -1, 0), fill)
    bmesh_bisect(bm, (0, y_max, 0), (0, 1, 0), fill)
    bmesh_bisect(bm, (0, 0, z_min), (0, 0, -1), fill)
    bmesh_bisect(bm, (0, 0, z_max), (0, 0, 1), fill)

    return bm

def recalc_normals(verts, edges, faces, loop=False):
    if loop:
        verts_out, edges_out, faces_out = [], [], []
        for vs, es, fs in zip_long_repeat(verts, edges, faces):
            vs, es, fs = recalc_normals(vs, es, fs, loop=False)
            verts_out.append(vs)
            edges_out.append(es)
            faces_out.append(fs)
        return verts_out, edges_out, faces_out
    else:
        bm = bmesh_from_pydata(verts, edges, faces)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        verts, edges, faces = pydata_from_bmesh(bm)
        bm.free()
        return verts, edges, faces

def calc_center_mass_bmesh(center_mode, mesh_vertices, mesh_edges, mesh_faces, mass_of_vertices=None, object_density=None, skip_test_volume_are_closed=False, quad_mode="BEAUTY", ngon_mode="BEAUTY"):
    '''
    Calculate center of mass for single mesh.

    Input:
        - center_mode=['VERTICES', 'EDGES', 'FACES', 'VOLUMES']
        - mesh_vertices = [[x1,y1,z1],[x2,y2,z2],...] (float) - vertices of mesh
        - mesh_edges = [[0,1],[1,2],[2,3],...] (int) - indixes of verts (edges)
        - mesh_faces = [[0,1,2],[1,2,3,4,...], ...] - indixes of verts (faces)
        - mass_of_vertices = [ [ 1.1, 1.0, 5.2, 0.2,...] ] - mass of every vert in mesh. Extrapolate a last value to the all vertices
        - object_density = [1.2] - density of volume. If center_mode is EDGES or FACES then mass of objects are proportional to length or area.
        - skip_test_volume_are_closed - (only for volume node) If you know that volume are close then you can speed up performance if you set this parameter to True. False - force test mesh are closed.
        - quad_mode [BEAUTY, FIXED, ALTERNATE, SHORT_EDGE], ngon_mode [BEAUTY, EAR_CLIP] - modes for triangulation if mesh has faces with 4 and more vertices (for center_mode FACES of VOLUMES only)

    Output:

        - result_mask - True/False. If False then another output params are None
        - result_vertices, result_edges, result_polygons - result mesh (source mesh or triangulated mesh)
        - result_center_mass_mesh - center of mass of mesh
        - result_mass_mesh - mass of mesh
        - result_size_mesh - for VERTICES - count vertices, for EDGES - length of edges, for FACES - area of mesh, for VOLUMES - volume of mesh

    Example:
        https://github.com/nortikin/sverchok/assets/14288520/e432b5c0-35e5-432b-8c9f-798f58b71f13
    '''
    result_mask = result_vertices_I = result_edges_I = result_polygons_I = result_center_mass_mesh_I = result_mass_mesh_I = result_size_mesh_I = None

    vertices_I, edges_I, faces_I, mass_of_vertices_I, density_I = mesh_vertices, mesh_edges, mesh_faces, mass_of_vertices, object_density

    if mass_of_vertices_I is None:
        mass_of_vertices_I=[1]
    if density_I is None:
        density_I=[1]

    if len(vertices_I)==0:
        # skip mesh if no vertices at all:
        result_mask = False

    if center_mode=='VERTICES':

        if len(vertices_I)==0:
            result_mask = False
        else:
            result_mask = True
            result_vertices_I = vertices_I
            result_edges_I = edges_I
            result_polygons_I = faces_I

            # shrink or extend list of mass if list of mass is not equals list of verts:
            mass_of_vertices_I_shrinked = mass_of_vertices_I[:len(vertices_I)]
            mass_of_vertices_I_np1 = np.append( mass_of_vertices_I_shrinked, np.full( (len(vertices_I)-len(mass_of_vertices_I_shrinked)), mass_of_vertices_I_shrinked[-1]) )
            vertices_I_np = np.array(vertices_I)
            mass_of_vertices_I_np2  = np.array([mass_of_vertices_I_np1])
            mass_I = mass_of_vertices_I_np2.sum()
            center_mass_mesh_I_np = (vertices_I_np * mass_of_vertices_I_np2.T).sum(axis=0) / mass_I

            result_center_mass_mesh_I = center_mass_mesh_I_np.tolist()
            result_mass_mesh_I = mass_I
            result_size_mesh_I = vertices_I_np.shape[0]  # Count of vertices

    elif center_mode=='EDGES':
            
        old_edges = np.array(edges_I)
        if old_edges.size==0:
            # skip mesh if no edges at all:
            result_mask = False
        else:
            result_mask = True
            verts_I = np.array(vertices_I)

            # Do not triangulate mesh for 'EDGE' mode
            result_vertices_I = vertices_I
            result_edges_I = edges_I
            result_polygons_I = faces_I
            
            segment_I = verts_I[old_edges]
            distances_I = np.linalg.norm(segment_I[:,1]-segment_I[:,0], axis=1)
            length_I = distances_I.sum()
            segment_center_I = segment_I.sum(axis=1) / 2.0
            center_mass_mesh_I_np = (segment_center_I * distances_I[np.newaxis].T).sum(axis=0) / length_I
            mass_I             = length_I * density_I[0]

            result_center_mass_mesh_I = center_mass_mesh_I_np.tolist()
            result_mass_mesh_I = mass_I
            result_size_mesh_I = length_I

    elif center_mode=='FACES':
            
        faces_I_np = np.array(faces_I)
        if faces_I_np.size==0:
            # skip mesh if no faces at all:
            result_mask = False
        else:
            result_mask = True

            # test if some polygons are not tris:
            if max(map(len, faces_I_np))>3:
                # triangulate mesh for 'FACES' mode
                bm_I = bmesh_from_pydata(vertices_I, edges_I, faces_I, markup_face_data=True, normal_update=True)
                b_faces = []
                for face in bm_I.faces:
                    b_faces.append(face)
                res = bmesh.ops.triangulate(
                    bm_I, faces=b_faces, quad_method=quad_mode, ngon_method=ngon_mode
                )
                new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I)
                bm_I.free()
            else:
                new_vertices_I,new_edges_I,new_faces_I = vertices_I, edges_I, faces_I

            result_vertices_I = new_vertices_I
            result_edges_I = new_edges_I
            result_polygons_I = new_faces_I
            
            verts_I_np         = np.array(new_vertices_I)
            faces_I_np         = np.array(new_faces_I)
            tris_I_np          = verts_I_np[faces_I_np]
            areases_I          = np.linalg.norm(np.cross(tris_I_np[:,1]-tris_I_np[:,0], tris_I_np[:,2]-tris_I_np[:,0]) / 2.0, axis=1)
            area_I             = areases_I.sum()
            tris_centers_I     = tris_I_np.sum(axis=1) / 3.0
            center_mass_mesh_I_np = (tris_centers_I * areases_I[np.newaxis].T).sum(axis=0) / area_I
            mass_I             = area_I * density_I[0]

            result_center_mass_mesh_I = center_mass_mesh_I_np.tolist()
            result_mass_mesh_I = mass_I
            result_size_mesh_I = area_I

    elif center_mode=='VOLUMES':
            
        faces_I_np = np.array(faces_I)
        if faces_I_np.size==0:
            # skip mesh if no faces at all:
            result_mask = False
        else:
            do_calc = False
            if max(map(len, faces_I_np))==3 and skip_test_volume_are_closed==True:
                new_vertices_I, new_edges_I, new_faces_I = vertices_I, edges_I, faces_I
                do_calc = True
            else:
                # triangulate mesh
                bm_I = bmesh_from_pydata(vertices_I, edges_I, faces_I, markup_face_data=True, normal_update=True)
                # test if all edges are contiguous (https://docs.blender.org/api/current/bmesh.types.html#bmesh.types.BMEdge.is_contiguous)
                # then volume is closed:
                for edge in bm_I.edges:
                    if edge.is_contiguous==False:
                        do_calc = False
                        break
                else:
                    do_calc = True
                    # test if some polygons are not tris:
                    if max(map(len, faces_I_np))>3:
                        b_faces = []
                        for face in bm_I.faces:
                            b_faces.append(face)

                        res = bmesh.ops.triangulate(
                            bm_I, faces=b_faces, quad_method=quad_mode, ngon_method=ngon_mode
                        )
                        new_vertices_I, new_edges_I, new_faces_I = pydata_from_bmesh(bm_I)
                    else:
                        new_vertices_I, new_edges_I, new_faces_I = vertices_I, edges_I, faces_I
                bm_I.free()

            if do_calc==False:
                result_mask = False
            else:
                result_mask = True
                result_vertices_I = new_vertices_I
                result_edges_I    = new_edges_I
                result_polygons_I = new_faces_I
                
                verts_I = np.array(new_vertices_I)
                faces_I = np.array(new_faces_I)
                tris_I = verts_I[faces_I]
                # to precise calc move all mesh to median point
                tris_I_median = np.median(tris_I, axis=(0,1))
                tris_I_delta = tris_I-tris_I_median
                signed_volumes_I   = np_dot(tris_I_delta[:,0], np.cross(tris_I_delta[:,1], tris_I_delta[:,2]))
                volume_I           = signed_volumes_I.sum()
                tetra_centers_I    = tris_I_delta.sum(axis=1) / 4.0
                center_mass_mesh_I_np = (tetra_centers_I * signed_volumes_I[np.newaxis].T).sum(axis=0) / volume_I + tris_I_median
                mass_I             = volume_I * density_I[0]

                result_center_mass_mesh_I = center_mass_mesh_I_np.tolist()
                result_mass_mesh_I = mass_I
                result_size_mesh_I = volume_I
    else:
        raise Exception(f'calc_center_of_mesh: param \'center_mode\'={center_mode} must be in [\'VERTICES\', \'EDGES\', \'FACES\', \'VOLUMES\']')

    return result_mask, result_vertices_I, result_edges_I, result_polygons_I, result_center_mass_mesh_I, result_mass_mesh_I, result_size_mesh_I