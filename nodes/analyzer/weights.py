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
from bpy.props import StringProperty, BoolProperty, FloatProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket
from sverchok.data_structure import (updateNode, match_long_cycle)


class SvVertexGroupNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Group '''
    bl_idname = 'SvVertexGroupNode'
    bl_label = 'Vertex group weights'
    bl_icon = 'OUTLINER_OB_EMPTY'

    fade_speed = FloatProperty(name='fade',
                               description='Speed of "clear unused" weights \
                               during animation', default=2,
                               options={'ANIMATABLE'}, update=updateNode)
    clear = BoolProperty(name='clear unused', description='clear weight of \
                         unindexed vertices', default=True, update=updateNode)

    vertex_group = StringProperty(
        default='',
        description='vert group',
        update=updateNode)

    def draw_buttons(self, context,   layout):

        ob = self.inputs['Objects'].sv_get()[0]
        col = layout.column()
        if self.inputs['Objects'].sv_get()[0].type == 'MESH':
            col.prop_search(self, 'vertex_group', ob, "vertex_groups", text="")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "clear",   text="clear unused")
        row.prop(self, "fade_speed", text="Clearing speed")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('StringsSocket', "VertIND")
        self.inputs.new('StringsSocket', "Weights")
        self.outputs.new('StringsSocket', "OutWeights")

    def process(self):

        obj = self.inputs['Objects'].sv_get()[0]
        obj.data.update()
        if not obj.vertex_groups:
            obj.vertex_groups.new(name='Sv_VGroup')
        if self.vertex_group not in obj.vertex_groups:
            return

        ovgs = obj.vertex_groups.get(self.vertex_group)
        vind = [i.index for i in obj.data.vertices]

        if self.inputs['VertIND'].is_linked:
            verts = self.inputs['VertIND'].sv_get()[0]
        else:
            verts = vind

        if self.inputs['Weights'].is_linked:
            wei = self.inputs['Weights'].sv_get()[0]
            lv = len(verts)
            if lv > len(wei):
                temp = match_long_cycle([verts, wei])
                verts, wei = temp[0], temp[1]

            if self.clear:
                ovgs.add(vind, self.fade_speed, "SUBTRACT")
            g = 0
            while g != lv:
                ovgs.add([verts[g]], wei[g], "REPLACE")
                g = g+1

        if self.outputs['OutWeights'].is_linked:
            out = []
            for i in verts:
                try:
                    out.append(ovgs.weight(i))
                except Exception:
                    out.append(0.0)
            self.outputs['OutWeights'].sv_set([out])


def register():
    bpy.utils.register_class(SvVertexGroupNode)


def unregister():
    bpy.utils.unregister_class(SvVertexGroupNode)
