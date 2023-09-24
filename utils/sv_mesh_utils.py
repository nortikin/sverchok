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

from itertools import chain
import numpy as np
from numpy.linalg import norm as np_margnitude

from sverchok.data_structure import invert_index_list, has_element
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.math import np_normalize_vectors
from sverchok.utils.modules.polygon_utils import np_faces_normals

from mathutils import Vector


def mesh_join(vertices_s, edges_s, faces_s):
    '''Given list of meshes represented by lists of vertices, edges and faces,
    produce one joined mesh.'''

    offset = 0
    result_vertices = []
    result_edges = []
    result_faces = []
    if len(edges_s) == 0:
        edges_s = [[]] * len(faces_s)
    for vertices, edges, faces in zip(vertices_s, edges_s, faces_s):
        result_vertices.extend(vertices)
        new_edges = [tuple(i + offset for i in edge) for edge in edges]
        new_faces = [[i + offset for i in face] for face in faces]
        result_edges.extend(new_edges)
        result_faces.extend(new_faces)
        offset += len(vertices)
    return result_vertices, result_edges, result_faces


def polygons_to_edges(obj, unique_edges=False):
    out = []
    for faces in obj:
        out_edges = []
        seen = set()
        for face in faces:
            for edge in zip(face, list(face[1:]) + list([face[0]])):
                if unique_edges and tuple(sorted(edge)) in seen:
                    continue
                if unique_edges:
                    seen.add(tuple(sorted(edge)))
                out_edges.append(edge)
        out.append(out_edges)
    return out


def pols_to_edges_irregular_mesh(pols, unique_edges):
    np_pols = np.array(pols,dtype=object)
    np_len = np.vectorize(len)
    lens = np_len(np_pols)
    pol_types = np.unique(lens)

    edges = []
    for sides_number in pol_types:
        mask = lens == sides_number
        np_pols_g = np.array(np_pols[mask].tolist())
        edges_g = np.empty(list(np_pols_g.shape)+[2], 'i')
        edges_g[:, :, 0] = np_pols_g
        edges_g[:, 1:, 1] = np_pols_g[:, :-1]
        edges_g[:, 0, 1] = np_pols_g[:, -1]

        edges_g = edges_g.reshape(-1, 2)
        edges.append(edges_g)
    if unique_edges:
        return np.unique(np.sort(np.concatenate([eds for eds in edges])), axis=0)

    return np.concatenate([eds for eds in edges])

def polygons_to_edges_np(obj, unique_edges=False, output_numpy=False):
    result = []

    for pols in obj:
        if len(pols) == 0:
            result.append([])
            continue
        regular_mesh = True
        try:
            np_pols = np.array(pols, dtype=np.int32)
        except ValueError:
            regular_mesh = False

        if not regular_mesh:
            if output_numpy:
                result.append(pols_to_edges_irregular_mesh(pols, unique_edges))
            else:
                result.append(pols_to_edges_irregular_mesh(pols, unique_edges).tolist())

        else:

            edges = np.empty(list(np_pols.shape)+[2], 'i')
            edges[:, :, 0] = np_pols
            edges[:, 1:, 1] = np_pols[:, :-1]
            edges[:, 0, 1] = np_pols[:, -1]

            edges = edges.reshape(-1, 2)
            if output_numpy:
                if unique_edges:
                    result.append(np.unique(np.sort(edges), axis=0))
                else:
                    result.append(edges)
            else:
                if unique_edges:
                    result.append(np.unique(np.sort(edges), axis=0).tolist())
                else:
                    result.append(edges.tolist())
    return result

