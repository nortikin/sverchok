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
from bpy.props import FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, numpy_match_long_repeat
from sverchok.utils.sv_itertools import sv_zip_longest
from sverchok.utils.modules.color_utils import hsl_to_rgb, hsv_to_rgb
from numpy import array, stack, zeros

# pylint: disable=w0141

def python_color_pack(i0_g, i1_g, i2_g, i3_g, color_mode, use_alpha):
    series_vec = []
    for i0, i1, i2, i3 in zip(i0_g, i1_g, i2_g, i3_g):

        max_v = max(map(len, (i0, i1, i2, i3)))
        fullList(i0, max_v)
        fullList(i1, max_v)
        fullList(i2, max_v)
        fullList(i3, max_v)

        if color_mode == 'RGB':
            if use_alpha:
                series_vec.append(list(zip(i0, i1, i2, i3)))
            else:
                series_vec.append(list(zip(i0, i1, i2)))
        else:
            if color_mode == 'HSV':
                convert = colorsys.hsv_to_rgb
            elif color_mode == 'HSL':
                convert = lambda h, s, l: colorsys.hls_to_rgb(h, l, s)


            colordata = []
            for c0, c1, c2, c3 in zip(i0, i1, i2, i3):
                colorv = list(convert(c0, c1, c2))
                if use_alpha:
                    colordata.append([colorv[0], colorv[1], colorv[2], c3])
                else:
                    colordata.append(colorv)

            series_vec.append(colordata)
    return series_vec

def numpy_pack_vecs(i0_g, i1_g, i2_g, i3_g, color_mode, use_alpha, output_numpy):
    series_vec = []
    for obj in zip(i0_g, i1_g, i2_g, i3_g):
        np_obj = [array(p) for p in obj]
        x, y, z, alpha = numpy_match_long_repeat(np_obj)
        if color_mode == 'RGB':
            if use_alpha:
                vecs = array([x, y, z, alpha]).T
            else:
                vecs = array([x, y, z]).T
        else:
            if color_mode == 'HSV':
                convert = hsv_to_rgb
            else:
                convert = hsl_to_rgb

            if use_alpha:
                vecs = zeros((x.shape[0],4))
                vecs[:,:3] = convert(array([x, y, z]).T)
                vecs[:,3] = alpha
            else:
                vecs = convert(array([x, y, z]).T)

        series_vec.append(vecs if output_numpy else vecs.tolist())
    return series_vec


def fprop_generator(**altprops):
    # min can be overwritten by passing in min=some_value into the altprops dict
    default_dict_vals = dict(update=updateNode, precision=3, min=0.0, max=1.0)
    default_dict_vals.update(**altprops)
    return FloatProperty(**default_dict_vals)


class SvColorsInNodeMK1(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: rgb, hsv, hsl -> color
    Tooltip: Generator for Color data from color components

    """
    bl_idname = 'SvColorsInNodeMK1'
    bl_label = 'Color in'
    bl_icon = 'COLOR'
    sv_icon = 'SV_COLOR_IN'

    def psuedo_update(self, context):
        for idx, socket in enumerate(self.selected_mode):
            self.inputs[idx].name = socket
            self.inputs[idx].prop_name = socket.lower() + '_'
        updateNode(self, context)

    use_alpha: BoolProperty(name='Use Alpha', default=True, update=updateNode)

    r_: fprop_generator(name='R', description='Red (0..1)')
    g_: fprop_generator(name='G', description='Green (0..1)')
    b_: fprop_generator(name='B', description='Blue (0..1)')
    a_: fprop_generator(name='A', description='Alpha (0..1) - opacity', default=1.0)

    h_: fprop_generator(name='H', description='Hue (0..1)')
    s_: fprop_generator(name='S', description='Saturation (0..1) - different for hsv and hsl')
    l_: fprop_generator(name='L', description='Lightness / Brightness (0..1)')
    v_: fprop_generator(name='V', description='Value / Brightness (0..1)')

    mode_options = [
        ("RGB", "RGB", "", 0),
        ("HSV", "HSV", "", 1),
        ("HSL", "HSL", "", 2),
    ]

    selected_mode: bpy.props.EnumProperty(
        default="RGB", description="offers color spaces",
        items=mode_options, update=psuedo_update
    )
    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation: bpy.props.EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method',
        default="NumPy", update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'selected_mode', expand=True)
        layout.prop(self, 'use_alpha')

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, "selected_mode", expand=True)
        layout.label(text="Implementation:")
        layout.prop(self, "implementation", expand=True)
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "selected_mode", text="Color Space")
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == "NumPy":
            layout.prop(self, "output_numpy", toggle=True)

    def sv_init(self, context):
        self.width = 110
        inew = self.inputs.new
        inew('SvStringsSocket', "R").prop_name = 'r_'
        inew('SvStringsSocket', "G").prop_name = 'g_'
        inew('SvStringsSocket', "B").prop_name = 'b_'
        inew('SvStringsSocket', "A").prop_name = 'a_'
        onew = self.outputs.new
        onew('SvColorSocket', "Colors")

    def process(self):

        if not self.outputs['Colors'].is_linked:
            return
        inputs = self.inputs

        i0_g = inputs[0].sv_get()
        i1_g = inputs[1].sv_get()
        i2_g = inputs[2].sv_get()
        i3_g = inputs[3].sv_get()

        series_vec = []
        max_obj = max(map(len, (i0_g, i1_g, i2_g, i3_g)))
        fullList(i0_g, max_obj)
        fullList(i1_g, max_obj)
        fullList(i2_g, max_obj)
        fullList(i3_g, max_obj)
        if self.implementation == 'Python':
            series_vec = python_color_pack(i0_g, i1_g, i2_g, i3_g, self.selected_mode, self.use_alpha)
        else:
            series_vec = numpy_pack_vecs(i0_g, i1_g, i2_g, i3_g, self.selected_mode, self.use_alpha, self.output_numpy)
        self.outputs['Colors'].sv_set(series_vec)


def register():
    bpy.utils.register_class(SvColorsInNodeMK1)


def unregister():
    bpy.utils.unregister_class(SvColorsInNodeMK1)
