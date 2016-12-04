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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle)


class SvVertexGroupNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Vertex Group mk2'''
    bl_idname = 'SvVertexGroupNodeMK2'
    bl_label = 'Vertex group weights'
    bl_icon = 'OUTLINER_OB_EMPTY'

    fade_speed = FloatProperty(name='fade', default=2, update=updateNode)
    clear = BoolProperty(name='clear w', default=True, update=updateNode)
    vertex_group = StringProperty(default='', update=updateNode)
    object_ref = StringProperty(default='', update=updateNode)

    def draw_buttons(self, context,   layout):
        #layout.prop_search(self, 'object_ref', bpy.data, 'objects')
        ob = bpy.data.objects.get(self.object_ref)
        if ob and ob.type == 'MESH':
            layout.prop_search(self, 'vertex_group', ob, "vertex_groups", text="")

    def draw_buttons_ext(self, context, layout):
        row = layout.row(align=True)
        row.prop(self,    "clear",   text="clear unindexed")
        row.prop(self, "fade_speed", text="Clearing speed")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "VertIND")
        self.inputs.new('StringsSocket', "Weights")
        self.inputs.new('SvObjectSocket', "Object")
        self.outputs.new('StringsSocket', "OutWeights")

    def process(self):
        obj = self.inputs['Object'].sv_get()[0]
        print(obj)
        self.object_ref = obj.name
        obj.data.update() 
        Ve, We, Owe = self.inputs[:2] + self.outputs[:]
        if not obj.vertex_groups:
            obj.vertex_groups.new(name='Sv_VGroup')
        if self.vertex_group not in obj.vertex_groups:
            return
        ovgs = obj.vertex_groups.get(self.vertex_group)
        Vi = [i.index for i in obj.data.vertices]
        if Ve.is_linked:
            verts = Ve.sv_get()[0]
        else:
            verts = Vi
        if We.is_linked:
            if self.clear:
                ovgs.add(Vi, self.fade_speed, "SUBTRACT")
            wei = We.sv_get()[0]
            verts, wei = second_as_first_cycle(verts, wei)
            for i, i2 in zip(verts, wei):
                ovgs.add([i], i2, "REPLACE")
        if Owe.is_linked:
            out = []
            for i in verts:
                try:
                    out.append(ovgs.weight(i))
                except Exception:
                    out.append(0.0)
            Owe.sv_set([out])


def register():
    bpy.utils.register_class(SvVertexGroupNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvVertexGroupNodeMK2)

if __name__ == '__main__':
    register()