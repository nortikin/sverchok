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

import bpy
import mathutils
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import (updateNode, Vector_generate)


class SvPointOnMeshNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Point on Mesh '''
    bl_idname = 'SvPointOnMeshNode'
    bl_label = 'closest_point_on_mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Mdist = FloatProperty(name='Max_Distance',
                               description='from surface to point', default=10,
                               options={'ANIMATABLE'}, update=updateNode)
    mode = BoolProperty(name='mode of points', description='mode for input points',
                        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('VerticesSocket', "point").use_prop = True
        self.inputs.new('StringsSocket', "max_dist").prop_name = "Mdist"
        self.outputs.new('VerticesSocket', "Point_on_mesh")
        self.outputs.new('VerticesSocket', "Normal_on_mesh")
        self.outputs.new('StringsSocket', "INDEX")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "mode",   text="Mode")

    def process(self):

        Location = []
        Normal = []
        Index = []
        point = Vector_generate(self.inputs['point'].sv_get())
        point = [Vector(x) for x in point[0]]
        max_dist = self.inputs['max_dist'].sv_get()[0][0]
        obj = self.inputs['Object'].sv_get()

        for i in obj:

            if self.mode:
                pnt = [i.closest_point_on_mesh(i.matrix_local.inverted()*p, max_dist) for p in point]
            else:
                pnt = [i.closest_point_on_mesh(p, max_dist) for p in point]

            for i2 in pnt:

                Location.append((i.matrix_world*i2[0])[:])
                Normal.append(i2[1][:])
                Index.append(i2[2])

        self.outputs['Point_on_mesh'].sv_set([Location])
        self.outputs['Normal_on_mesh'].sv_set([Normal])
        self.outputs['INDEX'].sv_set([Index])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvPointOnMeshNode)


def unregister():
    bpy.utils.unregister_class(SvPointOnMeshNode)
