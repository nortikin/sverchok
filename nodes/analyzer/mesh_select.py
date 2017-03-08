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

from mathutils import Vector, Matrix

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh
from sverchok.nodes.analyzer.normals import calc_mesh_normals

class SvMeshSelectNode(bpy.types.Node, SverchCustomTreeNode):
    '''Select vertices, edges, faces by geometric criteria'''
    bl_idname = 'SvMeshSelectNode'
    bl_label = 'Mesh select'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
            ("BySide", "BySide", "By side", 0),
            ("ByNormal", "ByNormal", "By normal direction", 1),
            ("ByRange", "ByRange", "In range", 2)
        ]

    def update_mode(self, context):
        updateNode(self, context)

    mode = EnumProperty(name="Mode",
            items=modes,
            default='ByNormal',
            update=update_mode)

    include_partial = BoolProperty(name="Include partial selection",
            description="Include partially selected edges/faces",
            default=False,
            update=updateNode)

    percent = FloatProperty(name="Percent", 
            default=1.0,
            hard_min=0.0, hard_max=100.0,
            update=updateNode)

    radius = FloatProperty(name="Radius", default=1.0)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def update(self, context):
        self.inputs['Radius'].hide = (self.mode != 'ByRange')
        self.inputs['Center'].hide = (self.mode != 'ByRange')
        self.inputs['Percent'].hide = (self.mode not in ['BySide', 'ByNormal'])
        self.inputs['Direction'].hide = (self.mode not in ['BySide', 'ByNormal'])

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertices")
        self.inputs.new('StringsSocket', "Edges")
        self.inputs.new('StringsSocket', "Polygons")

        d = self.inputs.new('VerticesSocket', "Direction")
        d.use_prop = True
        d.prop = (0.0, 0.0, 1.0)

        c = self.inputs.new('VerticesSocket', "Center")
        c.use_prop = True
        c.prop = (0.0, 0.0, 0.0)

        self.inputs.new('StringsSocket', 'Percent').prop_name = 'percent'
        self.inputs.new('StringsSocket', 'Radius').prop_name = 'radius'

        self.outputs.new('StringsSocket', 'VerticesMask')
        self.outputs.new('StringsSocket', 'EdgesMask')
        self.outputs.new('StringsSocket', 'FacesMask')

        self.update_mode(context)

    def map_percent(self, values, percent):
        maxv = max(values)
        minv = min(values)
        if maxv <= minv:
            return maxv
        return minv + percent * (maxv - minv) * 0.01

    def select_verts_by_faces(self, faces, verts):
        return [any(v in face for face in faces) for v in range(len(verts))]

    def select_edges_by_verts(self, verts_mask, edges):
        result = []
        for u,v in edges:
            if self.include_partial:
                ok = verts_mask[u] or verts_mask[v]
            else:
                ok = verts_mask[u] and verts_mask[v]
            result.append(ok)
        return result

    def select_faces_by_verts(self, verts_mask, faces):
        result = []
        for face in faces:
            if self.include_partial:
                ok = any(verts_mask[i] for i in face)
            else:
                ok = all(verts_mask[i] for i in face)
            result.append(ok)
        return result

    def by_normal(self, vertices, edges, faces):
        vertex_normals, face_normals = calc_mesh_normals(vertices, edges, faces)
        percent = self.inputs['Percent'].sv_get(default=[1.0])[0]
        direction = self.inputs['Direction'].sv_get()[0]
        values = [Vector(n).dot(direction) for n in face_normals]
        threshold = self.map_percent(values, percent)

        out_face_mask = [(value >= threshold) for value in values]
        out_faces = [face for (face, mask) in zip(faces, out_face_mask) if mask]
        out_verts_mask = self.select_verts_by_faces(out_faces, vertices)
        out_edges_mask = self.select_edges_by_verts(out_verts_mask, edges)

        return out_verts_mask, out_edges_mask, out_faces_mask
    
    def by_side(self, vertices, edges, faces):
        percent = self.inputs['Percent'].sv_get(default=[1.0])[0]
        direction = self.inputs['Direction'].sv_get()[0]
        values = [Vector(v).dot(direction) for v in vertices]
        threshold = self.map_percent(values, percent)

        out_verts_mask = [(value >= threshold) for value in values]
        out_edges_mask = self.select_edges_by_verts(out_verts_mask, edges)
        out_faces_mask = self.select_faces_by_verts(out_verts_mask, faces)

        return out_verts_mask, out_edges_mask, out_faces_mask

    def by_range(self, vertices, edges, faces):
        center = self.inputs['Center'].sv_get()[0]
        radius = self.inputs['Radius'].sv_get(default=[1.0])[0]

        out_verts_mask = [((Vector(v) - Vector(center)).length <= radius) for v in vertices]
        out_edges_mask = self.select_edges_by_verts(out_verts_mask, edges)
        out_faces_mask = self.select_faces_by_verts(out_verts_mask, faces)

        return out_verts_mask, out_edges_mask, out_faces_mask

    def process(self):

        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        edges_s = self.inputs['Edges'].sv_get(default=[[]])
        faces_s = self.inputs['Polygons'].sv_get(default=[[]])

        out_vertices = []
        out_edges = []
        out_faces = []

        meshes = match_long_repeat([vertices_s, edges_s, faces_s])
        for vertices, edges, faces in zip(*meshes):
            if self.mode == 'BySide':
                vs, es, fs = self.by_side(vertices, edges, faces)
            elif self.mode == 'ByNormal':
                vs, es, fs = self.by_normal(vertices, edges, faces)
            elif self.mode == 'ByRange':
                vs, es, fs = self.by_range(vertices, edges, faces)
            else:
                raise ValueError("Unknown mode: " + self.mode)

            out_vertices.append(vs)
            out_edges.append(es)
            out_faces.append(fs)

        if self.outputs['VerticesMask'].is_linked:
            self.outputs['VerticesMask'].sv_set(out_vertices)
        if self.outputs['EdgesMask'].is_linked:
            self.outputs['EdgesMask'].sv_set(out_edges)
        if self.outputs['FacesMask'].is_linked:
            self.outputs['FacesMask'].sv_set(out_faces)

def register():
    bpy.utils.register_class(SvMeshSelectNode)


def unregister():
    bpy.utils.unregister_class(SvMeshSelectNode)



