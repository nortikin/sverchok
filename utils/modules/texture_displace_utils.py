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
from colorsys import rgb_to_hls
from itertools import repeat
from mathutils import Vector, Color

from sverchok.data_structure import  iter_list_match_func
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.color_utils import color_channels

mapper_funcs = {
    'UV': lambda v, v_uv: Vector((v_uv[0]*2-1, v_uv[1]*2-1, v_uv[2])),
    'Mesh Matrix': lambda v, m: m @ v,
    'Texture Matrix': lambda v, m: m @ v
}


def end_vector(vertex, eval_v, mid_level, strength, scale_out):
    vx = vertex[0] + (eval_v[0] - mid_level) * strength * scale_out[0]
    vy = vertex[1] + (eval_v[1] - mid_level) * strength * scale_out[1]
    vz = vertex[2] + (eval_v[2] - mid_level) * strength * scale_out[2]
    return [vx, vy, vz]

def texture_displace_rgb(params, mapper_func):
    vertex, texture, scale_out, matrix, mid_level, strength = params
    v_vertex = Vector(vertex)
    eval_v = texture.evaluate(mapper_func(v_vertex, matrix))[:]

    return end_vector(vertex, eval_v, mid_level, strength, scale_out)


def texture_displace_hsv(params, mapper_func):
    vertex, texture, scale_out, matrix, mid_level, strength = params
    v_vertex = Vector(vertex)
    eval_v = Color(texture.evaluate(mapper_func(v_vertex, matrix))[:3]).hsv
    return end_vector(vertex, eval_v, mid_level, strength, scale_out)


def texture_displace_hls(params, mapper_func):
    vertex, texture, scale_out, matrix, mid_level, strength = params
    v_vertex = Vector(vertex)
    eval_v = rgb_to_hls(*texture.evaluate(mapper_func(v_vertex, matrix))[:3])
    return end_vector(vertex, eval_v, mid_level, strength, scale_out)


def texture_displace_vector_channel(params, mapper_func, extract_func):
    vertex, texture, scale_out, matrix, mid_level, strength, normal = params
    v_vertex = Vector(vertex)
    col = texture.evaluate(mapper_func(v_vertex, matrix))
    eval_s = (extract_func(col) - mid_level) * strength

    vx = vertex[0] + normal[0] * eval_s * scale_out[0]
    vy = vertex[1] + normal[1] * eval_s * scale_out[1]
    vz = vertex[2] + normal[2] * eval_s * scale_out[2]
    return [vx, vy, vz]


def apply_texture_displace_rgb(verts, pols, m_prop, channel, mapper_func, result):
    func = texture_displace_rgb
    result.append([func(v_prop, mapper_func) for v_prop in zip(verts, *m_prop)])


def apply_texture_displace_hsv(verts, pols, m_prop, channel, mapper_func, result):
    func = texture_displace_hsv
    result.append([func(v_prop, mapper_func) for v_prop in zip(verts, *m_prop)])

def apply_texture_displace_hls(verts, pols, m_prop, channel, mapper_func, result):
    func = texture_displace_hls
    result.append([func(v_prop, mapper_func) for v_prop in zip(verts, *m_prop)])


def apply_texture_displace_axis_x(verts, pols, m_prop, channel, mapper_func, result):
    apply_texture_displace_axis(verts, pols, m_prop, channel, mapper_func, result, [1, 0, 0])


def apply_texture_displace_axis_y(verts, pols, m_prop, channel, mapper_func, result):
    apply_texture_displace_axis(verts, pols, m_prop, channel, mapper_func, result, [0, 1, 0])


def apply_texture_displace_axis_z(verts, pols, m_prop, channel, mapper_func, result):
    apply_texture_displace_axis(verts, pols, m_prop, channel, mapper_func, result, [0, 0, 1])

def apply_texture_displace_axis_custom(verts, pols, m_prop, channel, mapper_func, result):
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, mapper_func, extract_func) for v_prop in zip(verts, *m_prop[:-1], m_prop[-1])])

def apply_texture_displace_axis(verts, pols, m_prop, channel, mapper_func, result, axis):
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, mapper_func, extract_func) for v_prop in zip(verts, *m_prop, repeat(axis))])



def apply_texture_displace_normal(verts, pols, m_prop, channel, mapper_func, result):
    bm = bmesh_from_pydata(verts, [], pols, normal_update=True)
    normals = [v.normal for v in bm.verts]
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, mapper_func, extract_func) for v_prop in zip(verts, *m_prop, normals)])
    bm.free()

def meshes_texture_diplace(params, constant, matching_f):
    '''
    This function prepares the data to pass to the different displace functions.

    params are verts, pols, texture, scale_out, matrix, mid_level, strength, axis
    - verts, scale_out, and axis should be list as [[[float, float, float],],] (Level 3)
    - pols should be list as [[[int, int, int, ...],],] (Level 3)
    - texture can be [texture, texture] or [[texture, texture],[texture]] for per vertex texture
    - matrix can be [matrix, matrix] or [[matrix, matrix],[texture]] for per vertex matrix,
            in case of UV Coors in mapping_mode it should be [[[float, float, float],],] (Level 3)
    mid_level and strength should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 2, 3, 2 or 3, 2, 2, 3]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    displace_mode, displace_function, color_channel, match_mode, mapping_mode = constant
    params = matching_f(params)
    local_match = iter_list_match_func[match_mode]
    mapper_func = mapper_funcs[mapping_mode]
    for props in zip(*params):
        verts, pols, texture, scale_out, matrix, mid_level, strength, axis = props
        if mapping_mode == 'Texture Matrix':
            if type(matrix) == list:
                matrix = [m.inverted() for m in matrix]
            else:
                matrix = [matrix.inverted()]
        elif mapping_mode == 'Mesh Matrix':
            if not type(matrix) == list:
                matrix = [matrix]

        if  not type(texture) == list:
            texture = [texture]
        if displace_mode == 'Custom Axis':
            axis_n = [Vector(v).normalized() for v in axis]
            m_prop = local_match([texture, scale_out, matrix, mid_level, strength, axis_n])
        else:
            m_prop = local_match([texture, scale_out, matrix, mid_level, strength])
        displace_function(verts, pols, m_prop, color_channel, mapper_func, result)

    return result

displace_funcs = {
    'NORMAL': apply_texture_displace_normal,
    'X': apply_texture_displace_axis_x,
    'Y': apply_texture_displace_axis_y,
    'Z': apply_texture_displace_axis_z,
    'Custom Axis': apply_texture_displace_axis_custom,
    'RGB to XYZ': apply_texture_displace_rgb,
    'HSV to XYZ': apply_texture_displace_hsv,
    'HLS to XYZ': apply_texture_displace_hls
    }