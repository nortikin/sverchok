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


from math import sqrt

import bpy
from bpy.props import EnumProperty, IntProperty, FloatVectorProperty
from mathutils import noise, Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_degenerate, list_match_func, numpy_list_match_modes, iter_list_match_func)
from sverchok.utils.sv_noise_utils import noise_options
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

def deepnoise(vert, noise_basis='PERLIN_ORIGINAL'):
    noise_v = noise.noise_vector(vert, noise_basis=noise_basis)[:]
    a = noise_v[0], noise_v[1], noise_v[2]-1   # a = noise_v minus (0,0,1)
    return sqrt((a[0] * a[0]) + (a[1] * a[1]) + (a[2] * a[2])) * 0.5

def vector_noise(params, noise_basis='PERLIN_ORIGINAL'):
    vert, scale_out, matrix = params
    v_vert = Vector(vert)
    noise_v = noise.noise_vector(matrix @ v_vert, noise_basis=noise_basis)[:]
    return v_vert + Vector((noise_v[0]*scale_out[0], noise_v[1]*scale_out[1], noise_v[2]*scale_out[2]))

def vector_noise_multi_seed(params, noise_basis='PERLIN_ORIGINAL'):
    vert, seed_val, scale_out, matrix = params
    noise.seed_set(seed_val if seed_val else 1385)
    v_vert = Vector(vert)
    noise_v = noise.noise_vector(matrix @ v_vert, noise_basis=noise_basis)[:]
    return v_vert + Vector((noise_v[0]*scale_out[0], noise_v[1]*scale_out[1], noise_v[2]*scale_out[2]))

def vector_noise_normal(params, noise_basis='PERLIN_ORIGINAL'):
    vert, scale_out, matrix, normal = params
    v_vert = Vector(vert)
    scalar_noise = deepnoise(matrix @ v_vert, noise_basis=noise_basis)
    noise_v = Vector(normal) * scalar_noise
    return v_vert + Vector((noise_v[0]*scale_out[0], noise_v[1]*scale_out[1], noise_v[2]*scale_out[2]))

def vector_noise_normal_multi_seed(params, noise_basis='PERLIN_ORIGINAL'):
    vert, seed_val, scale_out, matrix, normal = params
    v_vert = Vector(vert)
    noise.seed_set(seed_val if seed_val else 1385)
    noise_scalar = deepnoise(matrix @ v_vert, noise_basis=noise_basis)
    noise_v = Vector(normal) * noise_scalar
    return v_vert + Vector((noise_v[0]*scale_out[0], noise_v[1]*scale_out[1], noise_v[2]*scale_out[2]))

def v_noise(verts, pols, m_prop, noise_type, result):
    func = vector_noise if len(m_prop) == 2 else vector_noise_multi_seed
    result.append([func(v_prop, noise_basis=noise_type) for v_prop in zip(verts, *m_prop)])

def v_normal(verts, pols, m_prop, noise_type, result):
    bm = bmesh_from_pydata(verts, [], pols, normal_update=True)
    normals = [Vector(v.normal) for v in bm.verts]
    func = vector_noise_normal if len(m_prop) == 2 else vector_noise_normal_multi_seed
    result.append([func(v_prop, noise_basis=noise_type) for v_prop in zip(verts, *m_prop, normals)])
    bm.free()

def noise_displace(params, constant, matching_f):
    result = []
    noise_function, noise_type, match_mode = constant
    params = matching_f(params)
    local_match = iter_list_match_func[match_mode]
    for props in zip(*params):
        verts, pols, seed_val, scale_out, matrix = props
        if type(matrix) == list:
            matrix = [m.inverted() for m in matrix]
        else:
            matrix = [matrix.inverted()]
        if len(seed_val) > 1:
            m_prop = local_match([seed_val, scale_out, matrix])
        else:
            m_prop = local_match([scale_out, matrix])
            seed_val = seed_val[0]
            noise.seed_set(int(seed_val) if seed_val else 1385)
        noise_function(verts, pols, m_prop, noise_type, result)

    return Vector_degenerate(result)

avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]
noise_func = {'NORMAL': v_normal, 'VECTOR': v_noise}

class SvNoiseDisplaceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Add Noise to verts
    Tooltip: Move input verts/mesh with a noise values.

    """

    bl_idname = 'SvNoiseDisplaceNode'
    bl_label = 'Noise Displace'
    bl_icon = 'FORCE_TURBULENCE'

    out_modes = [
        ('NORMAL', 'Normal', 'Noise along Vertex Normal', '', 1),
        ('VECTOR', 'Vector', 'Add noise vector', '', 2)]


    out_mode: EnumProperty(
        items=out_modes,
        default='VECTOR',
        description='Apply Mode',
        update=updateNode)

    noise_type: EnumProperty(
        items=avail_noise,
        default='PERLIN_ORIGINAL',
        description="Noise type",
        update=updateNode)

    seed: IntProperty(default=0, name='Seed', update=updateNode)

    scale_out_v: FloatVectorProperty(
        name='Scale Out', description='Scale of the added vector',
        size=3, default=(1, 1, 1),
        update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'Seed').prop_name = 'seed'
        self.inputs.new('SvVerticesSocket', 'Scale Out').prop_name = 'scale_out_v'
        self.inputs.new('SvMatrixSocket', 'Noise Matrix')

        self.outputs.new('SvVerticesSocket', 'Vertices')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)
        layout.prop(self, 'noise_type', text="Type")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, 'list_match', expand=False)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs[:4]]
        params.append(inputs[4].sv_get(default=[Matrix()], deepcopy=False))

        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 3, 2, 3, 2]
        ops = [noise_func[self.out_mode], self.noise_type, self.list_match]
        result = recurse_f_level_control(params, ops, noise_displace, matching_f, desired_levels)

        self.outputs[0].sv_set(result)


    def draw_label(self):
        if self.hide:
            if not self.inputs['Seed'].is_linked:
                seed = ' + ({0})'.format(str(int(self.seed)))
            else:
                seed = ' + seed(s)'
            return self.noise_type.title() + seed
        else:
            return self.label or self.name

classes = [SvNoiseDisplaceNode]
register, unregister = bpy.utils.register_classes_factory(classes)
