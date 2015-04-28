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
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvFilterObjsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Filter Objects '''
    bl_idname = 'SvFilterObjsNode'
    bl_label = 'filter_dataobject'
    bl_icon = 'OUTLINER_OB_EMPTY'

    formula = StringProperty(name='formula', default='name', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', 'Objects')
        self.outputs.new('StringsSocket', 'Objects')

    def draw_buttons(self, context, layout):
        layout.prop(self,  "formula", text="")

    def process(self):
        out = []
        if self.outputs['Objects'].is_linked:
            for i in self.inputs['Objects'].sv_get():
                if self.formula in i.name:
                    out.append(i)

            self.outputs['Objects'].sv_set(out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvFilterObjsNode)


def unregister():
    bpy.utils.unregister_class(SvFilterObjsNode)
