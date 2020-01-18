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
import bpy
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, StringProperty
from mathutils import Vector, Matrix, Color

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, iter_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

class EmptyTexture():
    def evaluate(self, vec):
        return [1, 1, 1, 1]

def end_vector(vertex, eval_v, mid_level, strength, scale_out):
    vx = eval_v[0]
    vy = (eval_v[1] - mid_level) * strength * scale_out[1]
    vz = (eval_v[2] - mid_level) * strength * scale_out[2]
    return [vx, vy, vz]

def texture_displace_rgb(params):
    vertex, texture = params
    v_vertex = Vector(vertex)
    eval_v = texture.evaluate(v_vertex)[:]
    return eval_v


def texture_displace_hsv(params):
    vertex, texture = params
    v_vertex = Vector(vertex)
    eval_v = Color(texture.evaluate(v_vertex)[:3]).hsv
    return eval_v

def texture_displace_hls(params):
    vertex, texture = params
    v_vertex = Vector(vertex)
    eval_v = rgb_to_hls(*texture.evaluate(v_vertex)[:3])
    return eval_v



def texture_displace_vector_channel(params, extract_func):
    vertex, texture = params
    v_vertex = Vector(vertex)
    col = texture.evaluate(v_vertex)
    eval_s = extract_func(col)
    return eval_s


def apply_texture_displace_rgb(verts, m_prop, channel, result):
    func = texture_displace_rgb
    result.append([func(v_prop) for v_prop in zip(verts, *m_prop)])


def apply_texture_displace_hsv(verts, m_prop, channel, result):
    func = texture_displace_hsv
    result.append([func(v_prop) for v_prop in zip(verts, *m_prop)])

def apply_texture_displace_hls(verts, m_prop, channel, result):
    func = texture_displace_hls
    result.append([func(v_prop) for v_prop in zip(verts, *m_prop)])


def apply_texture_displace_axis_x(verts, m_prop, channel, result):
    apply_texture_displace_axis(verts, m_prop, channel, result)


def apply_texture_displace_axis_y(verts, m_prop, channel, result):
    apply_texture_displace_axis(verts, m_prop, channel, result)


def apply_texture_displace_axis_z(verts, m_prop, channel, result):
    apply_texture_displace_axis(verts, m_prop, channel, result)

def apply_texture_displace_axis_custom(verts, m_prop, channel, result):
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, extract_func) for v_prop in zip(verts, *m_prop)])

def apply_texture_displace_axis(verts, m_prop, channel, result):
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, extract_func) for v_prop in zip(verts, *m_prop)])



def apply_texture_displace_normal(verts, m_prop, channel, result):
    func = texture_displace_vector_channel
    extract_func = color_channels[channel][1]
    result.append([func(v_prop, extract_func) for v_prop in zip(verts, *m_prop)])


def meshes_texture_diplace(params, constant, matching_f):
    result = []
    displace_function, color_channel, match_mode = constant
    params = matching_f(params)
    local_match = iter_list_match_func[match_mode]
    for props in zip(*params):
        verts, texture = props
        if  not type(texture) == list:
            texture = [texture]

        m_prop = local_match([texture])
        displace_function(verts, m_prop, color_channel, result)

    return result

color_channels = {
    'RED':        (1, lambda x: x[0]),
    'GREEN':      (2, lambda x: x[1]),
    'BLUE':       (3, lambda x: x[2]),
    'HUE':        (4, lambda x: Color(x[:3]).h),
    'SATURATION': (5, lambda x: Color(x[:3]).s),
    'VALUE':      (6, lambda x: Color(x[:3]).v),
    'ALPHA':      (7, lambda x: x[3]),
    'RGB AVERAGE':(8, lambda x: sum(x[:3])/3),
    'LUMINOSITY': (9, lambda x: 0.21*x[0] + 0.72*x[1] + 0.07*x[2])
    }

color_channels_modes = [(t, t.title(), t.title(), '', color_channels[t][0]) for t in color_channels]

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

mapper_funcs = {
    'UV': lambda v, v_uv: Vector((v_uv[0]*2-1, v_uv[1]*2-1, v_uv[2])),
    'Mesh Matrix': lambda v, m: m @ v,
    'Texture Matrix': lambda v, m: m @ v
}

class SvTextureEvaluateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Add Noise to verts
    Tooltip: Affect input verts/mesh with a noise values.

    """

    bl_idname = 'SvTextureEvaluateNode'
    bl_label = 'Displace'
    bl_icon = 'FORCE_TURBULENCE'
    sv_icon = 'SV_VECTOR_NOISE'

    out_modes = [
        ('NORMAL', 'Single Channel', 'Texture displacement along Vertex Normal', '', 1),
        ('RGB to XYZ', 'RGB', 'Texture displacement with RGB as vector', '', 2),
        ('HSV to XYZ', 'HSV', 'Texture displacement with HSV as vector', '', 3),
        ('HLS to XYZ', 'HLS', 'Texture displacement with HSV as vector', '', 4)]

    texture_coord_modes = [
        ('UV', 'UV coords', 'Input UV coordinates to evaluate texture', '', 1),
        ('Mesh Matrix', 'Mesh Matrix', 'Matrix to apply to verts before evaluating texture', '', 2),
        ('Texture Matrix', 'Texture Matrix', 'Matrix of texture (External Object matrix)', '', 3),

    ]
    @throttled
    def change_mode(self, context):
        outputs = self.outputs
        if self.out_mode not in ['RGB to XYZ', 'HSV to XYZ', 'HLS to XYZ']:
            outputs[0].replace_socket('SvStringsSocket', 'Scalar')
        else:
            outputs[0].replace_socket('SvColorSocket', self.out_mode.split(' ')[0])




    name_texture: StringProperty(
        name='image_name',
        description='image name',
        default='',
        update=updateNode)

    out_mode: EnumProperty(
        name='Direction',
        items=out_modes,
        default='NORMAL',
        description='Apply Mode',
        update=change_mode)

    color_channel: EnumProperty(
        name='Component',
        items=color_channels_modes,
        default='ALPHA',
        description="Channel to use from texture",
        update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Texture').custom_draw = 'draw_texture_socket'

        self.outputs.new('SvVerticesSocket', 'Vertices')


    def draw_texture_socket(self, socket, context, layout):
        if not socket.is_linked:
            layout.label(text=socket.name+ ':')
            layout.prop_search(self, "name_texture", bpy.data, 'textures', text="")
        else:
            layout.label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=False)
        if self.out_mode in ['NORMAL']:
            layout.prop(self, 'color_channel', text="Channel")


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
        params = []
        params.append(inputs[0].sv_get(default=[[]], deepcopy=False))
        if not inputs[1].is_linked:
            if not self.name_texture:
                params.append([[EmptyTexture()]])
            else:
                params.append([[bpy.data.textures[self.name_texture]]])
        else:
            params.append(inputs[1].sv_get(default=[[]], deepcopy=False))


        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 2]
        ops = [displace_funcs[self.out_mode], self.color_channel, self.list_match]

        result = recurse_f_level_control(params, ops, meshes_texture_diplace, matching_f, desired_levels)

        self.outputs[0].sv_set(result)



    def draw_label(self):
        if self.hide:
            if not self.inputs['Texture'].is_linked:
                texture = ' ' + self.name_texture
            else:
                texture = ' + texture(s)'
            return 'Displace' + texture +' ' + self.color_channel.title() + ' channel'
        else:
            return self.label or self.name

classes = [SvTextureEvaluateNode]
register, unregister = bpy.utils.register_classes_factory(classes)
