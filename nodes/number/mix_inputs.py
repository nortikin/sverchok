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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.data_structure import Matrix_generate
from sverchok.utils.sv_easing_functions import *
from mathutils import Matrix, Quaternion
import re

idMat = [[tuple(v) for v in Matrix()]]  # identity matrix

input_info = {
    'INT': {
        "Index": 0,
        "SocketType": "StringsSocket",
        "PropType": ('IntProperty', dict()),
        "PropDefault": {"A": 0, "B": 1},
        "Mixer": lambda t, v1, v2: (int(v1 * (1 - t) + v2 * t)),
        "Inputs": lambda ia, ib: [ia.sv_get()[0], ib.sv_get()[0]],
        "Outputs": lambda o, v: o.sv_set([v])
    },

    'FLOAT': {
        "Index": 1,
        "SocketType": "StringsSocket",
        "PropType": ('FloatProperty', dict()),
        "PropDefault": {"A": 0.0, "B": 1.0},
        "Mixer": lambda t, v1, v2: v1 * (1 - t) + v2 * t,
        "Inputs": lambda ia, ib: [ia.sv_get()[0], ib.sv_get()[0]],
        "Outputs": lambda o, v: o.sv_set([v])
    },

    'VECTOR': {
        "Index": 2,
        "SocketType": "VerticesSocket",
        "PropType": ('FloatVectorProperty', dict(size=3, subtype='XYZ')),
        "PropDefault": {"A": (0.0, 0.0, 0.0), "B": (1.0, 1.0, 1.0)},
        "Mixer": lambda t, v1, v2: tuple([v1[i] * (1 - t) + v2[i] * t for i in range(3)]),
        "Inputs": lambda ia, ib: [ia.sv_get()[0], ib.sv_get()[0]],
        "Outputs": lambda o, v: o.sv_set([v])
    },

    'COLOR': {
        "Index": 3,
        "SocketType": "SvColorSocket",
        "PropType": ('FloatVectorProperty', dict(size=4, subtype='COLOR', min=0, max=1)),
        "PropDefault": {"A": (0.0, 0.0, 0.0, 1.0), "B": (1.0, 1.0, 1.0, 1.0)},
        "Mixer": lambda t, v1, v2: tuple([v1[i] * (1 - t) + v2[i] * t for i in range(4)]),
        "Inputs": lambda ia, ib: [ia.sv_get()[0], ib.sv_get()[0]],
        "Outputs": lambda o, v: o.sv_set([v])
    },

    'QUATERNION': {
        "Index": 4,
        "SocketType": "SvQuaternionSocket",
        "PropType": ('FloatVectorProperty', dict(size=4, subtype='QUATERNION')),
        "PropDefault": {"A": (0.0, 0.0, 0.0, 0.0), "B": (1.0, 1.0, 1.0, 1.0)},
        "Mixer": lambda t, v1, v2: quaternionMix(t, v1, v2),
        "Inputs": lambda ia, ib: [ia.sv_get()[0], ib.sv_get()[0]],
        "Outputs": lambda o, v: o.sv_set([v])
    },

    'MATRIX': {
        "Index": 5,
        "SocketType": "MatrixSocket",
        "Mixer": lambda t, v1, v2: matrixMix(t, v1, v2),
        "Inputs": lambda ia, ib: [ia.sv_get(default=idMat), ib.sv_get(default=idMat)],
        "Outputs": lambda o, v: o.sv_set(v)
    }
}

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


def matrixMix(t, v1, v2):
    m1 = Matrix_generate([v1])[0]
    m2 = Matrix_generate([v2])[0]
    m = m1.lerp(m2, t)
    return m


def quaternionMix(t, v1, v2):
    q1 = Quaternion(v1)
    q2 = Quaternion(v2)
    q = q1.slerp(q2, max(0, min(t, 1)))
    return q


def make_prop(mode, label):
    ''' Property Factory '''
    description = "Mix " + mode + " value " + label
    default = input_info[mode]["PropDefault"][label]
    # general parameters
    params = dict(name=label, description=description, default=default, update=updateNode)
    # add type specific parameters
    params.update(input_info[mode]["PropType"][1])
    propType = input_info[mode]["PropType"][0]
    return getattr(bpy.props, propType)(**params)


class SvMixInputsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Interpolate, Slerp
    Tooltip: Interpolate between values of various types
    """
    bl_idname = 'SvMixInputsNode'
    bl_label = 'Mix Inputs'
    sv_icon = 'SV_MIX_INPUTS'

    # SV easing based interpolator
    def get_interpolator(self):
        # get the interpolator function based on selected interpolation and easing
        if self.interpolation == "LINEAR":
            return LinearInterpolation
        else:
            ''' This maps the Strings used in the Enumerator properties to the associated function'''
            interpolatorName = self.interpolation + "_" + self.easing
            interpolatorName = re.sub('SINUSOIDAL', 'sine', interpolatorName)  # for the exception
            interpolate = globals()[re.sub(r'[_]', '', interpolatorName.lower().title())]

            # setup the interpolator with prepared parameters
            if self.interpolation == "EXPONENTIAL":
                b = self.exponentialBase
                e = self.exponentialExponent
                settings = prepareExponentialSettings(b, e)
                return lambda v: interpolate(v, settings)

            elif self.interpolation == "BACK":
                s = self.backScale
                return lambda v: interpolate(v, s)

            elif self.interpolation == "ELASTIC":
                n = self.elasticBounces
                b = self.elasticBase
                e = self.elasticExponent
                settings = prepareElasticSettings(n, b, e)
                return lambda v: interpolate(v, settings)

            elif self.interpolation == "BOUNCE":
                n = self.bounceBounces
                a = self.bounceAttenuation
                settings = prepareBounceSettings(n, a)
                return lambda v: interpolate(v, settings)

            else:
                return interpolate

    def update_mode(self, context):
        self.update_sockets()
        updateNode(self, context)

    typeDict = {input_info[t]["Index"]: t for t in input_info.keys()}
    typeItems = [(v, v.title(), "", "", k) for (k, v) in sorted(typeDict.items())]

    mode = EnumProperty(
        name="Mode", description="The type of the values to mix",
        default="FLOAT", items=typeItems,
        update=update_mode)

    # INTERPOLATION settings
    interpolation = EnumProperty(
        name="Interpolation", description="Interpolation type",
        default="LINEAR", items=interplationItems,
        update=updateNode)

    easing = EnumProperty(
        name="Easing", description="Easing type",
        default="EASE_IN_OUT", items=easingItems,
        update=updateNode)

    # BACK interpolation settings
    backScale = FloatProperty(
        name="Scale", description="Back scale",
        default=0.5, soft_min=0.0, soft_max=10.0,
        update=updateNode)

    # ELASTIC interpolation settings
    elasticBase = FloatProperty(
        name="Base", description="Elastic base",
        default=1.6, soft_min=0.0, soft_max=10.0,
        update=updateNode)

    elasticExponent = FloatProperty(
        name="Exponent", description="Elastic exponent",
        default=6.0, soft_min=0.0, soft_max=10.0,
        update=updateNode)

    elasticBounces = IntProperty(
        name="Bounces", description="Elastic bounces",
        default=6, soft_min=1, soft_max=10,
        update=updateNode)

    # EXPONENTIAL interpolation settings
    exponentialBase = FloatProperty(
        name="Base", description="Exponential base",
        default=2.0, soft_min=0.0, soft_max=10.0,
        update=updateNode)

    exponentialExponent = FloatProperty(
        name="Exponent", description="Exponential exponent",
        default=10.0, soft_min=0.0, soft_max=20.0,
        update=updateNode)

    # BOUNCE interpolation settings
    bounceAttenuation = FloatProperty(
        name="Attenuation", description="Bounce attenuation",
        default=0.5, soft_min=0.1, soft_max=0.9,
        update=updateNode)

    bounceBounces = IntProperty(
        name="Bounces", description="Bounce bounces",
        default=4, soft_min=1, soft_max=10,
        update=updateNode)

    # INPUT sockets props
    factor = FloatProperty(
        name="Factor", description="Factor value",
        default=0.5, min=0.0, max=1.0,
        update=updateNode)

    for m in input_info.keys():  # create props for input sockets A/B
        if m != "MATRIX":
            for l in ['A', 'B']:
                attr_name = m.lower() + "_" + l.lower()
                vars()[attr_name] = make_prop(m, l)

    mirror = BoolProperty(
        name="Mirror", description="Mirror the interplation factor",
        default=False, update=updateNode)

    swap = BoolProperty(
        name="Swap", description="Swap the two inputs",
        default=False, update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "f").prop_name = 'factor'
        self.inputs.new('StringsSocket', "A").prop_name = 'float_a'
        self.inputs.new('StringsSocket', "B").prop_name = 'float_b'
        self.outputs.new('StringsSocket', "Float")
        self.update_sockets()

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text="", expand=False)
        row = layout.row(align=True)
        row.prop(self, 'interpolation', text="", expand=False)
        row.prop(self, 'easing', text="", expand=True)
        row = layout.row(align=True)
        row.prop(self, 'mirror', toggle=True)
        row.prop(self, 'swap', toggle=True)

    def draw_label(self):
        if self.mode == "MATRIX":
            return "Mix Matrices"
        else:
            return "Mix " + self.mode.title() + "s"

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

    def get_mixer(self):
        return input_info[self.mode]['Mixer']

    def get_inputs(self):
        input_getter = input_info[self.mode]["Inputs"]
        f = self.inputs["f"].sv_get()[0]
        i, j = [2, 1] if self.swap else [1, 2]  # swap inputs ?
        [a, b] = input_getter(self.inputs[i], self.inputs[j])
        return [f, a, b]

    def set_ouputs(self, values):
        output_setter = input_info[self.mode]["Outputs"]
        output_setter(self.outputs[0], values)

    def update_sockets(self):
        # replace input and output sockets, linking input socket to corresponding props
        new_socket_type = input_info[self.mode]["SocketType"]
        for socket in self.inputs[1:]:
            if self.mode != "MATRIX":
                prop_name = self.mode.lower() + "_" + socket.name.lower()
                socket.replace_socket(new_socket_type).prop_name = prop_name
            else:
                socket.replace_socket(new_socket_type)

        self.outputs[0].replace_socket(new_socket_type, self.mode.title())

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists (single or multi value)
        input_factor, input_value1, input_value2 = self.get_inputs()

        parameters = match_long_repeat([input_factor, input_value1, input_value2])

        interpolate = self.get_interpolator()

        mix = self.get_mixer()

        values = []
        for f, v1, v2 in zip(*parameters):
            if self.mirror:
                f = 1 - 2 * abs(f - 0.5)
            t = interpolate(f)
            v = mix(t, v1, v2)
            values.append(v)

        self.set_ouputs(values)


def register():
    bpy.utils.register_class(SvMixInputsNode)


def unregister():
    bpy.utils.unregister_class(SvMixInputsNode)
