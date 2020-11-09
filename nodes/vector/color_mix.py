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
from bpy.props import EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func)
from sverchok.utils.modules.color_utils import hsv_to_rgb, rgb_to_hsv
from sverchok.utils.sv_itertools import recurse_f_level_control
import numpy as np

def overlay_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_a[:, i] < 0.5
        mask2 = color_a[:, i] > 0.5
        end_color[mask, i] = 2 * color_a[mask, i] * color_b[mask, i]
        end_color[mask2, i] = 1.0 - 2.0 * (1.0 - color_a[mask2, i]) * (1.0 - color_b[mask2, i])
    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def soft_light_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] < 0.5
        mask2 = color_b[:, i] > 0.5
        end_color[mask, i] = 2.0 * color_a[mask, i] * color_b[mask, i] + color_a[mask, i] * color_a[mask, i] * (1.0 - 2.0 * color_b[mask, i])
        end_color[mask2, i] = np.sqrt(color_a[mask2, i]) * (2.0 * color_b[mask2, i] - 1.0) + 2.0 * color_a[mask2, i] * (1.0 - color_b[mask2, i])
    return color_a + (end_color - color_a) * fac[:, np.newaxis]

def color_dodge_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] >= 1
        mask2 = np.invert(mask)
        end_color[mask, i] = color_b[mask, i]
        end_color[mask2, i] = np.minimum(color_a[mask2, i] / (1.0 - color_b[mask2, i]), 1.0)
    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def color_burn_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] <= 0
        mask2 = np.invert(mask)
        end_color[mask, i] = color_b[mask, i]
        end_color[mask2, i] = np.maximum((1.0 - ((1.0 - color_a[mask2, i]) / color_b[mask2, i])), 0.0)
    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def vivid_light_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] < 0.5
        mask2 = np.invert(mask)
        mask1b = color_b[:, i] <= 0
        mask2b = color_b[:, i] >= 1
        end_color[mask, i] = np.maximum((1.0 - ((1.0 - color_a[mask, i]) / color_b[mask, i])), 0.0)
        end_color[mask1b, i] = color_b[mask1b, i]
        end_color[mask2, i] = np.minimum(color_a[mask2, i] / (1.0 - color_b[mask2, i]), 1.0)
        end_color[mask2b, i] = color_b[mask2b, i]
    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def pin_light_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] < 0.5
        mask2 = np.invert(mask)
        end_color[mask, i] = np.minimum(color_a[mask, i], 2 * color_b[mask, i])
        end_color[mask2, i] = np.maximum(color_a[mask2, i], 2*(color_b[mask2, i]-0.5))

    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def hard_mix_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] < 0.5
        mask2 = np.invert(mask)
        mask1b = color_b[:, i] <= 0
        mask2b = color_b[:, i] >= 1
        end_color[mask, i] = np.maximum((1.0 - ((1.0 - color_a[mask, i]) / color_b[mask, i])), 0.0)
        end_color[mask1b, i] = color_b[mask1b, i]
        end_color[mask2, i] = np.minimum(color_a[mask2, i] / (1.0 - color_b[mask2, i]), 1.0)
        end_color[mask2b, i] = color_b[mask2b, i]
        mask_f = end_color[:, i] < 0.5
        end_color[mask_f, i] = 0
        end_color[np.invert(mask_f), i] = 1
    return color_a + (end_color - color_a) * fac[:, np.newaxis]


def reflect_func(fac, color_a, color_b):
    end_color = np.array(color_a)
    for i in range(color_a.shape[1]):
        mask = color_b[:, i] >= 1
        mask2 = np.invert(mask)

        end_color[mask, i] = color_b[mask, i]
        end_color[mask2, i] = np.minimum(color_a[mask2, i] * color_a[mask2, i] / (1.0 - color_b[mask2, i]), 1.0)

    return color_a + (end_color - color_a) * fac[:, np.newaxis]

def hue_mix(fac, color_a, color_b):
    return hsv_mix(fac, color_a, color_b, 0)

def saturation_mix(fac, color_a, color_b):
    return hsv_mix(fac, color_a, color_b, 1)

def value_mix(fac, color_a, color_b):
    return hsv_mix(fac, color_a, color_b, 2)

def hsv_mix(fac, color_a, color_b, channel):
    hsv_color_a = rgb_to_hsv(color_a)
    hsv_color_b = rgb_to_hsv(color_b)
    hsv_end_color = np.array(hsv_color_a)
    hsv_end_color[:, channel] = hsv_color_b[:, channel]
    rgb_end_color = np.zeros(color_a.shape)
    rgb_end_color[:, :3] = hsv_to_rgb(hsv_end_color[:, :3])
    rgb_end_color[:, 3] = color_b[:, 3]
    return color_a + (rgb_end_color - color_a) * fac[:, np.newaxis]