def mask_vertices(verts, edges, faces, verts_mask):
    if any(not m for m in verts_mask):
        vert_indexes = [i for i, m in enumerate(verts_mask) if m]
        index_set = set(vert_indexes)
        vert_dict = {vert_idx: i for i, vert_idx in enumerate(vert_indexes)}

        new_verts = [verts[i] for i in vert_indexes]
        new_edges = [[vert_dict[n] for n in edge]
                        for edge in edges if index_set.issuperset(edge)]
        new_faces = [[vert_dict[n] for n in face]
                        for face in faces if index_set.issuperset(face)]

        return new_verts, new_edges, new_faces

    return verts, edges, faces

# mesh cleaning functions

def get_unique_faces(faces):
    return get_unique_topology(faces)[0]

def get_unique_topology(edg_pol):
    '''
    Removes doubled items
    edg_pol: list of edges or polygons List[List[Int]]
    returns Tuple (List of unique items, Boolean List with preserved items marked as True)
    '''
    uniq_edg_pols = []
    unique_sets = []
    preseved_mask = []
    for e_p in edg_pol:
        e_p_set = set(e_p)
        if not e_p_set in unique_sets:
            uniq_edg_pols.append(e_p)
            unique_sets.append(e_p_set)
            preseved_mask.append(True)
        else:
            preseved_mask.append(False)
    return uniq_edg_pols, preseved_mask

def remove_unreferenced_verts(verts, edges, faces):
    '''
    Removes unreferenced vertices
    verts: list of vertices List[List[float]]
    edges: list of edges List[List[Int]]
    faces: list of polygons List[List[Int]]
    returns Tuple (List used verts,
                   List with updated edges,
                   List with updated polyogn
                   List with removed items marked as True)
    '''
    e_indx = set(chain.from_iterable(edges))
    f_indx = set(chain.from_iterable(faces))
    indx = set.union(e_indx, f_indx)
    verts_out = [v for i, v in enumerate(verts) if i in indx]

    v_index = {j: i for i, j in enumerate(sorted(indx))}
    edges_out = [list(map(lambda n: v_index[n], e)) for e in edges]
    faces_out = [list(map(lambda n: v_index[n], f)) for f in faces]
    return verts_out, edges_out, faces_out, list(set(range(len(verts)))-indx)

def remove_unreferenced_topology(edge_pol, verts_length):
    '''
    Removes elements that point to unexisitng vertices
    edg_pol: list of edges or polygons - List[List[Int]]
    returns Tuple (referenced items - List[List[Int]],
                   Boolean List with preserved items marked as True - List[bool])
    '''
    edge_pol_out = []
    preseved_mask = []
    for ep in edge_pol:
        if all([c < verts_length for c in ep]):
            edge_pol_out.append(ep)
            preseved_mask.append(True)
        else:
            preseved_mask.append(False)
    return edge_pol_out, preseved_mask

def non_coincident_edges(edges):
    '''
    Removes edges with repeated indices
    edges: list of edges - List[List[Int]] or Numpy array with shape (n,2)
    returns Tuple (valid edges - List[List[Int]] or similar Numpy array,
                   Boolean List with preserved items marked as True - List[bool] or similar numpy array)
    '''

    if isinstance(edges, np.ndarray):
        preseved_mask = edges[:, 0] != edges[:, 1]
        edges_out = edges[preseved_mask]
    else:
        edges_out = []
        preseved_mask = []
        for e in edges:
            if e[0] == e[1]:
                preseved_mask.append(False)
            else:
                edges_out.append(e)
                preseved_mask.append(True)
    return edges_out, preseved_mask

def non_redundant_faces_indices(faces):
    '''
    Removes repeated indices from faces and removes faces with less than three indices
    faces: list of faces - List[List[Int]]
    returns Tuple (valid faces - List[List[Int]],
                   Boolean List with preserved items marked as True - List[bool])
    '''
    faces_out = []
    preseved_mask = []
    for f in faces:
        new_face = []
        for idx, c in enumerate(f):
            if c != f[idx-1]:
                new_face.append(c)
        if len(new_face) > 2:
            faces_out.append(new_face)
            preseved_mask.append(True)
        else:
            preseved_mask.append(False)

    return faces_out, preseved_mask

