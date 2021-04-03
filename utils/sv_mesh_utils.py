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
from sverchok.data_structure import invert_index_list
from numpy import (array, empty, concatenate, unique, sort, int32, vectorize,
                   arange as np_arange,
                   ndarray as np_ndarray)
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
    np_pols = array(pols)
    np_len = vectorize(len)
    lens = np_len(np_pols)
    pol_types = unique(lens)

    edges = []
    for sides_number in pol_types:
        mask = lens == sides_number
        np_pols_g = array(np_pols[mask].tolist())
        edges_g = empty(list(np_pols_g.shape)+[2], 'i')
        edges_g[:, :, 0] = np_pols_g
        edges_g[:, 1:, 1] = np_pols_g[:, :-1]
        edges_g[:, 0, 1] = np_pols_g[:, -1]

        edges_g = edges_g.reshape(-1, 2)
        edges.append(edges_g)
    if unique_edges:
        return unique(sort(concatenate([eds for eds in edges])), axis=0)

    return concatenate([eds for eds in edges])

def polygons_to_edges_np(obj, unique_edges=False, output_numpy=False):
    result = []

    for pols in obj:
        if len(pols) == 0:
            result.append([])
            continue
        regular_mesh = True
        try:
            np_pols = array(pols, dtype=int32)
        except ValueError:
            regular_mesh = False

        if not regular_mesh:
            if output_numpy:
                result.append(pols_to_edges_irregular_mesh(pols, unique_edges))
            else:
                result.append(pols_to_edges_irregular_mesh(pols, unique_edges).tolist())

        else:

            edges = empty(list(np_pols.shape)+[2], 'i')
            edges[:, :, 0] = np_pols
            edges[:, 1:, 1] = np_pols[:, :-1]
            edges[:, 0, 1] = np_pols[:, -1]

            edges = edges.reshape(-1, 2)
            if output_numpy:
                if unique_edges:
                    result.append(unique(sort(edges), axis=0))
                else:
                    result.append(edges)
            else:
                if unique_edges:
                    result.append(unique(sort(edges), axis=0).tolist())
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

    if isinstance(edges, np_ndarray):
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
    Returs Clened meshes and removed items indexes
    '''
    verts_out, edges_out, faces_out = [], [], []
    verts_removed_out, edges_removed_out, faces_removed_out = [], [], []

    for verts_original, edges_original, faces_original in zip(vertices, edges, faces):
        verts_changed, edges_changed, faces_changed = False, False, False

        preserved_edges_idx = []
        preserved_faces_idx = []
        if remove_unreferenced_edges:
            edges, preserved_edges_mask = remove_unreferenced_topology(edges_original, len(verts_original))
            preserved_edges_idx = np_arange(len(edges_original))[preserved_edges_mask]
            edges_changed = True

        if remove_unreferenced_faces:
            faces, preserved_faces_mask = remove_unreferenced_topology(faces_original, len(verts_original))
            preserved_faces_idx = np_arange(len(faces_original))[preserved_faces_mask]
            faces_changed = True

        if remove_duplicated_edges:
            if edges_changed:
                edges, unique_edges_mask = get_unique_topology(edges)
                preserved_edges_idx = preserved_edges_idx[unique_edges_mask]
            else:
                edges, unique_edges_mask = get_unique_topology(edges_original)
                preserved_edges_idx = np_arange(len(edges_original))[unique_edges_mask]
            edges_changed = True

        if remove_duplicated_faces:
            if faces_changed:
                faces, unique_faces_mask = get_unique_topology(faces)
                preserved_faces_idx = preserved_faces_idx[unique_faces_mask]
            else:
                faces, unique_faces_mask = get_unique_topology(faces_original)
                preserved_faces_idx = np_arange(len(faces_original))[unique_faces_mask]
            faces_changed = True

        if remove_degenerated_edges:
            if edges_changed:
                edges, non_coincident_mask = non_coincident_edges(edges)
                preserved_edges_idx = preserved_edges_idx[non_coincident_mask]
            else:
                edges, non_coincident_mask = non_coincident_edges(edges_original)
                preserved_edges_idx = np_arange(len(edges_original))[non_coincident_mask]
            edges_changed = True
        if remove_degenerated_faces:
            if faces_changed:
                faces, non_redundant_mask = non_redundant_faces_indices(faces)
                preserved_faces_idx = preserved_faces_idx[non_redundant_mask]
            else:
                faces, non_redundant_mask = non_redundant_faces_indices(faces_original)
                preserved_faces_idx = np_arange(len(faces_original))[non_redundant_mask]
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

def point_inside_mesh(bvh, point):
    point = Vector(point)
    axis = Vector((1, 0, 0))
    outside = False
    count = 0
    while True:
        location, normal, index, distance = bvh.ray_cast(point, axis)
        if index is None:
            break
        count += 1
        point = location + axis * 0.00001
    if count % 2 == 0:
        outside = True
    return not outside
