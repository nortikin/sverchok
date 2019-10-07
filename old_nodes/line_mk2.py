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
from sverchok.data_structure import updateNode, fullList, match_long_repeat

directionItems = [("X", "X", ""), ("Y", "Y", ""), ("Z", "Z", "")]


def make_line(steps, center, direction):
    if direction == "X":
        v = lambda l: (l, 0.0, 0.0)
    elif direction == "Y":
        v = lambda l: (0.0, l, 0.0)
    elif direction == "Z":
        v = lambda l: (0.0, 0.0, l)

    verts = []
    addVert = verts.append
    x = -sum(steps) / 2 if center else 0
    for s in [0.0] + steps:
        x = x + s
        addVert(v(x))
    edges = [[i, i + 1] for i in range(len(steps))]
    return verts, edges


class SvLineNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Line MK2'''
    bl_idname = 'SvLineNodeMK2'
    bl_label = 'Line MK2'
    bl_icon = 'GRIP'

    replacement_nodes = [('SvLineNodeMK3', None, None)]
    
    def upgrade_if_needed(self):
        """ This allows us to keep the node mk2 - on the fly node upgrade"""
        if "Size" not in self.inputs:
            size_socket = self.inputs.new('StringsSocket', "Size")
            size_socket.prop_name = 'size'
            size_socket.hide_safe = not self.normalize

    def wrapped_update(self, context):
        """ need to do UX transformation before updating node"""
        self.upgrade_if_needed()
        size_socket = self.inputs["Size"]
        size_socket.hide_safe = not self.normalize
        updateNode(self, context)


    direction = EnumProperty(
        name="Direction", items=directionItems,
        default="X", update=updateNode)

    num = IntProperty(
        name='Num Verts', description='Number of Vertices',
        default=2, min=2, update=updateNode)

    step = FloatProperty(
        name='Step', description='Step length',
        default=1.0, update=updateNode)

    center = BoolProperty(
        name='Center', description='Center the line',
        default=False, update=updateNode)

    normalize = BoolProperty(
        name='Normalize', description='Normalize line to size',
        default=False, update=wrapped_update)

    size = FloatProperty(
        name='Size', description='Size of line',
        default=10.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Num").prop_name = 'num'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step'
        size_socket = self.inputs.new('StringsSocket', "Size")
        size_socket.prop_name = 'size'
        size_socket.hide_safe = True
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)


    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        input_num = self.inputs["Num"].sv_get()
        input_step = self.inputs["Step"].sv_get()
        c, d = self.center, self.direction
        stepList = []
        res1,res2 = [],[]

        normal_size = 1.0
        if self.normalize:
            self.upgrade_if_needed()
            normal_size = self.inputs["Size"].sv_get()[0][0]

        for n, s in zip(*match_long_repeat([input_num, input_step])):
            for num in n:
                num = max(2,num)
                s = s[:(num - 1)]  # shorten if needed
                fullList(s, num - 1)  # extend if needed
                stepList.append([S * normal_size / sum(s) for S in s] if self.normalize else s)
        for s in stepList:
            r1,r2 = make_line(s, c, d)
            res1.append(r1)
            res2.append(r2)
        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(res1)
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(res2)


def register():
    bpy.utils.register_class(SvLineNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK2)
