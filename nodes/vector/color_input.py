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

import colorsys
import bpy
from bpy.props import FloatProperty, BoolProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList
from sverchok.utils.sv_itertools import sv_zip_longest
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties


class SvColorInputNode(Show3DProperties, bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Color Input
    Tooltip: Specify color using color picker
    """
    bl_idname = "SvColorInputNode"
    bl_label = "Color Input"
    bl_icon = "COLOR"

    use_alpha: BoolProperty(name="Use Alpha", default=False, update=updateNode)

    color_data: FloatVectorProperty(
        name="Color", description="Color", size=4,
        min=0.0, max=1.0, subtype='COLOR', update=updateNode)

    def sv_init(self, context):
        self.outputs.new("SvColorSocket", "Color")

    def draw_buttons(self, context, layout):
        layout.template_color_picker(self, "color_data", value_slider=True)
        layout.prop(self, "color_data", text='')
        layout.prop(self, "use_alpha")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "draw_3dpanel")

    def draw_buttons_3dpanel(self, layout):
        row = layout.row(align=True)
        row.label(text=self.label if self.label else self.name)
        row.prop(self, 'color_data', text='')

    def process(self):
        if self.use_alpha:
            color = self.color_data[:]
        else:
            color = self.color_data[:3]

        self.outputs['Color'].sv_set([[color]])

def register():
    bpy.utils.register_class(SvColorInputNode)


def unregister():
    bpy.utils.unregister_class(SvColorInputNode)
