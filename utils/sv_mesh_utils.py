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
from numpy import array, empty, concatenate, unique, sort, int32, ndarray



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


def pol_to_edges(pol):

    edges = empty([len(pol), 2], 'i')
    edges[:, 0] = pol
    edges[1:, 1] = pol[:-1]
    edges[0, 1] = pol[-1]

    return edges

def polygons_to_edges_np(obj, unique_edges=False, output_numpy=False):
    result = []

    for pols in obj:
        regular_mesh = True
        try:
            np_pols = array(pols, dtype=int32)
        except ValueError:
            regular_mesh = False

        if not regular_mesh:
            if output_numpy:
                result.append(concatenate([pol_to_edges(p) for p in pols]))
            else:
                result.append(polygons_to_edges([pols], unique_edges)[0])
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
