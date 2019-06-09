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

from math import sin, cos, pi, degrees, radians

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.utils.mesh import *

class SvCircleNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Circle
    Tooltip: Generate a circle
    """
    bl_idname = 'SvCircleNodeMk2'
    bl_label = 'Circle Mk2'
    bl_icon = 'MESH_CIRCLE'

    radius = FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         update=updateNode)
    nverts = IntProperty(name='N Vertices', description='Number of vertices',
                        default=24, min=3,
                        update=updateNode)
    angle = FloatProperty(name='Angle', description='Angle to cover',
                          default=pi*2, min=0, max=pi*2, subtype='ANGLE',
                          update=updateNode)

    cycle_modes = [
            ("sector", "Sector", "Connect first and last vertex through the center, to form a circle sector", 1),
            ("segment", "Segment", "Connect first and last vertex directly, to form a circle segment", 2)
            #("no", "No", "Do not connect first and last vertex (do not produce faces)", 3)
        ]

    cycle_mode = EnumProperty(name = "Cycle mode",
                    description = "How to connect first and last vertex",
                    items = cycle_modes,
                    update = updateNode)

    faces_modes = [
            ("flat", "Flat", "Create single ngon face", 1),
            ("fan", "Fan", "Create fan-like arrangement", 2)
        ]
    
    faces_mode = EnumProperty(name = "Faces mode",
                    description = "Which faces to create",
                    items = faces_modes,
                    update = updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('StringsSocket', "NVertices").prop_name = 'nverts'
        self.inputs.new('StringsSocket', "Angle").prop_name = 'angle'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Faces", "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "cycle_mode", text="Mode")
        layout.prop(self, "faces_mode", text="Mode")

    def make_mesh(self, angle, nverts, radius):
        mesh = Mesh()
        full = angle >= 360
        if not full:
            theta = angle / (nverts - 1)
        else:
            theta = angle / nverts

        outer = []

        for i in range(nverts):
            x = radius * cos(radians(theta*i))
            y = radius * sin(radians(theta*i))
            z = 0
            vertex = mesh.new_vertex((x,y,z))
            outer.append(vertex)

        if self.faces_mode == "flat":
            if self.cycle_mode == "sector" and not full:
                center = mesh.new_vertex((0,0,0))
                outer.append(center)
            mesh.new_face(outer)
        else:
            center = mesh.new_vertex((0,0,0))
            for v1, v2 in zip(outer, outer[1:]):
                mesh.new_face([v1, v2, center])
            if full or self.cycle_mode == "segment":
                mesh.new_face([outer[-1], outer[0], center])

        return mesh

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        radius_s = self.inputs['Radius'].sv_get(deepcopy=False)[0]
        nverts_s = self.inputs['NVertices'].sv_get(deepcopy=False)[0]
        angle_s = self.inputs['Angle'].sv_get(deepcopy=False)[0]

        inputs = match_long_repeat([angle_s, nverts_s, radius_s])

        out_vertices = []
        out_edges = []
        out_faces = []

        for angle, nverts, radius in zip(*inputs):
            mesh = self.make_mesh(angle, nverts, radius)
            vertices = mesh.get_sv_vertices()
            edges = mesh.get_sv_edges()
            faces = mesh.get_sv_faces()
            out_vertices.append(vertices)
            out_edges.append(edges)
            out_faces.append(faces)

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)

def register():
    bpy.utils.register_class(SvCircleNodeMk2)

def unregister():
    bpy.utils.unregister_class(SvCircleNodeMk2)

