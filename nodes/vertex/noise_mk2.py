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

import inspect
import operator

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty
from mathutils import noise

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_degenerate, match_long_repeat)

# noise nodes
# from http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html

members = inspect.getmembers(noise.types)
noise_dict = {t[0]: t[1] for t in members if isinstance(t[1], int)}

noise_f = {'SCALAR': noise.noise, 'VECTOR': noise.noise_vector}


def avail_noise(self, context):
    n_t = [(t[0], t[0].title(), t[0].title(), '', t[1])
           for t in inspect.getmembers(noise.types) if isinstance(t[1], int)]
    n_t.sort(key=operator.itemgetter(0), reverse=True)
    return n_t


class SvNoiseNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Noise node'''
    bl_idname = 'SvNoiseNodeMK2'
    bl_label = 'Vector Noise MK2'
    bl_icon = 'FORCE_TURBULENCE'

    def changeMode(self, context):
        outputs = self.outputs
        if self.out_mode == 'SCALAR':
            if 'Noise S' not in outputs:
                outputs[0].replace_socket('StringsSocket', 'Noise S')
                return
        if self.out_mode == 'VECTOR':
            if 'Noise V' not in outputs:
                outputs[0].replace_socket('VerticesSocket', 'Noise V')
                return

    out_modes = [
        ('SCALAR', 'Scalar', 'Scalar output', '', 1),
        ('VECTOR', 'Vector', 'Vector output', '', 2)]

    out_mode = EnumProperty(
        items=out_modes,
        default='VECTOR',
        description='Output type',
        update=changeMode)

    noise_type = EnumProperty(
        items=avail_noise,
        description="Noise type",
        update=updateNode)

    seed = IntProperty(default=0, name='Seed', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Seed').prop_name = 'seed'
        self.outputs.new('VerticesSocket', 'Noise V')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)
        layout.prop(self, 'noise_type', text="Type")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return
        
        out = []
        verts = inputs['Vertices'].sv_get()
        seeds = inputs['Seed'].sv_get()[0]
        _noise_type = noise_dict[self.noise_type]
        noise_function = noise_f[self.out_mode]

        
        for idx, (seed, obj) in enumerate(zip(*match_long_repeat([seeds, verts]))):
            # multi-pass, make sure seed_val is a number and it isn't 0.
            # 0 unsets the seed and generates unreproducable output based on system time
            # We force the seed to a non 0 value. 
            # See https://github.com/nortikin/sverchok/issues/1095#issuecomment-271261600
            seed_val = seed if isinstance(seed, (int, float)) else 0
            seed_val = int(round(seed_val)) or 140230

            noise.seed_set(seed_val)
            out.append([noise_function(v, _noise_type) for v in obj])

        if 'Noise V' in outputs:
            outputs['Noise V'].sv_set(Vector_degenerate(out))
        else:
            outputs['Noise S'].sv_set(out)


def register():
    bpy.utils.register_class(SvNoiseNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvNoiseNodeMK2)