def clean_meshes(vertices, edges, faces,
                 remove_unreferenced_edges=False,
                 remove_unreferenced_faces=False,
                 remove_duplicated_edges=False,
                 remove_duplicated_faces=False,
                 remove_degenerated_edges=False,
                 remove_degenerated_faces=False,
                 remove_loose_verts=False,
                 calc_verts_idx=False,
                 calc_edges_idx=False,
                 calc_faces_idx=False):
    '''
    Cleans a group of meshes using different routines.
    Returns cleaned meshes and removed items indexes
    '''
    verts_out, edges_out, faces_out = [], [], []
    verts_removed_out, edges_removed_out, faces_removed_out = [], [], []

    for verts_original, edges_original, faces_original in zip(vertices, edges, faces):
        verts_changed, edges_changed, faces_changed = False, False, False

        preserved_edges_idx = []
        preserved_faces_idx = []
        if remove_unreferenced_edges:
            edges, preserved_edges_mask = remove_unreferenced_topology(edges_original, len(verts_original))
            preserved_edges_idx = np.arange(len(edges_original))[preserved_edges_mask]
            edges_changed = True

        if remove_unreferenced_faces:
            faces, preserved_faces_mask = remove_unreferenced_topology(faces_original, len(verts_original))
            preserved_faces_idx = np.arange(len(faces_original))[preserved_faces_mask]
            faces_changed = True

        if remove_duplicated_edges:
            if edges_changed:
                edges, unique_edges_mask = get_unique_topology(edges)
                preserved_edges_idx = preserved_edges_idx[unique_edges_mask]
            else:
                edges, unique_edges_mask = get_unique_topology(edges_original)
                preserved_edges_idx = np.arange(len(edges_original))[unique_edges_mask]
            edges_changed = True

        if remove_duplicated_faces:
            if faces_changed:
                faces, unique_faces_mask = get_unique_topology(faces)
                preserved_faces_idx = preserved_faces_idx[unique_faces_mask]
            else:
                faces, unique_faces_mask = get_unique_topology(faces_original)
                preserved_faces_idx = np.arange(len(faces_original))[unique_faces_mask]
            faces_changed = True

        if remove_degenerated_edges:
            if edges_changed:
                edges, non_coincident_mask = non_coincident_edges(edges)
                preserved_edges_idx = preserved_edges_idx[non_coincident_mask]
            else:
                edges, non_coincident_mask = non_coincident_edges(edges_original)
                preserved_edges_idx = np.arange(len(edges_original))[non_coincident_mask]
            edges_changed = True
        if remove_degenerated_faces:
            if faces_changed:
                faces, non_redundant_mask = non_redundant_faces_indices(faces)
                preserved_faces_idx = preserved_faces_idx[non_redundant_mask]
            else:
                faces, non_redundant_mask = non_redundant_faces_indices(faces_original)
                preserved_faces_idx = np.arange(len(faces_original))[non_redundant_mask]
            faces_changed = True

        if remove_loose_verts:
            verts, edges, faces, removed_verts_idx = remove_unreferenced_verts(
                verts_original,
                edges if edges_changed else edges_original,
                faces if faces_changed else faces_original)
            verts_changed = True
            edges_changed = True
            faces_changed = True


        if verts_changed:
            verts_out.append(verts)
            if calc_verts_idx:
                verts_removed_out.append(removed_verts_idx)
            else:
                verts_removed_out.append([])

        else:
            verts_out.append(verts_original)
            verts_removed_out.append([])

        if edges_changed:
            edges_out.append(edges)
            if calc_edges_idx and len(preserved_edges_idx) > 0:
                edges_removed_out.append(invert_index_list(preserved_edges_idx, len(edges_original)).tolist())

            else:
                edges_removed_out.append([])

        else:
            edges_out.append(edges_original)
            edges_removed_out.append([])

        if faces_changed:
            faces_out.append(faces)
            if calc_faces_idx and len(preserved_faces_idx) > 0:
                faces_removed_out.append(invert_index_list(preserved_faces_idx, len(faces_original)).tolist())

            else:
                faces_removed_out.append([])

        else:
            faces_out.append(faces_original)
            faces_removed_out.append([])

    return verts_out, edges_out, faces_out, verts_removed_out, edges_removed_out, faces_removed_out


