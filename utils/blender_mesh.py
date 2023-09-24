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

import numpy as np
# taken from here https://blenderartists.org/t/efficient-copying-of-vertex-coords-to-and-from-numpy-arrays/661467/3
def read_verts(blender_mesh, output_numpy=False):
    mverts_co = np.zeros((len(blender_mesh.vertices)*3), dtype=np.float64)
    blender_mesh.vertices.foreach_get("co", mverts_co)
    if output_numpy:
        return np.reshape(mverts_co, (len(blender_mesh.vertices), 3))
    return np.reshape(mverts_co, (len(blender_mesh.vertices), 3)).tolist()

def read_verts_normal(blender_mesh, output_numpy=False):
    mverts_normals = np.zeros((len(blender_mesh.vertices)*3), dtype=np.float64)
    blender_mesh.vertices.foreach_get("normal", mverts_normals)
    if output_numpy:
        return np.reshape(mverts_normals, (len(blender_mesh.vertices), 3))
    return np.reshape(mverts_normals, (len(blender_mesh.vertices), 3)).tolist()

def read_face_normal(blender_mesh, output_numpy=False):
    mface_normals = np.zeros((len(blender_mesh.polygons)*3), dtype=np.float64)
    blender_mesh.polygons.foreach_get("normal", mface_normals)
    if output_numpy:
        return np.reshape(mface_normals, (len(blender_mesh.polygons), 3))
    return np.reshape(mface_normals, (len(blender_mesh.polygons), 3)).tolist()

def read_face_center(blender_mesh, output_numpy=False):
    centers = np.zeros((len(blender_mesh.polygons)*3), dtype=np.float64)
    blender_mesh.polygons.foreach_get("center", centers)
    if output_numpy:
        return np.reshape(centers, (len(blender_mesh.polygons), 3))
    return np.reshape(centers, (len(blender_mesh.polygons), 3)).tolist()

def read_face_area(blender_mesh, output_numpy=False):
    areas = np.zeros((len(blender_mesh.polygons)), dtype=np.float64)
    blender_mesh.polygons.foreach_get("area", areas)
    if output_numpy:
        return areas
    return areas.tolist()

def read_edges(blender_mesh, output_numpy=False):
    fastedges = np.zeros((len(blender_mesh.edges)*2), dtype=np.int32)
    blender_mesh.edges.foreach_get("vertices", fastedges)
    if output_numpy:
        return np.reshape(fastedges, (len(blender_mesh.edges), 2))
    return np.reshape(fastedges, (len(blender_mesh.edges), 2)).tolist()

def read_materials_idx(blender_mesh, output_numpy=False):
    material_index = np.zeros((len(blender_mesh.polygons)), dtype=np.float64)
    blender_mesh.polygons.foreach_get("material_index", material_index)
    if output_numpy:
        return material_index
    return material_index.tolist()
