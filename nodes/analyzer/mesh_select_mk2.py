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

import math

from mathutils import Vector, kdtree

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, describe_data_shape, numpy_match_long_repeat, repeat_last_for_length
from sverchok.utils.math import np_dot
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.modules.polygon_utils import pols_normals

def select_verts_by_faces(faces, verts):
    flat_index_list = {idx for face in faces for idx in face}
    return [v in flat_index_list for v in range(len(verts))]

def select_edges_by_verts(verts_mask, edges, include_partial):
    if isinstance(verts_mask, np.ndarray):
        return select_edges_by_verts_numpy(verts_mask, edges, include_partial)
    return select_edges_by_verts_python(verts_mask, edges, include_partial)

def select_edges_by_verts_python(verts_mask, edges, include_partial):
    result = []
    for u,v in edges:
        if include_partial:
            ok = verts_mask[u] or verts_mask[v]
        else:
            ok = verts_mask[u] and verts_mask[v]
        result.append(ok)
    return result

def select_edges_by_verts_numpy(verts_mask, edges, include_partial):
    if include_partial:
        result = np.any(verts_mask[np.array(edges)], axis=1)
    else:
        result = np.all(verts_mask[np.array(edges)], axis=1)

    return result.tolist()

def select_faces_by_verts(verts_mask, faces, include_partial):
    result = []
    for face in faces:
        if include_partial:
            ok = any(verts_mask[i] for i in face)
        else:
            ok = all(verts_mask[i] for i in face)
        result.append(ok)
    return result

def map_percent(values, percent):
    maxv = np.amax(values)
    minv = np.amin(values)
    if maxv <= minv:
        return maxv
    return maxv - percent * (maxv - minv) * 0.01

def by_side(verts, direction, percent):
    np_verts = np.array(verts)
    np_dir = np.array(direction)
    np_dir, np_percent = numpy_match_long_repeat([np_dir, np.array(percent)])
    values = np_dot(np_verts[:,np.newaxis], np_dir[np.newaxis,:], axis=2)
    threshold = map_percent(values, np_percent)
    out_verts_mask = np.any(values >= threshold, axis=1)
    return out_verts_mask

def by_bbox(vertices, points, radius):
    np_rads = np.array(radius)
    np_verts = np.array(vertices)
    np_bbox = np.array(points)
    bbox_max = np.amax(np_bbox, axis=0)
    bbox_min = np.amin(np_bbox, axis=0)
    min_mask = np_verts > bbox_min - np_rads[:, np.newaxis]
    max_mask = np_verts < bbox_max + np_rads[:, np.newaxis]
    out_verts_mask = np.all(np.all([min_mask, max_mask], axis=0), axis=1)

    return out_verts_mask

def by_sphere(vertices, centers, radius):

    if len(centers) == 1:
        center = centers[0]
        out_verts_mask = np.linalg.norm(np.array(vertices)-np.array(center)[np.newaxis,:], axis=1)<= radius[0]
    else:
        # build KDTree
        tree = kdtree.KDTree(len(centers))
        for i, v in enumerate(centers):
            tree.insert(v, i)
        tree.balance()

        out_verts_mask = []
        rad = repeat_last_for_length(radius, len(centers))
        for vertex in vertices:
            _, idx, rho = tree.find(vertex)
            mask = rho <= rad[idx]
            out_verts_mask.append(mask)
    return out_verts_mask


def by_plane(vertices, center, radius, direction):

    np_verts = np.array(vertices)
    np_center = np.array(center)
    np_normal = np.array(direction)
    normal_length= np.linalg.norm(np_normal, axis=1)
    np_normal /= normal_length[:, np.newaxis]
    np_rad = np.array(radius)
    np_center, np_normal, np_rad = numpy_match_long_repeat([np_center, np_normal, np_rad])
    vs = np_verts[np.newaxis, :, :] - np_center[:, np.newaxis,:]
    distance = np.abs(np.sum(vs * np_normal[:,np.newaxis, :], axis=2))
    out_verts_mask = np.any(distance < np_rad[:,np.newaxis], axis=0)

    return out_verts_mask


def by_cylinder(vertices, center, radius, direction):
    np_vertices = np.array(vertices)
    np_location = np.array(center)
    np_direction = np.array(direction)
    np_direction = np_direction/np.linalg.norm(np_direction, axis=1)[:, np.newaxis]
    np_radius = np.array(radius)
    np_location, np_direction, np_radius = numpy_match_long_repeat([np_location, np_direction, np_radius])
    v_attract = np_vertices[np.newaxis, :, :] - np_location[:, np.newaxis, :]
    vect_proy = np_dot(v_attract, np_direction[:, np.newaxis, :], axis=2)

    closest_point = np_location[:, np.newaxis, :] + vect_proy[:, :, np.newaxis] * np_direction[:, np.newaxis, :]

    dif_v = closest_point - np_vertices[np.newaxis, :, :]
    dist_attract = np.linalg.norm(dif_v, axis=2)
    out_verts_mask = np.any(dist_attract < np_radius[:, np.newaxis], axis=0)

    return out_verts_mask

