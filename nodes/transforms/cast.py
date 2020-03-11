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
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty
import numpy as np
from numpy import pi
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func, no_space
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.modules.vector_math_utils import angle_between

def sphere_points(np_verts_c, mag):
    return np_verts_c/mag[:, np.newaxis]

def cylinder_points(np_verts_c, sides):
    ang = np.arctan2(np_verts_c[:, 1], np_verts_c[:, 0])
    div = np.cos((ang + pi/sides) % (2 * pi / sides) - pi / sides)
    div[sides < 2] = 1
    x_co = np.cos(ang) / div
    y_co = np.sin(ang) / div
    z_co = np_verts_c[:, 2]
    return np.stack((x_co, y_co, z_co)).T


def prism_points(np_verts_c, sides):
    ang = np.arctan2(np_verts_c[:, 1], np_verts_c[:, 0])
    ang2 = angle_between(np_verts_c, [[0, 0, 1]])
    div2 = np.cos((ang2 + pi/4) % (pi/2) - pi/4)
    div = np.cos((ang + pi/sides) % (2*pi/sides) - pi/sides) *div2
    div[sides < 2] = 1
    x_co = np.cos(ang)*np.sin(ang2)/div
    y_co = np.sin(ang)*np.sin(ang2)/div
    z_co = np.cos(ang2)/div2
    return np.stack((x_co, y_co, z_co)).T

def uv_sphere_points(np_verts_c, u_sides, v_sides):
    ang = np.arctan2(np_verts_c[:, 1], np_verts_c[:, 0])
    ang2 = angle_between(np_verts_c, [[0, 0, 1]])
    div2 = np.cos((ang2) % (pi/v_sides) - pi/v_sides/2) / np.cos(pi/v_sides/2)
    div2[v_sides < 1] = 1
    div = np.cos((ang)%(2*pi/u_sides)-pi/u_sides) *div2 / np.cos(pi/u_sides)
    div[u_sides < 2] = 1
    x_co = np.cos(ang)*np.sin(ang2)/div
    y_co = np.sin(ang)*np.sin(ang2)/div
    z_co = np.cos(ang2)/div2
    return np.stack((x_co, y_co, z_co)).T

