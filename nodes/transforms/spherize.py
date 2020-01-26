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
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, StringProperty, BoolProperty
from mathutils import Vector, Matrix, Color
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, iter_list_match_func, numpy_list_match_func
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.color_utils import color_channels


def meshes_texture_diplace(params, constant, matching_f):
    '''
    This function prepares the data to pass to the different displace functions.

    params are verts, pols, texture, scale_out, matrix, size, strength, axis
    - verts, scale_out, and axis should be list as [[[float, float, float],],] (Level 3)
    - pols should be list as [[[int, int, int, ...],],] (Level 3)
    - texture can be [texture, texture] or [[texture, texture],[texture]] for per vertex texture
    - matrix can be [matrix, matrix] or [[matrix, matrix],[texture]] for per vertex matrix,
            in case of UV Coors in mapping_mode it should be [[[float, float, float],],] (Level 3)
    size and strength should be list as [[float, float, ..], [float, ..], ..] (Level 2)
    desired_levels = [3, 3, 2, 2, 2 or 3, 2, 2, 3]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    center_mode, match_mode, size_mode = constant
    params = matching_f(params)
    local_match = numpy_list_match_func[match_mode]

    for props in zip(*params):
        verts, sphere_scale, axis_scale, origin, size, strength = local_match([np.array(p) for p in props])
        if center_mode == 'AVERAGE':
            origin = (np.sum(verts, axis=0)/verts.shape[0])[np.newaxis, :]

        np_verts_c = verts - origin
        mag = np.linalg.norm(np_verts_c, axis=1)

        if size_mode == 'AVERAGE':
            size = np.sum(mag)/mag.shape[0]

        else:
            size = size[:, np.newaxis]
        # sphere
        verts_normalized = np_verts_c/mag[:, np.newaxis] * size * sphere_scale + origin
        # cilinder

        ang = np.arctan2(np_verts_c[:,1],np_verts_c[:,0])
        x = np.cos(ang)
        y = np.sin(ang)
        z = np_verts_c[:,2]
        verts_normalized = np.stack((x,y,z)).T * size * sphere_scale + origin
        # cuboid
        y= np.interp(ang,[-np.pi,-np.pi/2,0, np.pi/2, np.pi],[0, -1, 0, 1, 0])
        x= np.interp(ang,[-np.pi,-np.pi/2,0, np.pi/2, np.pi],[-1, 0, 1, 0, -1])
        z = np_verts_c[:,2]
        verts_normalized = np.stack((x,y,z)).T * size * sphere_scale + origin
        verts_out = verts + (verts_normalized - verts) * strength[:, np.newaxis] * axis_scale

        result.append(verts_out .tolist())

    return result






class SvSpherizeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Add texture to verts
    Tooltip: Affect input verts/mesh with a scene texture. Mimics Blender Displace modifier

    """

    bl_idname = 'SvSpherizeNode'
    bl_label = 'Spherize'
    bl_icon = 'MOD_DISPLACE'

    origin_modes = [
        ('AVERAGE', 'Average', 'Texture displacement along Vertex Normal', '', 1),
        ('EXTERNAL', 'External', 'Texture displacement along X axis', '', 2),
        ]

    size_modes = [
        ('AVERAGE', 'Average', 'Input UV coordinates to evaluate texture', '', 1),
        ('EXTERNAL', 'Defined', 'Matrix to apply to verts before evaluating texture', '', 2),
    ]
    @throttled
    def handle_size_socket(self, context):
        input = self.inputs['Size']
        if self.size_mode == 'AVERAGE':
            if not input.hide_safe:
                input.hide_safe = True
        else:
            if input.hide_safe:
                input.hide_safe = False

    @throttled
    def handle_origin_socket(self, context):
        input = self.inputs['Origin']
        if self.origin_mode == 'AVERAGE':
            if not input.hide_safe:
                input.hide_safe = True
        else:
            if input.hide_safe:
                input.hide_safe = False

    use_x: BoolProperty(
        name="X", description="smooth vertices along X axis",
        default=True, update=updateNode)

    use_y: BoolProperty(
        name="Y", description="smooth vertices along Y axis",
        default=True, update=updateNode)

    use_z: BoolProperty(
        name="Z", description="smooth vertices along Z axis",
        default=True, update=updateNode)

    origin_mode: EnumProperty(
        name='Direction',
        items=origin_modes,
        default='AVERAGE',
        description='Apply Mode',
        update=handle_origin_socket)

    size_mode: EnumProperty(
        name='Size_mode',
        items=size_modes,
        default='AVERAGE',
        description="Mapping method",
        update=handle_size_socket)

    origin: FloatVectorProperty(
        name='Origin', description='Scale of the added vector',
        size=3, default=(1, 1, 1),
        update=updateNode)

    scale_out_v: FloatVectorProperty(
        name='Axis Scale Out', description='Scale of the added vector',
        size=3, default=(1, 1, 1),
        update=updateNode)

    sphere_axis_scale: FloatVectorProperty(
        name='Sphere Scale', description='Scale base sphere',
        size=3, default=(1, 1, 1),
        update=updateNode)

    strength: FloatProperty(
        name='Strength', description='Stength of the effect',
        default=1.0, update=updateNode)

    size: FloatProperty(
        name='Size', description='Size the sphere',
        default=1.0, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):

        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvVerticesSocket', 'Sphere Scale').prop_name = 'sphere_axis_scale'
        self.inputs.new('SvVerticesSocket', 'Axis Scale Out').prop_name = 'scale_out_v'
        self.inputs.new('SvVerticesSocket', 'Origin').prop_name = 'origin'
        self.inputs.new('SvStringsSocket', 'Size').prop_name = 'size'
        self.inputs.new('SvStringsSocket', 'Strength').prop_name = 'strength'
        self.inputs['Origin'].hide_safe = True
        self.inputs['Size'].hide_safe = True

        self.outputs.new('SvVerticesSocket', 'Vertices')


    def draw_buttons(self, context, layout):
        layout.prop(self, 'origin_mode', expand=False, text='Origin')
        layout.prop(self, 'size_mode', expand=False, text='Size')

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

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs]


        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 3, 3, 3, 2, 2]
        ops = [self.origin_mode, self.list_match, self.size_mode]

        result = recurse_f_level_control(params, ops, meshes_texture_diplace, matching_f, desired_levels)

        self.outputs[0].sv_set(result)

classes = [SvSpherizeNode]
register, unregister = bpy.utils.register_classes_factory(classes)
