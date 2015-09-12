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
from bpy.props import FloatProperty, BoolProperty, EnumProperty

from sverchok.data_structure import updateNode
from sverchok.node_tree import SverchCustomTreeNode

from sverchok.utils.sv_easing_functions import *
# star imports easing_dict and all easing functions.

easing_list = []
for k in sorted(easing_dict.keys()):
    fname = easing_dict[k].__name__
    easing_list.append(tuple([str(k), fname, "", k]))


class SvEasingNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvEasingNode'
    bl_label = 'Easing'

    selected_mode = EnumProperty(
        items=easing_list,
        description="offers easing choice",
        default="0",
        update=updateNode
    )

    def draw_buttons(self, context, l):
        c = l.column()
        c.label(text="set easing function")
        c.prop(self, "selected_mode", text="")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'float'
        self.outputs.new('StringsSocket', "Float")

    def process(self):
        p = self.inputs['Float'].sv_get()

        float_out = self.outputs['Float']
        if float_out.is_linked:
            out = []
            for obj in p:
                r = []
                for i in obj:
                    easing_func = easing_dict.get(int(self.selected_mode))
                    r.append(easing_func(i))
                out.append(r)
            float_out.sv_set(out)
        else:
            float_out.sv_set([[None]])


def register():
    bpy.utils.register_class(SvEasingNode)


def unregister():
    bpy.utils.unregister_class(SvEasingNode)