def cast_meshes(params, constant, matching_f):
    '''
    This function prepares the data to pass to the different cast functions.

    params are verts, base_scale, effect_scale, size, strength, size, u_sides, v_sides
    - verts, base_scale, effect_scale and origin should be list as [[[float, float, float],],] (Level 3)
    - size and strength should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    - u_sides and v_sides should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 3, 3, 2, 2, 2, 2]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    cast_shape, center_mode, match_mode, size_mode, output_numpy = constant
    params = matching_f(params)
    cast_func = CAST_FORMULAS[cast_shape]
    local_match = numpy_list_match_func[match_mode]

    for props in zip(*params):
        verts, base_scale, effect_scale, origin, size, strength, u_sides, v_sides = local_match([np.array(p) for p in props])
        if center_mode == 'AVERAGE':
            origin = (np.sum(verts, axis=0)/verts.shape[0])[np.newaxis, :]
        np_verts_c = verts - origin
        mag = np.linalg.norm(np_verts_c, axis=1)

        if size_mode == 'AVERAGE':
            size = np.sum(mag)/mag.shape[0]
        else:
            size = size[:, np.newaxis]
        if cast_shape == 'UV_Sphere':
            sub_props = [np_verts_c, u_sides, v_sides]
        elif cast_shape == 'Sphere':
            sub_props = [np_verts_c, mag]
        elif cast_shape == 'Prism':
            sub_props = [np_verts_c, u_sides]
        else:
            sub_props = [np_verts_c, u_sides]


        verts_normalized = cast_func(*sub_props) * size * base_scale + origin
        verts_out = verts + (verts_normalized - verts) * strength[:, np.newaxis] * effect_scale

        result.append(verts_out if output_numpy else verts_out.tolist())

    return result


CAST_FORMULAS = {
    'Sphere': sphere_points,
    'Cylinder': cylinder_points,
    'Prism': prism_points,
    'UV_Sphere': uv_sphere_points
    }



class SvCastNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: To Sphere, Prism, Cylinder
    Tooltip: Affect input verts/mesh with a scene texture. Mimics Blender Displace modifier

    """

    bl_idname = 'SvCastNode'
    bl_label = 'Cast'
    bl_icon = 'MOD_CAST'

    origin_modes = [
        ('AVERAGE', 'Average', 'Texture displacement along Vertex Normal', '', 1),
        ('EXTERNAL', 'External', 'Texture displacement along X axis', '', 2),
        ]

    size_modes = [
        ('AVERAGE', 'Average', 'Input UV coordinates to evaluate texture', '', 1),
        ('EXTERNAL', 'Defined', 'Matrix to apply to verts before evaluating texture', '', 2),
    ]

    cast_modes = [(t, t.replace('_', ' '), 'Cast to ' + t.replace('_', ' '), '', id) for id, t in enumerate(CAST_FORMULAS)]

    @throttled
    def handle_size_socket(self, context):
        input_socket = self.inputs['Size']
        if self.size_mode == 'AVERAGE':
            if not input_socket.hide_safe:
                input_socket.hide_safe = True
        else:
            if input_socket.hide_safe:
                input_socket.hide_safe = False

    @throttled
    def handle_origin_socket(self, context):
        input_socket = self.inputs['Origin']
        if self.origin_mode == 'AVERAGE':
            if not input_socket.hide_safe:
                input_socket.hide_safe = True
        else:
            if input_socket.hide_safe:
                input_socket.hide_safe = False

    @throttled
    def handle_uv_sockets(self, context):
        u_socket = self.inputs['U']
        v_socket = self.inputs['V']
        if self.cast_mode == 'Sphere':
            u_socket.hide_safe = True
            v_socket.hide_safe = True
        elif self.cast_mode in ['Cylinder', 'Prism']:
            v_socket.hide_safe = True
            if u_socket.hide_safe:
                u_socket.hide_safe = False
        else:
            if u_socket.hide_safe:
                u_socket.hide_safe = False
            if v_socket.hide_safe:
                v_socket.hide_safe = False

    cast_mode: EnumProperty(
        name='Cast Type',
        items=cast_modes,
        default='Sphere',
        description='Shape to cast',
        update=handle_uv_sockets)

    origin_mode: EnumProperty(
        name='Origin',
        items=origin_modes,
        default='AVERAGE',
        description='Origin of base mesh',
        update=handle_origin_socket)

    size_mode: EnumProperty(
        name='Size_mode',
        items=size_modes,
        default='AVERAGE',
        description="Size of base mesh",
        update=handle_size_socket)

    origin: FloatVectorProperty(
        name='Origin', description='Origin of the base mesh',
        size=3, default=(0, 0, 0),
        update=updateNode)

    scale_out_v: FloatVectorProperty(
        name='Effect Scale', description='Scale of the added vector',
        size=3, default=(1, 1, 1),
        update=updateNode)

    sphere_axis_scale: FloatVectorProperty(
        name='Shape Scale', description='Scale base shape',
        size=3, default=(1, 1, 1),
        update=updateNode)

    strength: FloatProperty(
        name='Strength', description='Stength of the effect',
        default=1.0, update=updateNode)

    size: FloatProperty(
        name='Size', description='Size the sphere',
        default=1.0, update=updateNode)

    U_div: FloatProperty(
        name='Meridians', description='Meridians of the UV sphere. If less than 2 -> circular',
        default=4.0, update=updateNode)
    V_div: FloatProperty(
        name='Parallels', description='Paralels of the UV sphere. If less than 2 -> circular',
        default=4.0, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):

        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvVerticesSocket', 'Shape Scale').prop_name = 'sphere_axis_scale'
        self.inputs.new('SvVerticesSocket', 'Effect Scale').prop_name = 'scale_out_v'
        self.inputs.new('SvVerticesSocket', 'Origin').prop_name = 'origin'
        self.inputs.new('SvStringsSocket', 'Size').prop_name = 'size'
        self.inputs.new('SvStringsSocket', 'Strength').prop_name = 'strength'
        self.inputs.new('SvStringsSocket', 'U').prop_name = 'U_div'
        self.inputs.new('SvStringsSocket', 'V').prop_name = 'V_div'
        self.inputs['Origin'].hide_safe = True
        self.inputs['Size'].hide_safe = True
        self.inputs['U'].hide_safe = True
        self.inputs['V'].hide_safe = True

        self.outputs.new('SvVerticesSocket', 'Vertices')


    def draw_buttons(self, context, layout):
        layout.prop(self, 'cast_mode', expand=False, text='To')
        layout.prop(self, 'origin_mode', expand=False, text='Origin')
        layout.prop(self, 'size_mode', expand=False, text='Size')

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, 'output_numpy')
        layout.prop(self, 'list_match', expand=False)

    def rclick_menu(self, context, layout):
        layout.prop(self, 'output_numpy')
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def draw_label(self):
        return self.label or self.name + ' to ' + self.cast_mode.title()

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs]

        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 3, 3, 3, 2, 2, 2, 2]
        ops = [self.cast_mode, self.origin_mode, self.list_match, self.size_mode, self.output_numpy]

        result = recurse_f_level_control(params, ops, cast_meshes, matching_f, desired_levels)

        self.outputs[0].sv_set(result)

classes = [SvCastNode]
register, unregister = bpy.utils.register_classes_factory(classes)
