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
from math import sqrt

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty
from mathutils import noise,Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_degenerate, match_long_repeat)

# noise nodes
# from http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html


noise_options = [
    ('BLENDER', 0),
    ('STDPERLIN', 1),
    ('NEWPERLIN', 2),
    ('VORONOI_F1', 3),
    ('VORONOI_F2', 4),
    ('VORONOI_F3', 5),
    ('VORONOI_F4', 6),
    ('VORONOI_F2F1', 7),
    ('VORONOI_CRACKLE', 8),
    ('CELLNOISE', 14)
]

def turbulence(verts, octaves, hard, _noise_type, amp, freq):
    return noise.turbulence(verts, octaves, hard, _noise_type, amp, freq )

noise_dict = {t[0]: t[1] for t in noise_options}
avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]

turbulence_f = {'SCALAR': turbulence, 'VECTOR': noise.turbulence_vector}


class SvTurbulenceNode(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Turbulence node'''
    bl_idname = 'SvTurbulenceNode'
    bl_label = 'Vector Turbulence'
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
        default='STDPERLIN',
        description="Noise type",
        update=updateNode)

    octaves = IntProperty(default=3, min=0, max=6, description='Octaves', name='Octaves', update=updateNode)
    hard = IntProperty(default=0, min=0, max=1, description="Hard (sharp transitions) or soft (smooth transitions)", name="Hard", update=updateNode)
    amp = FloatProperty(default=0.5, description="The amplitude scaling factor", name="Amplitude", update=updateNode)
    freq = IntProperty(default=0, description="The frequency scaling factor", name="Frequency", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Octaves').prop_name = 'octaves'
        self.inputs.new('StringsSocket', 'Hard').prop_name = 'hard'
        self.inputs.new('StringsSocket', 'Amplitude').prop_name = 'amp'
        self.inputs.new('StringsSocket', 'Frequency').prop_name = 'freq'
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
        '''
        print("verts from circle: ")
        print(verts)
        print("number of verts: ")
        print(len(verts))'''
        m_octaves = inputs['Octaves'].sv_get()[0][0]
        m_hard = inputs['Hard'].sv_get()[0][0]
        m_amp = inputs['Amplitude'].sv_get()[0][0]
        m_freq = inputs['Frequency'].sv_get()[0][0]
        param_list = [m_octaves, m_hard, m_amp, m_freq ]

        _noise_type = noise_dict[self.noise_type]
        turbulence_function = turbulence_f[self.out_mode]

        vertices = []
        for vertices in verts[:]:

            out.append([turbulence_function(v, m_octaves, m_hard, _noise_type, m_amp, m_freq) for v in vertices])
            
        if 'Noise V' in outputs:
            outputs['Noise V'].sv_set(Vector_degenerate(out))
        else:
            outputs['Noise S'].sv_set(out)


def register():
    bpy.utils.register_class(SvTurbulenceNode)


def unregister():
    bpy.utils.unregister_class(SvTurbulenceNode)
