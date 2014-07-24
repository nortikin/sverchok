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

import bpy
from bpy.props import FloatProperty

from node_tree import SverchCustomTreeNode
from data_structure import SvGetSocketAnyType, SvSetSocketAnyType, updateNode, match_long_repeat


class SvRotateNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Rotate 3D '''
    bl_idname = 'SvRotateNode'
    bl_label = 'Rotate 3D'
    bl_icon = 'OUTLINER_OB_EMPTY'

    angle_ = FloatProperty(name='Angle', description='rotation angle',
                           default=0.0,
                           options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Center", "Center")
        self.inputs.new('VerticesSocket', "Direction", "Direction")
        self.inputs.new('StringsSocket', "Angle", "Angle").prop_name = "angle_"
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def rotation(self, Vertices, Center, Direction, Angle):
        #Getting variables from inputs
        x = Vertices[0]
        y = Vertices[1]
        z = Vertices[2]

        a = Center[0]
        b = Center[1]
        c = Center[2]

        uUn = Direction[0]
        vUn = Direction[1]
        wUn = Direction[2]

        #Making of additional variables
        l = sqrt(uUn**2+vUn**2+wUn**2)
        theta = radians(Angle)

        u = uUn/l
        v = vUn/l
        w = wUn/l

        u2 = u*u
        v2 = v*v
        w2 = w*w
        cosT = cos(theta)
        oneMinusCosT = 1-cosT
        sinT = sin(theta)

        #Making rotation matrix
        m11 = u2 + (v2 + w2) * cosT
        m12 = u*v * oneMinusCosT - w*sinT
        m13 = u*w * oneMinusCosT + v*sinT
        m14 = (a*(v2 + w2) - u*(b*v + c*w))*oneMinusCosT  + (b*w - c*v)*sinT

        m21 = u*v * oneMinusCosT + w*sinT
        m22 = v2 + (u2 + w2) * cosT
        m23 = v*w * oneMinusCosT - u*sinT
        m24 = (b*(u2 + w2) - v*(a*u + c*w))*oneMinusCosT  + (c*u - a*w)*sinT

        m31 = u*w * oneMinusCosT - v*sinT
        m32 = v*w * oneMinusCosT + u*sinT
        m33 = w2 + (u2 + v2) * cosT
        m34 = (c*(u2 + v2) - w*(a*u + b*v))*oneMinusCosT  + (a*v - b*u)*sinT

        #Rotated point
        p0 = m11*x + m12*y + m13*z + m14
        p1 = m21*x + m22*y + m23*z + m24
        p2 = m31*x + m32*y + m33*z + m34

        point = [p0, p1, p2]
        return point

    def vert_rot(self, Vertices, Center, Direction, Angle):
        rotated = []
        for i in Vertices:
            rotated.append(self.rotation(i, Center, Direction, Angle))
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
        if 'Direction' in self.inputs and self.inputs['Direction'].links:
            Direction = SvGetSocketAnyType(self, self.inputs['Direction'])[0]
        else:
            Direction = [[0.0, 0.0, 1.0]]

        parameters = match_long_repeat([Vertices, Center, Direction, Angle])

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
