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
from bpy.props import StringProperty, EnumProperty, BoolProperty

from node_tree import SverchCustomTreeNode
from data_structure import updateNode, SvSetSocketAnyType, SvGetSocketAnyType, match_long_repeat, dataCorrect


def mirror(vertex, center, axis):
    mirrored = []
    vertex = dataCorrect(vertex, nominal_dept=2)
    for i in vertex:
        tmp = []
        for j in i:
            v = Vector(j).reflect(axis)
            c = Vector((center[0]*axis[0], center[1]*axis[1], center[2]*axis[2]))
            tmp.append((v+2*c)[:])
        mirrored.append(tmp)
    return mirrored

def axis_mirror(vertex, center, axis):
    axis_mirrored = [[vertex]]
    axis = Vector(axis)
    center = Vector(center)
    if axis[0] == True:
        x =  mirror(axis_mirrored, center, (1.0, 0.0, 0.0))
        axis_mirrored.append(x)
        if axis[1] == True:
            y =  mirror(axis_mirrored, center, (0.0, 1.0, 0.0))
            axis_mirrored.append(y)
            if axis[2] == True:
                z =  mirror(axis_mirrored, center, (0.0, 0.0, 1.0))
                axis_mirrored.append(z)
        elif axis[2] == True:
            z =  mirror(axis_mirrored, center, (0.0, 0.0, 1.0))
            axis_mirrored.append(z)
    elif axis[1] == True:
        y =  mirror(axis_mirrored, center, (0.0, 1.0, 0.0))
        axis_mirrored.append(y)
        if axis[2] == True:
            z =  mirror(axis_mirrored, center, (0.0, 0.0, 1.0))
            axis_mirrored.append(z)
    elif axis[2] == True:
        z =  mirror(axis_mirrored, center, (0.0, 0.0, 1.0))
        axis_mirrored.append(z)
    return axis_mirrored

class SvMirrorNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Mirroring  '''

    bl_idname = 'SvMirrorNode'
    bl_label = 'Mirror'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self, context):
        self.current_axis = ((0.0, 0.0, 0.0))
        if self.x_mirror == True:
            self.current_axis[0] = 1.0
        if self.y_mirror == True:
            self.current_axis[1] = 1.0
        if self.z_mirror == True:
            self.current_axis[2] = 1.0
        updateNode(self, context)

    current_axis = FloatVectorProperty(name="current_axis", default=(1.0, 0.0, 0.0))

    x_mirror = BoolProperty(name="X", description="X mirror",
                            default=True,   update=mode_change)
    y_mirror = BoolProperty(name="Y", description="Y mirror",
                            update=mode_change)
    z_mirror = BoolProperty(name="Z", description="Z mirror",
                            update=mode_change)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('VerticesSocket', "Center", "Center")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "x_mirror", toggle=True)
        row.prop(self, "y_mirror", toggle=True)
        row.prop(self, "z_mirror", toggle=True)

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

        parameters = match_long_repeat([Vertices, Center, [self.current_axis]])

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            points = dataCorrect([axis_mirror(v, c, a) for v, c, a in zip(*parameters)])
            SvSetSocketAnyType(self, 'Vertices', points)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMirrorNode)


def unregister():
    bpy.utils.unregister_class(SvMirrorNode)
