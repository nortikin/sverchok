# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import operator
from math import sqrt

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty, BoolProperty
from mathutils import noise, Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, Vector_degenerate, match_long_repeat
from sverchok.utils.sv_noise_utils import noise_options, PERLIN_ORIGINAL


def deepnoise(v, noise_basis=PERLIN_ORIGINAL):
    u = noise.noise_vector(v, noise_basis=noise_basis)[:]
    a = u[0], u[1], u[2]-1   # a = u minus (0,0,1)
    return sqrt((a[0] * a[0]) + (a[1] * a[1]) + (a[2] * a[2])) * 0.5


avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]
noise_f = {'SCALAR': deepnoise, 'VECTOR': noise.noise_vector}


class SvNoiseDisplace(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Vector Noise Displace
    Tooltip: Affect input verts with a noise function.
    
    A short description for reader of node code
    """

    bl_idname = 'SvNoiseDisplace'
    bl_label = 'Vector Noise Displace'
    bl_icon = 'FORCE_TURBULENCE'

    def changeMode(self, context):
        outputs = self.outputs
        
        #if self.displace and not self.out_mode == 'Vector':
        #    self.displace = False
        
        #self.set_sockets_associated_with_displacemode(context)

        if self.out_mode == 'SCALAR':
            if 'Noise S' not in outputs:
                outputs[0].replace_socket('SvStringsSocket', 'Noise S')
                return
        if self.out_mode == 'VECTOR':
            if 'Noise V' not in outputs:
                outputs[0].replace_socket('SvVerticesSocket', 'Noise V')
                return

    def set_sockets_associated_with_displacemode(self, context):
        # this will disconnect links. fix that.
        # if self.out_mode == 'Vector':

        #    self.inputs["Rescale"].hide != self.displace:

        self.inputs["Rescale"].hide_safe = not self.displace
        self.inputs["Amplify"].hide_safe = not self.displace
        #    # self.process()
        pass

    out_modes = [
        ('SCALAR', 'Scalar', 'Scalar output', '', 1),
        ('VECTOR', 'Vector', 'Vector output', '', 2)]

    out_mode: EnumProperty(
        items=out_modes,
        default='VECTOR',
        description='Output type',
        update=changeMode)

    noise_type: EnumProperty(
        items=avail_noise,
        default=PERLIN_ORIGINAL,
        description="Noise type",
        update=updateNode)

    displace: BoolProperty(
        default=False, description="displace input verts", name="displace by noise",
        update=set_sockets_associated_with_displacemode)
    
    seed: IntProperty(default=0, name='Seed', update=updateNode)
    rescale: FloatProperty(default=1.0, min=0.00001, name="Rescale", update=updateNode)
    amplify: FloatProperty(default=1.0, min=0.00001, name="Amplify", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.inputs.new('SvStringsSocket', 'Rescale').prop_name = 'rescale'
        self.inputs.new('SvStringsSocket', 'Amplify').prop_name = 'amplify'
        self.inputs['Rescale'].hide_safe = True
        self.inputs['Amplify'].hide_safe = True

        self.outputs.new('SvVerticesSocket', 'Noise V')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)
        layout.prop(self, 'noise_type', text="Type")
        if self.out_mode == 'VECTOR':
            layout.prop(self, 'displace', text="Displace")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        out = []
        verts = inputs['Vertices'].sv_get(deepcopy=False)
        seeds = inputs['Seed'].sv_get()[0]

        noise_function = noise_f[self.out_mode]


        for idx, (seed, obj) in enumerate(zip(*match_long_repeat([seeds, verts]))):
            # multi-pass, make sure seed_val is a number and it isn't 0.
            # 0 unsets the seed and generates unreproducable output based on system time
            # We force the seed to a non 0 value.
            # See https://github.com/nortikin/sverchok/issues/1095#issuecomment-271261600
            seed_val = seed if isinstance(seed, (int, float)) else 0
            seed_val = int(round(seed_val)) or 140230

            noise.seed_set(seed_val)

            if not self.inputs['Amplify'].hide and self.displace:
                
                # doesn't handle reading inputs yet.
                reamp = self.amplify
                vrescale = self.rescale
                vec_scale = lambda v, scale: (v[0] * scale, v[1] * scale, v[2] * scale)

                strict_evaluation = []
                strict_obtain = strict_evaluation.append
                premultiplied_v = [vec_scale(v, vrescale) for v in obj]
                for v, original_v in zip(premultiplied_v, obj):
                    strict_obtain((noise_function(v, noise_basis=self.noise_type) / vrescale * reamp) + Vector(original_v))
                out.append(strict_evaluation)
            else:
                out.append([noise_function(v, noise_basis=self.noise_type) for v in obj])

        if 'Noise V' in outputs:
            outputs['Noise V'].sv_set(Vector_degenerate(out))
        else:
            outputs['Noise S'].sv_set(out)

    def draw_label(self):
        if self.hide:
            if not self.inputs['Seed'].is_linked:
                seed = ' + ({0})'.format(str(int(self.seed)))
            else:
                seed = ' + seed(s)'
            return self.noise_type.title() + seed
        else:
            return self.label or self.name

classes = [SvNoiseDisplace]
register, unregister = bpy.utils.register_classes_factory(classes)

