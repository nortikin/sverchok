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


class SvMixNumbersNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Mix Numbers '''
    bl_idname = 'SvMixNumbersNode'
    bl_label = 'Mix Numbers'
    bl_icon = 'ANIM'

    # SV easing based interpolator
    def getInterpolator(self):
        if self.interpolation == "LINEAR":
            interpolate = LinearInterpolation

        elif self.interpolation == "QUADRATIC":
            if self.easing == "EASE_IN":
                interpolate = QuadraticEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = QuadraticEaseOut
            else:
                interpolate = QuadraticEaseInOut

        elif self.interpolation == "CUBIC":
            if self.easing == "EASE_IN":
                interpolate = CubicEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = CubicEaseOut
            else:
                interpolate = CubicEaseInOut

        elif self.interpolation == "QUARTIC":
            if self.easing == "EASE_IN":
                interpolate = QuarticEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = QuarticEaseOut
            else:
                interpolate = QuarticEaseInOut

        elif self.interpolation == "QUINTIC":
            if self.easing == "EASE_IN":
                interpolate = QuinticEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = QuinticEaseOut
            else:
                interpolate = QuinticEaseInOut

        elif self.interpolation == "CIRCULAR":
            if self.easing == "EASE_IN":
                interpolate = CircularEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = CircularEaseOut
            else:
                interpolate = CircularEaseInOut

        elif self.interpolation == "SINUSOIDAL":
            if self.easing == "EASE_IN":
                interpolate = SineEaseIn
            elif self.easing == "EASE_OUT":
                interpolate = SineEaseOut
            else:
                interpolate = SineEaseInOut

        elif self.interpolation == "BACK":
            s = self.backScale
            if self.easing == "EASE_IN":
                interpolate = lambda v : BackEaseIn(v, s)
            elif self.easing == "EASE_OUT":
                interpolate = lambda v : BackEaseOut(v, s)
            else:
                interpolate = lambda v : BackEaseInOut(v, s)

        elif self.interpolation == "ELASTIC":
            n = self.elasticBounces
            b = self.elasticBase
            e = self.elasticExponent
            settings = prepareElasticSettings(n, b, e)
            if self.easing == "EASE_IN":
                interpolate = lambda v : ElasticEaseIn(v, settings)
            elif self.easing == "EASE_OUT":
                interpolate = lambda v : ElasticEaseOut(v, settings)
            else:
                interpolate = lambda v : ElasticEaseInOut(v, settings)

        elif self.interpolation == "EXPONENTIAL":
            b = self.exponentialBase
            e = self.exponentialExponent
            settings = prepareExponentialSettings(b, e)
            if self.easing == "EASE_IN":
                interpolate = lambda v : ExponentialEaseIn(v, settings)
            elif self.easing == "EASE_OUT":
                interpolate = lambda v : ExponentialEaseOut(v, settings)
            else:
                interpolate = lambda v : ExponentialEaseInOut(v, settings)

        elif self.interpolation == "BOUNCE":
            n = self.bounceBounces
            a = self.bounceAttenuation
            settings = prepareBounceSettings(n, a)
            if self.easing == "EASE_IN":
                interpolate = lambda v : BounceEaseIn(v, settings)
            elif self.easing == "EASE_OUT":
                interpolate = lambda v : BounceEaseOut(v, settings)
            else:
                interpolate = lambda v : BounceEaseInOut(v, settings)

        else:
            interpolate = LinearInterpolation

        return interpolate


    def update_interpolation(self, context):
        updateNode(self, context)


    def update_easing(self, context):
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
        name="Interpolation",
        default="LINEAR",
        items=interplationItems,
        update=update_interpolation)

    easing = EnumProperty(
        name="Easing",
        default="EASE_IN_OUT",
        items=easingItems,
        update=update_easing)

    # BACK interpolation settings
    backScale = FloatProperty(
        name="Scale",
        default=0.5,
        soft_min=0.0,
        soft_max=10.0,
        description="Back scale",
        update=updateNode)

    # ELASTIC interpolation settings
    elasticBase = FloatProperty(
        name="Base",
        default=1.6,
        soft_min=0.0,
        soft_max=10.0,
        description="Elastic base",
        update=updateNode)

    elasticExponent = FloatProperty(
        name="Exponent",
        default=6.0,
        soft_min=0.0,
        soft_max=10.0,
        description="Elastic exponent",
        update=updateNode)

    elasticBounces = IntProperty(
        name="Bounces",
        default=6,
        soft_min=1,
        soft_max=10,
        description="Elastic bounces",
        update=updateNode)

    # EXPONENTIAL interpolation settings
    exponentialBase = FloatProperty(
        name="Base",
        default=2.0,
        soft_min=0.0,
        soft_max=10.0,
        description="Exponential base",
        update=updateNode)

    exponentialExponent = FloatProperty(
        name="Exponent",
        default=10.0,
        soft_min=0.0,
        soft_max=20.0,
        description="Exponential exponent",
        update=updateNode)

    # BOUNCE interpolation settings
    bounceAttenuation = FloatProperty(
        name="Attenuation",
        default=0.5,
        soft_min=0.1,
        soft_max=0.9,
        description="Bounce attenuation",
        update=updateNode)

    bounceBounces = IntProperty(
        name="Bounces",
        default=4,
        soft_min=1,
        soft_max=10,
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
            box.prop(self, 'bounceAttenuation')
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

        interpolate = self.getInterpolator()

        values=[]
        for v1, v2, f in zip(*parameters):
            t = interpolate(f)
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