def by_normal(vertices, edges, faces, percent, direction):
    face_normals = pols_normals(vertices, faces, output_numpy=True)
    np_dir, np_percent = numpy_match_long_repeat([np.array(direction), np.array(percent)])
    values = np_dot(face_normals[:, np.newaxis], np_dir[np.newaxis,:], axis=2)
    threshold = map_percent(values, np_percent)
    out_face_mask = np.any(values >= threshold, axis=1)

    return out_face_mask

def by_outside(vertices, edges, faces, percent, center):
    face_normals = pols_normals(vertices, faces, output_numpy=True)
    center = Vector(center[0])

    def get_center(face):
        verts = [Vector(vertices[i]) for i in face]
        result = Vector((0,0,0))
        for v in verts:
            result += v
        return (1.0/float(len(verts))) * result

    values = []
    for face, normal in zip(faces, face_normals):
        face_center = get_center(face)
        direction = face_center - center
        dirlength = direction.length
        if dirlength > 0:
            value = math.pi - direction.angle(normal)
        else:
            value = math.pi
        values.append(value)
    threshold = map_percent(values, percent[0])

    out_face_mask = [(value >= threshold) for value in values]

    return out_face_mask


def by_edge_dir(vertices, edges, percent, direction):

    np_verts = np.array(vertices)
    np_edges = np.array(edges)
    edges_v = np_verts[np_edges]
    edges_dir = edges_v[:, 1 , :] - edges_v[:, 0 ,:]
    np_dir = np.array(direction)
    np_dir /= np.linalg.norm(np_dir, axis=1)[:, np.newaxis]
    edges_dir /= np.linalg.norm(edges_dir, axis=1)[:, np.newaxis]
    np_percent = np.array(percent)
    np_dir, np_percent = numpy_match_long_repeat([np_dir, np_percent])

    values = np.abs(np_dot(edges_dir[:, np.newaxis], np_dir[np.newaxis, :], axis=2))
    threshold = map_percent(values, np_percent)

    out_edges_mask = np.any(values >= threshold, axis=1)

    return out_edges_mask

def edge_modes_select(params, mode='BySide', v_mask=True, e_mask=True, p_mask=True, include_partial=True):
    vertices, edges, faces, direction, center, percent, radius = params
    if mode == 'EdgeDir':
        out_edges_mask = by_edge_dir(vertices, edges, percent, direction)

    out_edges = [edge for (edge, mask) in zip (edges, out_edges_mask) if mask]

    out_verts_mask = select_verts_by_faces(out_edges, vertices) if v_mask or p_mask else []

    out_faces_mask = select_faces_by_verts(out_verts_mask, faces, False) if p_mask else []

    return out_verts_mask, out_edges_mask.tolist() if isinstance(out_edges_mask, np.ndarray) else out_edges_mask, out_faces_mask



def face_modes_select(params, mode='BySide', v_mask=True, e_mask=True, p_mask=True, include_partial=True):
    vertices, edges, faces, direction, center, percent, radius = params
    if mode == 'ByNormal':
        out_faces_mask = by_normal(vertices, edges, faces, percent, direction)
        _include_partial = False
    if mode == 'Outside':
        out_faces_mask = by_outside(vertices, edges, faces, percent, center)
        _include_partial = include_partial

    out_faces = [face for (face, mask) in zip(faces, out_faces_mask) if mask]
    out_verts_mask = select_verts_by_faces(out_faces, vertices) if v_mask or e_mask else []
    out_edges_mask = select_edges_by_verts(out_verts_mask, edges, _include_partial) if e_mask else []

    return out_verts_mask, out_edges_mask, out_faces_mask.tolist() if (isinstance(out_faces_mask, np.ndarray) and p_mask) else out_faces_mask

def vert_modes_select(params, mode='BySide', v_mask=True, e_mask=True, p_mask=True, include_partial=True):
    verts, edges, faces, direction, center, percent, radius = params
    if mode == 'BySide':
        out_verts_mask = by_side(verts, direction, percent)
    if mode == 'BBox':
        out_verts_mask = by_bbox(verts, center, radius)
    if mode == 'BySphere':
        out_verts_mask = by_sphere(verts, center, radius)
    if mode == 'ByPlane':
        out_verts_mask = by_plane(verts, center, radius, direction)
    if mode == 'ByCylinder':
        out_verts_mask = by_cylinder(verts, center, radius, direction)
    if e_mask:
        out_edges_mask = select_edges_by_verts(out_verts_mask, edges, include_partial)
    else:
        out_edges_mask = []
    if p_mask:
        out_faces_mask = select_faces_by_verts(out_verts_mask, faces, include_partial)
    else:
        out_faces_mask = []

    return out_verts_mask.tolist() if (isinstance(out_verts_mask, np.ndarray) and v_mask) else out_verts_mask, out_edges_mask, out_faces_mask

