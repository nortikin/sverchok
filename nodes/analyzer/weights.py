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
import parser
from bpy.props import StringProperty, BoolProperty, EnumProperty, FloatProperty
from node_tree import SverchCustomTreeNode, StringsSocket
from data_structure import (SvGetSocketAnyType, updateNode, match_short,
                            match_long_cycle)


class SvVertexGroupNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Group '''
    bl_idname = 'SvVertexGroupNode'
    bl_label = 'weights'
    bl_icon = 'OUTLINER_OB_EMPTY'

    Itermodes = [
        ("match_short",        "match_short",         "", 1),
        ("match_long_cycle",   "match_long_cycle",    "", 2),
    ]

    Iteration = EnumProperty(name="iteration modes",
                             description="Iteration modes",
                             default="match_short", items=Itermodes,
                             update=updateNode)
    formula = StringProperty(name='formula',
                             description='name of object to operate on',
                             default='Cube', update=updateNode)
    fade_speed = FloatProperty(name='fade',
                               description='Speed of "clear unused" weights \
                               during animation', default=2,
                               options={'ANIMATABLE'}, update=updateNode)
    clear = BoolProperty(name='clear unused', description='clear weight of \
                         unindexed vertices', default=True, update=updateNode)

    def draw_buttons(self, context,   layout):
        layout.prop(self,  "formula", text="")
        row = layout.row(align=True)
        row.prop(self,    "clear",   text="clear unused")
        layout.prop(self, "Iteration", "Iteration modes")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "fade_speed", text="Clearing speed")

    def init(self, context):
        self.inputs.new('StringsSocket', "VertIND")
        self.inputs.new('StringsSocket', "Weights")

    def update(self):

        if not (self.formula in bpy.data.objects):
            return

        if not ('Weights' in self.inputs):
            return

        vertex_weight = self.inputs['Weights'].links
        if not (vertex_weight and (type(vertex_weight[0].from_socket) ==
                StringsSocket)):
            return

        self.process()

    def process(self):
        obj = bpy.data.objects[self.formula]

        if self.inputs['VertIND'].links:
            verts = SvGetSocketAnyType(self, self.inputs['VertIND'])[0]
        else:
            verts = [i.index for i in obj.data.vertices]

        wei = SvGetSocketAnyType(self, self.inputs['Weights'])[0]

        if self.Iteration == 'match_short':
            temp = match_short([verts, wei])
            verts, wei = temp[0], temp[1]
        if self.Iteration == 'match_long_cycle':
            temp = match_long_cycle([verts, wei])
            verts, wei = temp[0], temp[1]

        obj.data.update()
        if obj.vertex_groups.active and\
           obj.vertex_groups.active.name.find('Sv_VGroup') != -1:

            if self.clear:
                obj.vertex_groups.active.add([i.index for i in
                                              obj.data.vertices],
                                             self.fade_speed, "SUBTRACT")
            g = 0
            while g != len(wei):
                obj.vertex_groups.active.add([verts[g]], wei[g], "REPLACE")
                g = g+1

        else:
            obj.vertex_groups.active = obj.vertex_groups.new(name='Sv_VGroup')

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvVertexGroupNode)


def unregister():
    bpy.utils.unregister_class(SvVertexGroupNode)