def non_redundant_faces_indices_np(faces):
    F = np.array(faces)
    M = np.sort(F, axis=-1, order=None)

    # from https://stackoverflow.com/a/16973510/1243487
    K = np.ascontiguousarray(M).view(np.dtype((np.void, M.dtype.itemsize * M.shape[1])))
    _, idx = np.unique(K, return_index=True)
    return F[idx]    


def point_inside_mesh(bvh, point):
    point = Vector(point)
    axis = Vector((1, 0, 0))
    outside = True
    location, normal, index, distance = bvh.ray_cast(point, axis)
    if index is not None:
        if normal.dot(point-location)<0:
            outside = False

    return not outside

################
# Mesh Normals #
################
def prepare_arrays(vertices, faces):
    if isinstance(vertices, np.ndarray):
        np_verts = vertices
    else:
        np_verts = np.array(vertices)

    if isinstance(faces, np.ndarray):
        np_faces = faces
    else:
        np_faces = np.array(faces)

    return np_verts, np_faces

def mean_weighted_equally(np_faces, v_pols, v_normals, non_planar, algorithm):
    pol_sides = v_pols.shape[1]
    if non_planar:
        f_normals = np.zeros((len(v_pols), 3), dtype=np.float64)
        for i in range(pol_sides - 1):
            f_normals += np.cross(v_pols[::, (1+i)%pol_sides] - v_pols[::, i],
                                  v_pols[::, (i-1)%pol_sides] - v_pols[::, i])
    else:
        f_normals = np.cross(v_pols[::, 1] - v_pols[::, 0],
                             v_pols[::, 2] - v_pols[::, 0])
    if algorithm == 'MWE':
        np_normalize_vectors(f_normals)

    for i in range(np_faces.shape[1]):
        np.add.at(v_normals, np_faces[:, i], f_normals)

    if algorithm == 'MWAT':
        np_normalize_vectors(f_normals)
    return f_normals, v_normals


def factor_mw_angle(cross, side1, side2):
    return np.arcsin(np.clip(np_margnitude(cross, axis=1)/(np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1)),-1,1))

def factor_mw_angle_area(cross, side1, side2):
    area = np_margnitude(cross, axis=1)
    return area*np.arcsin(np.clip(area/(np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1)),-1,1))

def factor_mw_sine(cross, side1, side2):
    return 1/(np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1))

def factor_mw_sine_area(cross, side1, side2):
    return np_margnitude(cross, axis=1)/(np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1))

def factor_mw_sine_ed_length_r(cross, side1, side2):
    return 1/((np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1)**2))

def factor_mw_ed_length_r(cross, side1, side2):
    return 1/(np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1))

def factor_mw_ed_length(cross, side1, side2):
    return (np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1))

def factor_mw_root_ed_length_r(cross, side1, side2):
    return 1/((np_margnitude(side1, axis=1)*np_margnitude(side2, axis=1))**0.5)

def factor_mw_area(cross, side1, side2):
    return np_margnitude(cross, axis=1)

VERTEX_NORMAL_FACTOR_METHODS ={
    'MWA': factor_mw_angle,
    'MWS': factor_mw_sine,
    'MWSELR': factor_mw_sine_ed_length_r,
    'MWAT': factor_mw_area,
    'MWAAT': factor_mw_angle_area,
    'MWSAT': factor_mw_sine_area,
    'MWEL':factor_mw_ed_length,
    'MWELR':factor_mw_ed_length_r,
    'MWRELR': factor_mw_root_ed_length_r,
}
AREA_DEPENDENT_FACTORS = ('MWAT', 'MWS', 'MWSELR')

