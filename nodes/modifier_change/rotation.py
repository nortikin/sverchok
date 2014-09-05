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

from math import radians

from mathutils import Matrix, Vector, Euler, Quaternion

import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty

from node_tree import SverchCustomTreeNode
from data_structure import (SvGetSocketAnyType, SvSetSocketAnyType,
                            updateNode, match_long_repeat)


def axis_rotation(vertex, center, axis, angle):
    mat = Matrix.Rotation(radians(angle), 4,  axis)
    c = Vector(center)
    rotated = [ (c + mat * ( Vector(i) - c))[:] for i in vertex ]
    return rotated

def euler_rotation(vertex, x, y, z, order):
    rotated = []
    mat_eul = Euler((radians(x), radians(y), radians(z)), order).to_matrix().to_4x4()
    for i in vertex:
        v = Vector(i)
        rotated.append((mat_eul*v)[:])
    return rotated

def quat_rotation(vertex, x, y, z, w):
    rotated = []
    quat = Quaternion((w, x, y, z)).normalized()
    for i in vertex:
        v = Vector(i)
        rotated.append((quat*v)[:])
    return rotated

class SvRotationNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Axis Rotation '''
    bl_idname = 'SvRotationNode'
    bl_label = 'Rotation'
    bl_icon = 'OUTLINER_OB_EMPTY'

    angle_ = FloatProperty(name='Angle', description='rotation angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    x_ = FloatProperty(name='X', description='X angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    y_ = FloatProperty(name='Y', description='Y angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    z_ = FloatProperty(name='Z', description='Z angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)
    w_ = FloatProperty(name='W', description='W',
                           default=1.0,
                           options={'ANIMATABLE'}, update=updateNode)

    current_mode = StringProperty(default="AXIS")

    def mode_change(self, context):
        # just because click doesn't mean we need to change mode
        mode = self.mode
        if mode == self.current_mode:
            return

        while len(self.inputs) > 1:
            self.inputs.remove(self.inputs[-1])

        if mode == 'AXIS':
            self.inputs.new('VerticesSocket', "Center", "Center")
            self.inputs.new('VerticesSocket', "Axis", "Axis")
            self.inputs.new('StringsSocket', "Angle", "Angle").prop_name = "angle_"
        elif mode == 'EULER' or mode == 'QUAT':
            self.inputs.new('StringsSocket', "X", "X").prop_name = "x_"
            self.inputs.new('StringsSocket', "Y", "Y").prop_name = "y_"
            self.inputs.new('StringsSocket', "Z", "Z").prop_name = "z_"
            if mode == 'QUAT':
                self.inputs.new('StringsSocket', "W", "W").prop_name = "w_"

        self.current_mode = mode
        updateNode(self, context)

    modes = [
        ("AXIS", "Axis", "Axis and angle rotation", 1),
        ("EULER", "Euler", "Euler Rotation", 2),
        ("QUAT", "Quat", "Quaternion Rotation", 3),
    ]

    mode = EnumProperty(name="mode", description="mode",
                          default='AXIS', items=modes,
                          update=mode_change)

    orders = [
        ('XYZ', "XYZ",        "", 0),
        ('XZY', 'XZY',        "", 1),
        ('YXZ', 'YXZ',        "", 2),
        ('YZX', 'YZX',        "", 3),
        ('ZXY', 'ZXY',        "", 4),
        ('ZYX', 'ZYX',        "", 5),
    ]
    order = EnumProperty(name="Order", description="Order",
                          default="XYZ", items=orders,
                          update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Center", "Center")
        self.inputs.new('VerticesSocket', "Axis", "Axis")
        self.inputs.new('StringsSocket', "Angle", "Angle").prop_name = "angle_"
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        if self.mode == 'EULER':
            layout.prop(self, "order", text="Order:")

    def update(self):
        # inputs
        if self.mode == 'AXIS':
            if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
                Vertices = SvGetSocketAnyType(self, self.inputs['Vertices'])
            else:
                Vertices = []
            if 'Angle' in self.inputs and self.inputs['Angle'].links:
                Angle = SvGetSocketAnyType(self, self.inputs['Angle'])[0]
            else:
                Angle = [self.angle_]
            if 'Center' in self.inputs and self.inputs['Center'].links:
                Center = SvGetSocketAnyType(self, self.inputs['Center'])[0]
            else:
                Center = [[0.0, 0.0, 0.0]]
            if 'Axis' in self.inputs and self.inputs['Axis'].links:
                Axis = SvGetSocketAnyType(self, self.inputs['Axis'])[0]
            else:
                Axis = [[0.0, 0.0, 1.0]]

            parameters = match_long_repeat([Vertices, Center, Axis, Angle])

        elif self.mode == 'EULER' or self.mode == 'QUAT':
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

            parameters = match_long_repeat([Vertices, X, Y, Z, [self.order]])

            if self.mode == 'QUAT':
                if 'W' in self.inputs and self.inputs['W'].links:
                    W = SvGetSocketAnyType(self, self.inputs['W'])[0]
                else:
                    W = [self.w_]

                parameters = match_long_repeat([Vertices, X, Y, Z, W])

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            if self.mode == 'AXIS':
                points = [axis_rotation(v, c, d, a) for v, c, d, a in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)
            elif self.mode == 'EULER':
                points = [euler_rotation(v, x, y, z, o) for v, x, y, z, o in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)
            elif self.mode == 'QUAT':
                points = [quat_rotation(m, x, y, z, w) for m, x, y, z, w in zip(*parameters)]
                SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRotationNode)


def unregister():
    bpy.utils.unregister_class(SvRotationNode)

if __name__ == '__main__':
    register()
