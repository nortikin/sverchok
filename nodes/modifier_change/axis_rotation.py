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

from math import cos, sin, sqrt, radians

from mathutils import Matrix, Vector

import bpy
from bpy.props import FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvGetSocketAnyType, SvSetSocketAnyType, updateNode, match_long_repeat


class SvRotateNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Axis Rotation '''
    bl_idname = 'SvRotateNode'
    bl_label = 'Axis Rotation'
    bl_icon = 'OUTLINER_OB_EMPTY'

    angle_ = FloatProperty(name='Angle', description='rotation angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Center", "Center")
        self.inputs.new('VerticesSocket', "Axis", "Axis")
        self.inputs.new('StringsSocket', "Angle", "Angle").prop_name = "angle_"
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def rotation(self, vertex, center, axis, angle):
        mat = Matrix.Rotation(radians(angle), 4,  axis)
        c = Vector(center)
        pt = Vector(vertex)
        return (c + mat * ( pt - c))[:]

    def vert_rot(self, vertices, center, axis, angle):
        rotated = []
        for i in vertices:
            rotated.append(self.rotation(i, center, axis, angle))
        return rotated
  
    def update(self):
        # inputs
        if 'Angle' in self.inputs and self.inputs['Angle'].links:
            Angle = SvGetSocketAnyType(self, self.inputs['Angle'])[0]
        else:
            Angle = [self.angle_]
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            Vertices = SvGetSocketAnyType(self, self.inputs['Vertices'])
        else:
            Vertices = []
        if 'Center' in self.inputs and self.inputs['Center'].links:
            Center = SvGetSocketAnyType(self, self.inputs['Center'])[0]
        else:
            Center = [[0.0, 0.0, 0.0]]
        if 'Axis' in self.inputs and self.inputs['Axis'].links:
            Axis = SvGetSocketAnyType(self, self.inputs['Axis'])[0]
        else:
            Axis = [[0.0, 0.0, 1.0]]

        parameters = match_long_repeat([Vertices, Center, Axis, Angle])

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            points = [self.vert_rot(v, c, d, a) for v, c, d, a in zip(*parameters)]
            SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRotateNode)


def unregister():
    bpy.utils.unregister_class(SvRotateNode)
