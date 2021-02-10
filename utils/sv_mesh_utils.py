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

from sverchok.data_structure import fullList_deep_copy
from numpy import array, empty, concatenate, unique, sort, int32, ndarray, vectorize

from mathutils import Vector
try:
    from mathutils.geometry import delaunay_2d_cdt
except ImportError:
    pass

from sverchok.data_structure import fullList_deep_copy
from sverchok.utils.geom import linear_approximation

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
    else:
        return verts, edges, faces

def get_unique_faces(faces):
    uniq_faces = []
    for face in faces:
        if set(face) in [set(f) for f in uniq_faces]:
            print(face)
        else:
            uniq_faces.append(face)
    return uniq_faces

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

