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

from mathutils import Vector

import bpy
from bpy.props import FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvGetSocketAnyType, SvSetSocketAnyType, updateNode, match_long_repeat


class SvScaleNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Scale '''
    bl_idname = 'SvScaleNode'
    bl_label = 'Scale'
    bl_icon = 'OUTLINER_OB_EMPTY'

    factor_ = FloatProperty(name='Factor', description='scaling factor',
                           default=1.0,
                           options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Center", "Center")
        self.inputs.new('StringsSocket', "Factor", "Factor").prop_name = "factor_"
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def scaling(self, vertex, center, factor):
        pt = Vector(vertex)
        c = Vector(center)
        return (c + factor*(pt-c))[:]

    def vert_scl(self, vertex, center, factor):
        scaled = []
        for i in vertex:
            scaled.append(self.scaling(i, center, factor))
        return scaled
  
    def update(self):
        # inputs
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            Vertices = SvGetSocketAnyType(self, self.inputs['Vertices'])
        else:
            Vertices = []
        if 'Center' in self.inputs and self.inputs['Center'].links:
            Center = SvGetSocketAnyType(self, self.inputs['Center'])[0]
        else:
            Center = [[0.0, 0.0, 0.0]]
        if 'Factor' in self.inputs and self.inputs['Factor'].links:
            Factor = SvGetSocketAnyType(self, self.inputs['Factor'])[0]
        else:
            Factor = [self.factor_]

        parameters = match_long_repeat([Vertices, Center, Factor])

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            points = [self.vert_scl(v, c, f) for v, c, f in zip(*parameters)]
            SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvScaleNode)


def unregister():
    bpy.utils.unregister_class(SvScaleNode)
