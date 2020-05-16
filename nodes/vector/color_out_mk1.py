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
from mathutils import Color

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, fullList, dataCorrect, dataCorrect_np
from sverchok.utils.sv_itertools import sv_zip_longest
from sverchok.utils.modules.color_utils import rgb_to_hsv, rgb_to_hsl
from numpy import ndarray, array

# pylint: disable=w0141
def unpack_np(obj):
    return (obj[:, i] for i in range(obj.shape[1]))

def unpack_list(obj):
    return (list(x) for x in zip(*obj))

def unpack_list_to_np(obj):
    return (array(x) for x in zip(*obj))


class SvColorsOutNodeMK1(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: col -> rgb, hsv, hsl
    Tooltip: Generator for Color data from color components

    """
    bl_idname = 'SvColorsOutNodeMK1'
    bl_label = 'Color Out'
    bl_icon = 'COLOR'
    sv_icon = 'SV_COLOR_OUT'

    def psuedo_update(self, context):
        for idx, socket in enumerate(self.selected_mode):
            self.outputs[idx].name = socket
        updateNode(self, context)
    mode_options = [
        ("RGB", "RGB", "", 0),
        ("HSV", "HSV", "", 1),
        ("HSL", "HSL", "", 2),
    ]

    selected_mode: bpy.props.EnumProperty(
        default="RGB", description="offers color spaces",
        items=mode_options, update=psuedo_update
    )
    unit_color: FloatVectorProperty(
        update=updateNode, name='', default=(.3, .3, .2, 1.0),
        size=4, min=0.0, max=1.0, subtype='COLOR'
    )

    # use_alpha: BoolProperty(default=False, update=updateNode)
    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.width = 110
        inew = self.inputs.new
        # inew('SvColorSocket', "Colors").prop_name = "unit_color"
        inew('SvColorSocket', "Colors").custom_draw = 'draw_color_socket'
        onew = self.outputs.new
        onew('SvStringsSocket', "R")
        onew('SvStringsSocket', "G")
        onew('SvStringsSocket', "B")
        onew('SvStringsSocket', "A")

    def draw_color_socket(self, socket, context, layout):
        if not socket.is_linked:
            layout.prop(self, 'unit_color', text="")

        else:

            layout.label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
    def draw_buttons(self, context, layout):
        layout.prop(self, 'selected_mode', expand=True)
        # layout.prop(self, 'use_alpha')

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, 'selected_mode', expand=True)
        # layout.prop(self, 'use_alpha')
        layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "selected_mode", text="Function")
        # layout.prop(self, 'use_alpha')
        layout.prop(self, "output_numpy", toggle=True)
    def process(self):

        color_input = self.inputs['Colors']
        if color_input.is_linked:
            abc = self.inputs['Colors'].sv_get()
            data = dataCorrect_np(abc)
        else:
            data = [[self.unit_color[:]]]

        if self.output_numpy:
            unpack_func = unpack_np if isinstance(data[0], ndarray) else unpack_list_to_np
        else:
            unpack_func = unpack_list

        if self.selected_mode == 'HSV':
            transform_func = rgb_to_hsv
        elif self.selected_mode == 'HSL':
            transform_func = rgb_to_hsl

        out = [[] for s in self.outputs]
        for obj in data:
            if not self.selected_mode == 'RGB':
                cols = transform_func(array(obj))
                obj_cols = unpack_func(cols)
            else:
                obj_cols = unpack_func(obj)
            for i, col in enumerate(obj_cols):
                out[i].append(col)

        for i, socket in enumerate(self.outputs[:len(data[0][0])]):
            self.outputs[socket.name].sv_set(out[i])


def register():
    bpy.utils.register_class(SvColorsOutNodeMK1)


def unregister():
    bpy.utils.unregister_class(SvColorsOutNodeMK1)
