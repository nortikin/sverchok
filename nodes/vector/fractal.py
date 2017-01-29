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
from bpy.props import EnumProperty, IntProperty, FloatProperty
from mathutils import noise

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

# helpers
def dict_from(options, idx1, idx2):
    return {t[idx1]: t[idx2] for t in options}

def enum_from(options):
    return [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in options]

# function wrappers
def fractal(nbasis, verts, h_factor, lacunarity, octaves, offset, gain):
    return [noise.fractal(v, h_factor, lacunarity, octaves, nbasis) for v in verts]

def multifractal(nbasis, verts, h_factor, lacunarity, octaves, offset, gain):
    return [noise.multi_fractal(v, h_factor, lacunarity, octaves, nbasis) for v in verts]

def hetero(nbasis, verts, h_factor, lacunarity, octaves, offset, gain):
    return [noise.hetero_terrain(v, h_factor, lacunarity, octaves, offset, nbasis) for v in verts]

def ridged(nbasis, verts, h_factor, lacunarity, octaves, offset, gain):
    return [noise.ridged_multi_fractal(v, h_factor, lacunarity, octaves, offset, gain, nbasis) for v in verts]

def hybrid(nbasis, verts, h_factor, lacunarity, octaves, offset, gain):
    return [noise.hybrid_multi_fractal(v, h_factor, lacunarity, octaves, offset, gain, nbasis) for v in verts]

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

fractal_options = [
    ('FRACTAL', 0, (0, 0), fractal),
    ('MULTI_FRACTAL', 1, (0, 0), multifractal),
    ('HETERO_TERRAIN', 2, (1, 0), hetero),
    ('RIDGED_MULTI_FRACTAL', 3, (1, 1), ridged),
    ('HYBRID_MULTI_FRACTAL', 4, (1, 1), hybrid),
]


noise_dict = dict_from(noise_options, 0, 1)
fractal_f = dict_from(fractal_options, 0, 3)
props_enabled = dict_from(fractal_options, 0, 2)

avail_noise = enum_from(noise_options)
avail_fractal = enum_from(fractal_options)


class SvVectorFractal(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Fractal node'''
    bl_idname = 'SvVectorFractal'
    bl_label = 'Vector Fractal'
    bl_icon = 'FORCE_TURBULENCE'

    def wrapped_update(self, context):
        num_inputs = len(self.inputs)
        enabled = props_enabled.get(self.fractal_type)

        if enabled == (0, 0):
            if num_inputs > 4:
                for _ in range(num_inputs - 4):
                    self.inputs.remove(self.inputs[-1])

        elif enabled == (1, 0):
            if num_inputs == 4:
                self.inputs.new('StringsSocket', 'Offset').prop_name = 'offset'
            elif num_inputs == 6:
                self.inputs.remove(self.inputs[-1])

        elif enabled == (1, 1):
            if num_inputs == 4:
                self.inputs.new('StringsSocket', 'Offset').prop_name = 'offset'
                self.inputs.new('StringsSocket', 'Gain').prop_name = 'gain'
            elif num_inputs == 5:
                self.inputs.new('StringsSocket', 'Gain').prop_name = 'gain'


    noise_type = EnumProperty(
        items=avail_noise,
        default='STDPERLIN',
        description="Noise type",
        update=updateNode)

    fractal_type = EnumProperty(
        items=avail_fractal,
        default="FRACTAL",
        description="Fractal type",
        update=wrapped_update)

    h_factor = FloatProperty(default=0.05, description='H factor parameter', name='H Factor', update=updateNode)
    lacunarity = FloatProperty(default=0.5, description='Lacunarity parameter', name='Lacunarity', update=updateNode)
    octaves = IntProperty(default=3, min=0, max=6, description='Octaves', name='Octaves', update=updateNode)
    offset = FloatProperty(default=0.0, name='Offset', description='Offset parameter', update=updateNode)
    gain = FloatProperty(default=0.5, description='Gain parameter', name='Gain', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'H Factor').prop_name = 'h_factor'
        self.inputs.new('StringsSocket', 'Lacunarity').prop_name = 'lacunarity'
        self.inputs.new('StringsSocket', 'Octaves').prop_name = 'octaves'
        self.outputs.new('StringsSocket', 'Value')


    def draw_buttons(self, context, layout):
        layout.prop(self, 'fractal_type', text="Type")
        layout.prop(self, 'noise_type', text="Type")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        _noise_type = noise_dict[self.noise_type]
        wrapped_fractal_function = fractal_f[self.fractal_type]

        verts = inputs['Vertices'].sv_get()

        m_h_factor = inputs['H Factor'].sv_get()[0]
        m_lacunarity = inputs['Lacunarity'].sv_get()[0]
        m_octaves = inputs['Octaves'].sv_get()[0]
        m_offset = inputs['Offset'].sv_get()[0] if 'Offset' in inputs else [0.0]
        m_gain = inputs['Gain'].sv_get()[0] if 'Gain' in inputs else [0.0]
        param_list = [m_h_factor, m_lacunarity, m_octaves, m_offset, m_gain]

        out = []
        for idx, vlist in enumerate(verts):
            # lazy generation of full parameters.
            params = [(param[idx] if idx < len(param) else param[-1]) for param in param_list]
            out.append(wrapped_fractal_function(_noise_type, vlist, *params))

        outputs[0].sv_set(out)


def register():
    bpy.utils.register_class(SvVectorFractal)


def unregister():
    bpy.utils.unregister_class(SvVectorFractal)
