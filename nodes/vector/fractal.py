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


def fractal(_noise_type, v, h_factor, lacunarity, octaves, offset, gain):
    return noise.fractal(verts, h_factor, lacunarity, octaves, _noise_type)
 
def multifractal(_noise_type, v, h_factor, lacunarity, octaves, offset, gain):
    out = 0.0
    print("hey, i'am a multifractal!")
    return out

def hetero(_noise_type, v, h_factor, lacunarity, octaves, offset, gain):
    out = 0.0
    print("hetero fractal works")
    return out

def ridged(_noise_type, v, h_factor, lacunarity, octaves, offset, gain):
    out = 0.0
    print("ridged fractal!")
    return out

def hybrid(_noise_type, v, h_factor, lacunarity, octaves, offset, gain):
    out = 0.0
    print("you got a hybrid fractal!")
    return out

fractal_f = {
    'FRACTAL': fractal, 
    'MULTI_FRACTAL': multifractal, 
    'HETERO_TERRAIN': hetero, 
    'RIDGED_MULTI_FRACTAL': ridged, 
    'HYBRID_MULTI_FRACTAL': hybrid
}

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
    ('FRACTAL', 0),
    ('MULTI_FRACTAL', 1),
    ('HETERO_TERRAIN', 2),
    ('RIDGED_MULTI_FRACTAL', 3),
    ('HYBRID_MULTI_FRACTAL', 4),
]


noise_dict = {t[0]: t[1] for t in noise_options}
avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]

fractal_dict = {t[0]: t[1] for t in fractal_options}
avail_fractal = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in fractal_options]


class SvVectorFractal(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Fractal node'''
    bl_idname = 'SvVectorFractal'
    bl_label = 'Vector Fractal'
    bl_icon = 'FORCE_TURBULENCE'

    noise_type = EnumProperty(
        items=avail_noise,
        default='STDPERLIN',
        description="Noise type",
        update=updateNode)

    fractal_type = EnumProperty(
        items=avail_fractal,
        default="FRACTAL",
        description="Fractal type",
        update=updateNode)

    h_factor = FloatProperty(default=0.5, name='H Factor', update=updateNode)
    lacunarity = FloatProperty(default=1.0, name='Lacunarity', update=updateNode)
    octaves = IntProperty(default=3, min=0, max=6, name='Octaves', update=updateNode)
    offset = FloatProperty(default=0.0, name='Offset', update=updateNode)
    gain = FloatProperty(default=0.5, name='Gain', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'H Factor').prop_name = 'h_factor'
        self.inputs.new('StringsSocket', 'Lacunarity').prop_name = 'lacunarity'
        self.inputs.new('StringsSocket', 'Octaves').prop_name = 'octaves'
        self.inputs.new('StringsSocket', 'Offset').prop_name = 'offset'
        self.inputs.new('StringsSocket', 'Gain').prop_name = 'gain'        
        self.outputs.new('StringsSocket', 'Value')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'fractal_type', text="Type")
        layout.prop(self, 'noise_type', text="Type")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        out = []
        _noise_type = noise_dict[self.noise_type]
        fractal_function = fractal_f[self.fractal_type]

        verts = inputs['Vertices'].sv_get()

        m_h_factor = inputs['H Factor'].sv_get()[0]
        m_lacunarity = inputs['Lacunarity'].sv_get()[0]
        m_octaves = inputs['Octaves'].sv_get()[0]
        m_offset = inputs['Offset'].sv_get()[0]
        m_gain = inputs['Gain'].sv_get()[0]

        param_list = [m_h_factor, m_lacunarity, m_octaves, m_offset, m_gain]

        for idx, vlist in enumerate(verts):
            # lazy generation of full parameters.
            params = [(param[idx] if idx < len(param) else param[-1]) for param in param_list]
            out.append([fractal_function(_noise_type, v, *params) for v in vlist])

        outputs[0].sv_set(out)


def register():
    bpy.utils.register_class(SvVectorFractal)


def unregister():
    bpy.utils.unregister_class(SvVectorFractal)
