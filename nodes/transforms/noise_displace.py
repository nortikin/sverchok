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
from bpy.props import EnumProperty, IntProperty, FloatVectorProperty, BoolProperty
from mathutils import noise, Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, list_match_func, numpy_list_match_modes, iter_list_match_func, numpy_full_list_func)
from sverchok.utils.sv_noise_utils import noise_options, noise_numpy_types
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
import numpy as np


def matrix_apply_np(verts, matrix):
    '''taken from https://blender.stackexchange.com/a/139517'''

    verts_co_4d = np.ones(shape=(verts.shape[0], 4), dtype=np.float)
    verts_co_4d[:, :-1] = verts  # cos v (x,y,z,1) - point,   v(x,y,z,0)- vector
    return np.einsum('ij,aj->ai', matrix, verts_co_4d)[:, :-1]


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


def v_noise(verts, _, m_prop, noise_type, result, output_numpy):
    py_verts = verts.tolist() if isinstance(verts, np.ndarray) else verts
    func = vector_noise if len(m_prop) == 2 else vector_noise_multi_seed
    if output_numpy:
        result.append(
            np.array(
                [func(v_prop, noise_basis=noise_type)[:] for v_prop in zip(py_verts, *m_prop)]
                )
            )
    else:
        result.append([func(v_prop, noise_basis=noise_type)[:] for v_prop in zip(py_verts, *m_prop)])

def v_noise_numpy(verts, _, noise_type, n_props, result, output_numpy):
    scale, seed, matrix, smooth, interpolate = n_props
    noise_function = noise_numpy_types[noise_type][interpolate]
    smooth = smooth
    np_verts = np.array(verts)
    distorted_v = matrix_apply_np(np_verts, matrix)

    n_v = np.stack((
        noise_function(distorted_v, seed, smooth),
        noise_function(distorted_v, seed+1, smooth),
        noise_function(distorted_v, seed+2, smooth)
        )).T

    if output_numpy:
        result.append(np_verts +  (2 * n_v - 1) * scale)
    else:
        result.append((np_verts +  (2 * n_v - 1) * scale).tolist())

def v_normal(verts, pols, m_prop, noise_type, result, output_numpy):
    py_verts = verts.tolist() if isinstance(verts, np.ndarray) else verts
    bm = bmesh_from_pydata(py_verts, [], pols, normal_update=True)
    normals = [Vector(v.normal) for v in bm.verts]
    func = vector_noise_normal if len(m_prop) == 2 else vector_noise_normal_multi_seed
    if output_numpy:
        result.append(
            np.array(
                [func(v_prop, noise_basis=noise_type)[:] for v_prop in zip(py_verts, *m_prop, normals)]
                )
            )
    else:
        result.append([func(v_prop, noise_basis=noise_type)[:] for v_prop in zip(verts, *m_prop, normals)])

    bm.free()

def v_normal_numpy(verts, pols, noise_type, n_props, result, output_numpy):
    bm = bmesh_from_pydata(verts, [], pols, normal_update=True)
    normals = np.array([v.normal for v in bm.verts])
    scale, seed, matrix, smooth, interpolate = n_props
    noise_function = noise_numpy_types[noise_type][interpolate]
    smooth = smooth
    np_verts = np.array(verts)
    n_v = noise_function(matrix_apply_np(np_verts, matrix), seed, smooth)
    if output_numpy:
        result.append(np_verts + normals * n_v[:, np.newaxis] * scale)
    else:
        result.append((np_verts + normals * n_v[:, np.newaxis] * scale).tolist())
    bm.free()

def noise_displace(params, constant, matching_f):
    result = []
    noise_function, noise_type, _, _, match_mode, output_numpy = constant
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
        noise_function(verts, pols, m_prop, noise_type, result, output_numpy)

    return result


def noise_displace_numpy(params, constant, matching_f):
    result = []
    noise_function, noise_type, smooth, interpolate, match_mode, output_numpy = constant
    params = matching_f(params)
    local_match = numpy_full_list_func[match_mode]
    for props in zip(*params):
        verts, pols, seed_val, scale_out, matrix = props
        np_scale = local_match(np.array(scale_out), len(verts))
        if type(matrix) == list:
            matrix = matrix[0].inverted()
        else:
            matrix = matrix.inverted()

        n_props = [np_scale, seed_val[0], matrix, smooth, interpolate]
        noise_function(verts, pols, noise_type, n_props, result, output_numpy)

    return result


avail_noise = [(t[0], t[0].title(), t[0].title(), '', t[1]) for t in noise_options]

for idx, new_type in enumerate(noise_numpy_types.keys()):
    avail_noise.append((new_type, new_type.title().replace('_', ' '), new_type.title(), '', 100 + idx))

noise_func = {'NORMAL': v_normal, 'VECTOR': v_noise}
noise_func_numpy = {'NORMAL': v_normal_numpy, 'VECTOR': v_noise_numpy}

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

    smooth: BoolProperty(
        name='Smooth',
        description='Smooth noise',
        default=True, update=updateNode)

    interpolate: BoolProperty(
        name='Interpolate',
        description='Interpolate gradients',
        default=True, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

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
        if self.noise_type in noise_numpy_types.keys():
            row = layout.row(align=True)
            row.prop(self, 'smooth', toggle=True)
            row.prop(self, 'interpolate', toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, "output_numpy", toggle=False)
        layout.prop(self, 'list_match', expand=False)

    def rclick_menu(self, context, layout):
        if self.noise_type in noise_numpy_types.keys():
            layout.prop(self, 'smooth', toggle=True)
            layout.prop(self, 'interpolate', toggle=True)
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.prop(self, "output_numpy", toggle=True)


    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs[:4]]
        params.append(inputs[4].sv_get(default=[Matrix()], deepcopy=False))

        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 3, 2, 3, 2]
        if self.noise_type in noise_numpy_types.keys():
            main_func = noise_displace_numpy
            noise_function = noise_func_numpy[self.out_mode]
        else:
            main_func = noise_displace
            noise_function = noise_func[self.out_mode]
        ops = [noise_function, self.noise_type, self.smooth, self.interpolate, self.list_match, self.output_numpy]
        result = recurse_f_level_control(params, ops, main_func, matching_f, desired_levels)

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
