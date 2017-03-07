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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList

directionItems = [("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")]


def make_line(steps, center, direction):
    if direction == "X":
        v = lambda l: (l, 0.0, 0.0)
    elif direction == "Y":
        v = lambda l: (0.0, l, 0.0)
    elif direction == "Z":
        v = lambda l: (0.0, 0.0, l)

    ss = -sum(steps) / 2 if center else 0
    verts = [v(ss)]  # starting vertex
    for s in steps:
        ss = ss + s
        verts.append(v(ss))

    edges = [[i, i + 1] for i in range(len(steps))]

    return verts, edges


class SvLineNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Line MK2'''
    bl_idname = 'SvLineNodeMK2'
    bl_label = 'Line MK2'
    bl_icon = 'GRIP'

    direction = EnumProperty(name="Direction",
                             default="X", items=directionItems,
                             update=updateNode)

    num = IntProperty(name='Num Verts', description='Number of Vertices',
                      default=2, min=2, options={'ANIMATABLE'},
                      update=updateNode)

    step = FloatProperty(name='Step', description='Step length',
                         default=1.0, options={'ANIMATABLE'},
                         update=updateNode)

    center = BoolProperty(name='Center', description='Center the line',
                          default=False,
                          update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Num").prop_name = 'num'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        layout.prop(self, "direction", expand=True)
        layout.prop(self, "center")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        n = self.inputs["Num"].sv_get()[0][0]
        input_step = self.inputs["Step"].sv_get()[0]

        # sanitize the inputs
        n = max(2, n)

        # adjust the step list based on number of verts and steps
        input_step = input_step[:(n - 1)]
        fullList(input_step, n - 1)

        verts, edges = make_line(input_step, self.center, self.direction)

        # outputs
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set([verts])

        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set([edges])


def register():
    bpy.utils.register_class(SvLineNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK2)