def mean_weighted_unequally(np_faces, v_pols, v_normals, non_planar, factor_mode):
    pol_sides = v_pols.shape[1]
    factor_func = VERTEX_NORMAL_FACTOR_METHODS[factor_mode]
    if non_planar:
        face_factor = np.zeros((len(v_pols), pol_sides), dtype=np.float64)
        f_normals = np.zeros((len(v_pols), 3), dtype=np.float64)
        for i in range(pol_sides - 1):
            side1 = v_pols[::, (1+i)%pol_sides] - v_pols[::, i]
            side2 = v_pols[::, (i-1)%pol_sides] - v_pols[::, i]
            cross = np.cross(side1, side2)
            face_factor[:, i] = factor_func(cross, side1, side2)
            f_normals += cross
    else:
        side1 = v_pols[::, 1] - v_pols[::, 0]
        side2 = v_pols[::, 2] - v_pols[::, 0]
        f_normals = np.cross(side1, side2)
        face_factor = factor_func(f_normals, side1, side2)

    if factor_mode in AREA_DEPENDENT_FACTORS:
        np_normalize_vectors(f_normals)

    for i in range(np_faces.shape[1]):
        np.add.at(v_normals, np_faces[:, i], f_normals*face_factor[:, i, np.newaxis])

    if not factor_mode in AREA_DEPENDENT_FACTORS:
        np_normalize_vectors(f_normals)
    return f_normals, v_normals

def calc_mesh_normals_np(vertices,
                         faces,
                         get_f_normals=True,
                         get_v_normals=True,
                         non_planar=True,
                         v_normal_alg='MWE',
                         output_numpy=True):
    if not has_element(faces):
        return [], vertices


    np_verts, np_faces = prepare_arrays(vertices, faces)


    if get_v_normals:
        v_normals = np.zeros(np_verts.shape, dtype=np_verts.dtype)
        if v_normal_alg in ('MWE', 'MWAT'):
            norm_func = mean_weighted_equally
        else:
            norm_func = mean_weighted_unequally

    if np_faces.dtype == object:
        np_len = np.vectorize(len)
        lens = np_len(np_faces)
        pol_types = np.unique(lens)
        f_normals = np.zeros((len(np_faces), 3), dtype=np.float64)
        for pol_sides in pol_types:
            mask = lens == pol_sides
            np_faces_g = np.array(np_faces[mask].tolist())
            v_pols = np_verts[np_faces_g]
            if get_v_normals:
                f_normal_g, v_normals = norm_func(np_faces_g, v_pols, v_normals, non_planar, v_normal_alg)
            else:
                f_normal_g = np_faces_normals(v_pols)

            f_normals[mask, :] = f_normal_g

    else:
        pol_sides = np_faces.shape[1]
        v_pols = np_verts[np_faces]
        if get_v_normals:
            f_normals, v_normals = norm_func(np_faces, v_pols, v_normals, non_planar, v_normal_alg)
        else:
            f_normals = np_faces_normals(v_pols)

    if output_numpy:
        return (f_normals if get_f_normals else [],
                np_normalize_vectors(v_normals) if get_v_normals else [])
    return (f_normals.tolist() if get_f_normals else [],
            np_normalize_vectors(v_normals).tolist() if get_v_normals else [])


def calc_mesh_normals_bmesh(vertices, faces, get_f_normals=True, get_v_normals=True):
    bm = bmesh_from_pydata(vertices, [], faces, normal_update=True)
    vertex_normals = []
    face_normals = []
    if get_v_normals:
        for vertex in bm.verts:
            vertex_normals.append(tuple(vertex.normal))
    if get_f_normals:
        for face in bm.faces:
            face_normals.append(tuple(face.normal.normalized()))
    bm.free()
    return face_normals, vertex_normals
