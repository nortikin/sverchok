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

from mathutils import Euler, Vector, Matrix

import bpy
from bpy.props import FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvGetSocketAnyType, SvSetSocketAnyType, updateNode, match_long_repeat


class SvEulerRotationNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Euler Rotation '''
    bl_idname = 'SvEulerRotationNode'
    bl_label = 'Euler Rotation'
    bl_icon = 'OUTLINER_OB_EMPTY'

    x_ = FloatProperty(name='X', description='X angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    y_ = FloatProperty(name='Y', description='Y angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    z_ = FloatProperty(name='Z', description='Z angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "X", "X").prop_name = "x_"
        self.inputs.new('StringsSocket', "Y", "Y").prop_name = "y_"
        self.inputs.new('StringsSocket', "Z", "Z").prop_name = "z_"
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def rotation(self, vertex, x, y, z):
        mat_eul = Euler((radians(x), radians(y), radians(z)), 'XYZ').to_matrix()
        v = Vector(vertex)
        return (v*mat_eul)[:]

    def vert_rot(self, vertices, x, y, z):
        rotated = []
        for i in vertices:
            rotated.append(self.rotation(i, x, y, z))
        return rotated
  
    def update(self):
        # inputs
        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            Vertices = SvGetSocketAnyType(self, self.inputs['Vertices'])
        else:
            Vertices = []
        if 'X' in self.inputs and self.inputs['X'].links:
            X = SvGetSocketAnyType(self, self.inputs['X'])[0]
        else:
            X = [self.x_]
        if 'Y' in self.inputs and self.inputs['Y'].links:
            Y = SvGetSocketAnyType(self, self.inputs['Y'])[0]
        else:
            Y = [self.y_]
        if 'Z' in self.inputs and self.inputs['Z'].links:
            Z = SvGetSocketAnyType(self, self.inputs['Z'])[0]
        else:
            Z = [self.z_]

        parameters = match_long_repeat([Vertices, X, Y, Z])

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            points = [self.vert_rot(v, x, y, z) for v, x, y, z in zip(*parameters)]
            SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvEulerRotationNode)


def unregister():
    bpy.utils.unregister_class(SvEulerRotationNode)
