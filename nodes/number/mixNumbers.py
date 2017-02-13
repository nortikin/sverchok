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

from math import sin, cos, pi, sqrt, pow, radians, floor
from random import random
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, SvSetSocketAnyType
from sverchok.utils.sv_easing_functions import *

DEBUG=False

typeItems = [
    ("INT", "Integer", "", "", 0),
    ("FLOAT", "Float", "", "", 1)]

interplationItems = [
    ("LINEAR", "Linear", "", "IPO_LINEAR", 0),
    ("SINUSOIDAL", "Sinusoidal", "", "IPO_SINE", 1),
    ("QUADRATIC", "Quadratic", "", "IPO_QUAD", 2),
    ("CUBIC", "Cubic", "", "IPO_CUBIC", 3),
    ("QUARTIC", "Quartic", "", "IPO_QUART", 4),
    ("QUINTIC", "Quintic", "", "IPO_QUINT", 5),
    ("EXPONENTIAL", "Exponential", "", "IPO_EXPO", 6),
    ("CIRCULAR", "Circular", "", "IPO_CIRC", 7),
    # DYNAMIC effects
    ("BACK", "Back", "", "IPO_BACK", 8),
    ("BOUNCE", "Bounce", "", "IPO_BOUNCE", 9),
    ("ELASTIC", "Elastic", "", "IPO_ELASTIC", 10)]

easingItems = [
    ("EASE_IN", "Ease In", "", "IPO_EASE_IN", 0),
    ("EASE_OUT", "Ease Out", "", "IPO_EASE_OUT", 1),
    ("EASE_IN_OUT", "Ease In-Out", "", "IPO_EASE_IN_OUT", 2)]

# POWER interpolation : QUADTRATIC, CUBIC, QUARTIC, QUINTIC

def powerInOut(x, exponent = 2):
    '''Exponent has to be a positive integer'''
    if x <= 0.5:
        return pow(x * 2, exponent) / 2
    else:
        return pow((x - 1) * 2, exponent) / (-2 if exponent % 2 == 0 else 2) + 1

def powerIn(x, exponent = 2):
    return pow(x, exponent)

def powerOut(x, exponent = 2):
    return pow(x - 1, exponent) * (-1 if exponent % 2 == 0 else 1) + 1

# CIRCULAR interpolation

def circularInOut(x):
    if x <= 0.5:
        x *= 2
        return (1 - sqrt(1 - x * x)) / 2
    else:
        x = (x - 1) * 2
        return (sqrt(1 - x * x) + 1) / 2

def circularIn(x):
    return 1 - sqrt(1 - x * x)

def circularOut(x):
    x -= 1
    return sqrt(1 - x * x)

# SINUSOIDAL interpolation

def sinInOut(x):
    return (1 - cos(x * pi)) / 2

def sinIn(x):
    return 1 - cos(x * pi / 2)

def sinOut(x):
    return sin(x * pi / 2)

# BACK swing interpolation

def backInOut(x, scale = 1.7):
    if x <= 0.5:
        x *= 2
        return x * x * ((scale + 1) * x - scale) / 2
    else:
        x = (x - 1) * 2
        return x * x * ((scale + 1) * x + scale) / 2 + 1

def backIn(x, scale = 1.7):
    return x * x * ((scale + 1) * x - scale)

def backOut(x, scale = 1.7):
    x -= 1
    return x * x * ((scale + 1) * x + scale) + 1

# ELASTIC interpolation

def prepareElasticSettings(base, exponent, bounces):
    scale = -1 if bounces % 2 == 0 else 1
    bounces = bounces + 0.5
    base = max(base, 0)
    bounces = bounces * pi * (1 if bounces % 2 == 0 else -1)
    return (base, exponent, bounces, scale)

def elasticInOut(x, settings):
    base, exponent, bounces, scale = settings
    if x <= 0.5:
        x *= 2
        return pow(base, exponent * (x - 1)) * sin(x * bounces) * scale / 2
    else:
        x = (1 - x) * 2
        return 1 - pow(base, exponent * (x - 1)) * sin(x * bounces) * scale / 2

def elasticIn(x, settings):
    base, exponent, bounces, scale = settings
    return pow(base, exponent * (x - 1)) * sin(x * bounces) * scale