COLOR_MODES_DICT = {
    "Mix":         (lambda fac, color_a, color_b: color_a + (color_b-color_a) * fac[:, np.newaxis], 1),
    "Darken":      (lambda fac, color_a, color_b: color_a + (np.minimum(color_a, color_b) - color_a) * fac[:, np.newaxis], 10),
    "Multiply":    (lambda fac, color_a, color_b: color_a + ((color_a * color_b) - color_a) * fac[:, np.newaxis], 11),
    "Burn":        (color_burn_func, 12),

    "Lighten":     (lambda fac, color_a, color_b: color_a + (np.maximum(color_a, color_b) -color_a) * fac[:, np.newaxis], 20),
    "Screen":      (lambda fac, color_a, color_b: color_a + ((1 - (1 - color_a) * (1 - color_b)) - color_a) * fac[:, np.newaxis], 21),
    "Dodge":       (color_dodge_func, 22),
    "Add":         (lambda fac, color_a, color_b: color_a + color_b * fac[:, np.newaxis], 23),

    "Overlay":     (overlay_func, 30),
    "Soft Light":  (soft_light_func, 31),
    "Vivid Light":  (vivid_light_func, 32),
    "Pin Light":   (pin_light_func, 33),
    "Hard Mix":    (hard_mix_func, 34),

    "Subtract":   (lambda fac, color_a, color_b: color_a - color_b * fac[:, np.newaxis], 40),
    "Difference": (lambda fac, color_a, color_b: color_a + ((color_a-color_b)-color_a) * fac[:, np.newaxis], 41),
    "Divide":     (lambda fac, color_a, color_b: color_a + ((color_a/color_b)-color_a) * fac[:, np.newaxis], 42),

    "Reflect":  (reflect_func, 50),

    "Hue": (hue_mix, 60),
    "Saturation": (saturation_mix, 61),
    "Value": (value_mix, 62),



}

COLOR_MODE_ITEMS = [(k.replace(" ", "_"), k, k, "", COLOR_MODES_DICT[k][1]) for k in COLOR_MODES_DICT]


def color_mix(params, constant, matching_f):
    result = []
    mode, match_mode, clamp, out_numpy = constant
    params = matching_f(params)
    numpy_match = numpy_list_match_func[match_mode]
    color_func = COLOR_MODES_DICT[mode.replace("_", " ")][0]

    for props in zip(*params):

        np_props = [np.array(prop) for prop in props]
        fac, color_a, color_b = numpy_match(np_props)

        res = color_func(fac, color_a, color_b)
        if clamp:
            res = np.clip(res, 0, 1)
        result.append(res if out_numpy else res.tolist())

    return result

class SvColorMixNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Colors Math
    Tooltip: Mix colors with various methods.
    """
    bl_idname = 'SvColorMixNode'
    bl_label = 'Color Mix'
    sv_icon = 'SV_COLOR_MIX'

    current_op: EnumProperty(
        name="Function", description="Function choice", default="Mix",
        items=COLOR_MODE_ITEMS, update=updateNode)

    factor: FloatProperty(default=1.0, name='Fac', soft_min=0.0, soft_max=1.0, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)
    clamp_output: BoolProperty(
        name='Clamp',
        description='Clamp result of the node to 0..1 range.',
        default=False, update=updateNode)

    color_A = FloatVectorProperty(
        name="Color A",
        subtype='COLOR',
        size=4,
        default=(0.0, 0.0, 0.0, 1.0),
        min=0.0, max=1.0,
        description="color picker",
        update=updateNode
        )
    color_B = FloatVectorProperty(
        name="Color B",
        subtype='COLOR',
        size=4,
        default=(1.0, 1.0, 1.0, 1.0),
        min=0.0, max=1.0,
        description="color picker",
        update=updateNode
        )

    def draw_label(self):
        if self.hide:
            label = ["Color", self.current_op,]
            return " ".join(label)
        return "Color Mix"

    def draw_buttons(self, ctx, layout):

        layout.prop(self, 'current_op', text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.prop(self, 'clamp_output')

    def draw_buttons_ext(self, ctx, layout):
        layout.prop(self, 'current_op', text="", icon_value=custom_icon("SV_FUNCTION"))
        layout.prop(self, 'list_match', expand=False)
        layout.prop(self, 'clamp_output')
        layout.prop(self, 'output_numpy', expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, 'current_op', text="Function")
        layout.prop(self, 'clamp_output')
        layout.prop(self, "output_numpy", expand=False)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Fac").prop_name = 'factor'
        self.inputs.new('SvColorSocket', "Color A").prop_name = 'color_A'
        self.inputs.new('SvColorSocket', "Color B").prop_name = 'color_B'
        self.outputs.new('SvColorSocket', "Color")


    def process(self):

        if self.outputs[0].is_linked:

            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
            matching_f = list_match_func[self.list_match]

            desired_levels = [2, 3, 3]
            ops = [self.current_op, self.list_match, self.clamp_output, self.output_numpy]
            result = recurse_f_level_control(params, ops, color_mix, matching_f, desired_levels)

            self.outputs[0].sv_set(result)


classes = [SvColorMixNode]
register, unregister = bpy.utils.register_classes_factory(classes)