VERT_MODES = ['BySide', 'BBox', 'BySphere', 'ByPlane', 'ByCylinder']
EDGE_MODES = ['EdgeDir']
FACE_MODES = ['ByNormal', 'Outside']

class SvMeshSelectNodeMk2(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    '''
    Triggers: Mask by geometry
    Tooltip: Select vertices, edges, faces by geometric criteria
    '''
    bl_idname = 'SvMeshSelectNodeMk2'
    bl_label = 'Select mesh elements'
    bl_icon = 'UV_SYNC_SELECT'

    modes = [
            ("BySide", "By side", "Select specified side of mesh", 0),
            ("ByNormal", "By normal direction", "Select faces with normal in specified direction", 1),
            ("BySphere", "By center and radius", "Select vertices within specified distance from center", 2),
            ("ByPlane", "By plane", "Select vertices within specified distance from plane defined by point and normal vector", 3),
            ("ByCylinder", "By cylinder", "Select vertices within specified distance from straight line defined by point and direction vector", 4),
            ("EdgeDir", "By edge direction", "Select edges that are nearly parallel to specified direction", 5),
            ("Outside", "Normal pointing outside", "Select faces with normals pointing outside", 6),
            ("BBox", "By bounding box", "Select vertices within bounding box of specified points", 7)
        ]

    def update_mode(self, context):
        self.inputs['Radius'].hide_safe = (self.mode not in ['BySphere', 'ByPlane', 'ByCylinder', 'BBox'])
        self.inputs['Center'].hide_safe = (self.mode not in ['BySphere', 'ByPlane', 'ByCylinder', 'Outside', 'BBox'])
        self.inputs['Percent'].hide_safe = (self.mode not in ['BySide', 'ByNormal', 'EdgeDir', 'Outside'])
        self.inputs['Direction'].hide_safe = (self.mode not in ['BySide', 'ByNormal', 'ByPlane', 'ByCylinder', 'EdgeDir'])

        updateNode(self, context)

    mode: EnumProperty(name="Mode",
            items=modes,
            default='ByNormal',
            update=update_mode)

    include_partial: BoolProperty(name="Include partial selection",
            description="Include partially selected edges/faces",
            default=False,
            update=updateNode)

    percent: FloatProperty(name="Percent",
            default=1.0,
            min=0.0, max=100.0,
            update=updateNode)

    radius: FloatProperty(name="Radius", default=1.0, min=0.0, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')
        if self.mode not in ['ByNormal', 'EdgeDir']:
            layout.prop(self, 'include_partial')
    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'list_match')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices").is_mandatory = True
        eds = self.inputs.new('SvStringsSocket', "Edges")
        eds.nesting_level = 3
        pols = self.inputs.new('SvStringsSocket', "Polygons")
        pols.nesting_level = 3
        d = self.inputs.new('SvVerticesSocket', "Direction")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)
        d.nesting_level = 3
        c = self.inputs.new('SvVerticesSocket', "Center")
        c.use_prop = True
        c.default_property = (0.0, 0.0, 0.0)
        c.nesting_level = 3
        perc = self.inputs.new('SvStringsSocket', 'Percent')
        perc.prop_name = 'percent'
        perc.nesting_level = 2
        rad = self.inputs.new('SvStringsSocket', 'Radius')
        rad.prop_name = 'radius'
        rad.nesting_level = 2

        self.outputs.new('SvStringsSocket', 'VerticesMask')
        self.outputs.new('SvStringsSocket', 'EdgesMask')
        self.outputs.new('SvStringsSocket', 'FacesMask')

        self.update_mode(context)

    def process_data(self, params):
        result = [[] for s in self.outputs]
        if self.mode in VERT_MODES:
            func = vert_modes_select
        elif self.mode in EDGE_MODES:
            func = edge_modes_select
        else:
            func = face_modes_select

        for local_params in zip(*params):
            masks = func(
                local_params,
                mode=self.mode,
                v_mask=self.outputs[0].is_linked,
                e_mask=self.outputs[1].is_linked,
                p_mask=self.outputs[2].is_linked,
                include_partial=self.include_partial
                )
            [r.append(r_local) for r, r_local in zip(result, masks)]
        return result


def register():
    bpy.utils.register_class(SvMeshSelectNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvMeshSelectNodeMk2)