def elasticOut(x, settings):
    base, exponent, bounces, scale = settings
    x = 1 - x
    return 1 - pow(base, exponent * (x - 1)) * sin(x * bounces) * scale

# EXPONENTIAL interpolation

def prepareExponentialSettings(base, exponent):
    exponent = min(max(0, int(exponent)), 70)
    base = max(0.0001, base) if base != 1 else 1.0001
    minValue = pow(base, -exponent)
    scale = 1 / (1 - minValue)
    return (base, exponent, minValue, scale)

def exponentialInOut(x, settings):
    base, exponent, minValue, scale = settings
    if x <= 0.5:
        return (pow(base, exponent * (x * 2 - 1)) - minValue) * scale / 2
    else:
        return (2 - (pow(base, -exponent * (x * 2 - 1)) - minValue) * scale) / 2

def exponentialIn(x, settings):
    base, exponent, minValue, scale = settings
    return (pow(base, exponent * (x - 1)) - minValue) * scale

def exponentialOut(x, settings):
    base, exponent, minValue, scale = settings
    return 1 - (pow(base, -exponent * x) - minValue) * scale

# BOUNCE interpolation

def prepareBounceSettings(bounces, base):
    '''
    sum(widths) - widths[0] / 2 = 1
    '''
    bounces = max(1, int(bounces))
    a = 2 ** (bounces - 1)
    b = (1 - 2 ** bounces) / (1 - 2) - 2 ** (bounces - 2)
    c = a / b
    widths = [c / 2 ** i for i in range(bounces)]
    heights = [x * base for x in widths]
    heights[0] = 1
    return (widths, heights)

def bounceInOut(x, settings):
    if x <= 0.5: return (1 - bounceOut(1 - x * 2, settings)) / 2
    else: return bounceOut(x * 2 - 1, settings) / 2 + 0.5

def bounceIn(x, settings):
    return 1 - bounceOut(1 - x, settings)

def bounceOut(x, settings):
    widths, heights = settings
    x += widths[0] / 2
    for width, height in zip(widths, heights):
        if x <= width: break
        x -= width
    x /= width
    z = 4 / width * height * x
    return 1 -(z - z * x) * width


class SvMixNumbersNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Mix Numbers '''
    bl_idname = 'SvMixNumbersNode'
    bl_label = 'Mix Numbers'
    bl_icon = 'ANIM'

    # Animation-Nodes easing based interpolation
    def interpolate1(self, v):
        if self.interpolation == "LINEAR":
            value = v

        elif self.interpolation == "QUADRATIC":
            if self.easing == "EASE_IN":
                value = powerIn(v)
            elif self.easing == "EASE_OUT":
                value = powerOut(v)
            else:
                value = powerInOut(v)

        elif self.interpolation == "CUBIC":
            if self.easing == "EASE_IN":
                value = powerIn(v,3)
            elif self.easing == "EASE_OUT":
                value = powerOut(v,3)
            else:
                value = powerInOut(v,3)

        elif self.interpolation == "QUARTIC":
            if self.easing == "EASE_IN":
                value = powerIn(v,4)
            elif self.easing == "EASE_OUT":
                value = powerOut(v,4)
            else:
                value = powerInOut(v,4)

        elif self.interpolation == "QUINTIC":
            if self.easing == "EASE_IN":
                value = powerIn(v,5)
            elif self.easing == "EASE_OUT":
                value = powerOut(v,5)
            else:
                value = powerInOut(v,5)

        elif self.interpolation == "CIRCULAR":
            if self.easing == "EASE_IN":
                value = circularIn(v)
            elif self.easing == "EASE_OUT":
                value = circularOut(v)
            else:
                value = circularInOut(v)

        elif self.interpolation == "SINUSOIDAL":
            if self.easing == "EASE_IN":
                value = sinIn(v)
            elif self.easing == "EASE_OUT":
                value = sinOut(v)
            else:
                value = sinInOut(v)

        elif self.interpolation == "BACK":
            if self.easing == "EASE_IN":
                value = backIn(v, self.backScale)
            elif self.easing == "EASE_OUT":
                value = backOut(v, self.backScale)
            else:
                value = backInOut(v, self.backScale)

        elif self.interpolation == "ELASTIC":
            settings = prepareElasticSettings(self.elasticBase, self.elasticExponent, self.elasticBounces)
            if self.easing == "EASE_IN":
                value = elasticIn(v, settings)
            elif self.easing == "EASE_OUT":
                value = elasticOut(v, settings)
            else:
                value = elasticInOut(v, settings)

        elif self.interpolation == "EXPONENTIAL":
            settings = prepareExponentialSettings(self.exponentialBase, self.exponentialExponent)
            if self.easing == "EASE_IN":
                value = exponentialIn(v, settings)
            elif self.easing == "EASE_OUT":
                value = exponentialOut(v, settings)
            else:
                value = exponentialInOut(v, settings)

        elif self.interpolation == "BOUNCE":
            settings = prepareBounceSettings(self.bounceBounces, self.bounceBase)
            if self.easing == "EASE_IN":
                value = bounceIn(v, settings)
            elif self.easing == "EASE_OUT":
                value = bounceOut(v, settings)
            else:
                value = bounceInOut(v, settings)

        else:
            value = 0

        return value

    # SV easing based interpolation
    def interpolate2(self, v):
        if self.interpolation == "LINEAR":
            value = v

        elif self.interpolation == "QUADRATIC":
            if self.easing == "EASE_IN":
                value = QuadraticEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = QuadraticEaseOut(v)
            else:
                value = QuadraticEaseInOut(v)

        elif self.interpolation == "CUBIC":
            if self.easing == "EASE_IN":
                value = CubicEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = CubicEaseOut(v)
            else:
                value = CubicEaseInOut(v)

        elif self.interpolation == "QUARTIC":
            if self.easing == "EASE_IN":
                value = QuarticEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = QuarticEaseOut(v)
            else:
                value = QuarticEaseInOut(v)

        elif self.interpolation == "QUINTIC":
            if self.easing == "EASE_IN":
                value = QuinticEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = QuinticEaseOut(v)
            else:
                value = QuinticEaseInOut(v)

        elif self.interpolation == "CIRCULAR":
            if self.easing == "EASE_IN":
                value = CircularEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = CircularEaseOut(v)
            else:
                value = CircularEaseInOut(v)

        elif self.interpolation == "SINUSOIDAL":
            if self.easing == "EASE_IN":
                value = SineEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = SineEaseOut(v)
            else:
                value = SineEaseInOut(v)

        elif self.interpolation == "BACK":
            if self.easing == "EASE_IN":
                value = BackEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = BackEaseOut(v)
            else:
                value = BackEaseInOut(v)

        elif self.interpolation == "ELASTIC":
            if self.easing == "EASE_IN":
                value = ElasticEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = ElasticEaseOut(v)
            else:
                value = ElasticEaseInOut(v)

        elif self.interpolation == "EXPONENTIAL":
            if self.easing == "EASE_IN":
                value = ExponentialEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = ExponentialEaseOut(v)
            else:
                value = ExponentialEaseInOut(v)

        elif self.interpolation == "BOUNCE":
            if self.easing == "EASE_IN":
                value = BounceEaseIn(v)
            elif self.easing == "EASE_OUT":
                value = BounceEaseOut(v)
            else:
                value = BounceEaseInOut(v)

        else:
            value = 0

        return value


    def update_interpolation(self, context):
        # do some updates here
        updateNode(self, context)


    def update_easing(self, context):
        # do some updates here
        updateNode(self, context)


    def update_type(self, context):
        # do some updates here
        if self.numType == 'INT':
            self.inputs['v1'].prop_name = "value_int1"
            self.inputs['v2'].prop_name = "value_int2"
        else: # float type
            self.inputs['v1'].prop_name = "value_float1"
            self.inputs['v2'].prop_name = "value_float2"

        updateNode(self, context)


    numType = EnumProperty(
        name="Number Type",
        default="FLOAT",
        items=typeItems,
        update=update_type)

    # INTERPOLATION settings
    interpolation = EnumProperty(
        name = "Interpolation",
        default = "LINEAR",
        items = interplationItems,
        update = update_interpolation)

    easing = EnumProperty(
        name = "Easing",
        default = "EASE_IN_OUT",
        items = easingItems,
        update = update_easing)

    # BACK interpolation settings
    backScale = FloatProperty(
        name="Scale",
        default=1.7,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Back scale",
        update=updateNode)

    # ELASTIC interpolation settings
    elasticBase = FloatProperty(
        name="Base",
        default=1.6,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Elastic base",
        update=updateNode)

    elasticExponent = FloatProperty(
        name="Exponent",
        default=6.0,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Elastic exponent",
        update=updateNode)

    elasticBounces = IntProperty(
        name="Bounces",
        default=6,
        soft_min = 1,
        soft_max = 10,
        description="Elastic bounces",
        update=updateNode)

    # EXPONENTIAL interpolation settings
    exponentialBase = FloatProperty(
        name="Base",
        default=2.0,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Exponential base",
        update=updateNode)

    exponentialExponent = FloatProperty(
        name="Exponent",
        default=5.0,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Exponential exponent",
        update=updateNode)

    # BOUNCE interpolation settings
    bounceBase = FloatProperty(
        name="Base",
        default=1.5,
        soft_min = 0.0,
        soft_max = 10.0,
        description="Bounce base",
        update=updateNode)

    bounceBounces = IntProperty(
        name="Bounces",
        default=4,
        soft_min = 1,
        soft_max = 10,
        description="Bounce bounces",
        update=updateNode)

    # INPUT sockets settings
    value_float1 = FloatProperty(
        name="Value 1",
        default=0.0,
        description="Mix FLOAT value 1",
        update=updateNode)

    value_float2 = FloatProperty(
        name="Value 2",
        default=1.0,
        description="Mix FLOAT value 2",
        update=updateNode)

    value_int1 = IntProperty(
        name="Value 1",
        default=0,
        description="Mix INT value 1",
        update=updateNode)

    value_int2 = IntProperty(
        name="Value 2",
        default=1,
        description="Mix INT value 2",
        update=updateNode)

    factor = FloatProperty(
        name="Factor",
        default=0.5,
        min=0.0, max=1.0,
        description="Factor value",
        update=updateNode)


    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "v1").prop_name = 'value_float1'
        self.inputs.new('StringsSocket', "v2").prop_name = 'value_float2'
        self.inputs.new('StringsSocket', "f").prop_name = 'factor'

        self.outputs.new('StringsSocket', "Value")


    def draw_buttons(self, context, layout):
        layout.prop(self, 'numType', expand=True)
        layout.prop(self, 'interpolation', expand=False)
        layout.prop(self, 'easing', expand=False)


    def draw_buttons_ext(self, context, layout):
        if self.interpolation == "BACK":
            layout.column().label(text="Interpolation:")
            box = layout.box()
            box.prop(self, 'backScale')

        elif self.interpolation == "ELASTIC":
            layout.column().label(text="Interpolation:")
            box = layout.box()
            box.prop(self, 'elasticBase')
            box.prop(self, 'elasticExponent')
            box.prop(self, 'elasticBounces')

        elif self.interpolation == "EXPONENTIAL":
            layout.column().label(text="Interpolation:")
            box = layout.box()
            box.prop(self, 'exponentialBase')
            box.prop(self, 'exponentialExponent')

        elif self.interpolation == "BOUNCE":
            layout.column().label(text="Interpolation:")
            box = layout.box()
            box.prop(self, 'bounceBase')
            box.prop(self, 'bounceBounces')


    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_value1 = self.inputs["v1"].sv_get()[0]
        input_value2 = self.inputs["v2"].sv_get()[0]
        input_factor = self.inputs["f"].sv_get()[0]

        parameters = match_long_repeat([input_value1, input_value2, input_factor])

        values=[]
        for v1, v2, f in zip(*parameters):
            t = self.interpolate2(f)
            v = v1*(1-t) + v2*t

            values.append(v)

        # if self.numType == "INT":
        #     values = list(map(lambda x: int(x), values))

        self.outputs['Value'].sv_set([values])


def register():
    bpy.utils.register_class(SvMixNumbersNode)


def unregister():
    bpy.utils.unregister_class(SvMixNumbersNode)

if __name__ == '__main__':
    register()
