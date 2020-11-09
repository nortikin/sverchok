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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.core.socket_data import SvGetSocketInfo
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, throttle_and_update_node
from sverchok.utils.sv_itertools import recurse_f_level_control
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.modules.color_utils import color_channels
from sverchok.utils.modules.texture_displace_utils import displace_funcs, meshes_texture_diplace

class EmptyTexture():
    def evaluate(self, vec):
        return [1, 1, 1, 1]

color_channels_modes = [(t.replace(" ", "_"), t, t, '', color_channels[t][0]) for t in color_channels]

mapper_funcs = {
    'UV': lambda v, v_uv: Vector((v_uv[0]*2-1, v_uv[1]*2-1, v_uv[2])),
    'Mesh Matrix': lambda v, m: m @ v,
    'Texture Matrix': lambda v, m: m @ v
}

class SvDisplaceNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    """
    Triggers: Add texture to verts
    Tooltip: Affect input verts/mesh with a scene texture. Mimics Blender Displace modifier

    """

    bl_idname = 'SvDisplaceNode'
    bl_label = 'Texture Displace'
    bl_icon = 'MOD_DISPLACE'

    replacement_nodes = [('SvDisplaceNodeMk2', None, None)]

    out_modes = [
        ('NORMAL', 'Normal', 'Texture displacement along Vertex Normal', '', 1),
        ('X', 'X', 'Texture displacement along X axis', '', 2),
        ('Y', 'Y', 'Texture displacement along Y axis', '', 3),
        ('Z', 'Z', 'Texture displacement along Z axis', '', 4),
        ('Custom_Axis', 'Custom Axis', 'Texture displacement along Custom Axis', '', 5),
        ('RGB_to_XYZ', 'RGB to XYZ', 'Texture displacement with RGB as vector', '', 6),
        ('HSV_to_XYZ', 'HSV to XYZ', 'Texture displacement with HSV as vector', '', 7),
        ('HLS_to_XYZ', 'HLS to XYZ', 'Texture displacement with HSV as vector', '', 8)]

    texture_coord_modes = [
        ('UV', 'UV', 'Input UV coordinates to evaluate texture', '', 1),
        ('Mesh_Matrix', 'Mesh Matrix', 'Matrix to apply to verts before evaluating texture', '', 2),
        ('Texture_Matrix', 'Texture Matrix', 'Matrix of texture (External Object matrix)', '', 3),

    ]
    @throttle_and_update_node
    def change_mode(self, context):
        inputs = self.inputs
        if self.tex_coord_type == 'Texture Matrix':
            if 'Texture Matrix' not in inputs:
                if 'UV coords' in inputs:
                    inputs[4].hide_safe = False
                inputs[4].replace_socket('SvMatrixSocket', 'Texture Matrix')

        elif self.tex_coord_type == 'Mesh Matrix':
            if 'Mesh Matrix' not in inputs:
                if 'UV coords' in inputs:
                    inputs[4].hide_safe = False
                inputs[4].replace_socket('SvMatrixSocket', 'Mesh Matrix')

        elif  self.tex_coord_type == 'UV':
            if 'UV Coordinates' not in inputs:
                inputs[4].hide_safe = False
                inputs[4].replace_socket('SvVerticesSocket', 'UV Coordinates')

    @throttle_and_update_node
    def change_direction_sockets(self, context):
        inputs = self.inputs
        if self.out_mode == 'Custom Axis':
            if inputs['Custom Axis'].hide_safe:
                inputs['Custom Axis'].hide_safe = False
        else:
            inputs['Custom Axis'].hide_safe = True


    name_texture: StringProperty(
        name='Texture',
        description='Texture(s) to evaluate',
        default='',
        update=updateNode)

    out_mode: EnumProperty(
        name='Direction',
        items=out_modes,
        default='NORMAL',
        description='Apply Mode',
        update=change_direction_sockets)

    color_channel: EnumProperty(
        name='Component',
        items=color_channels_modes[:9],
        default='Alpha',
        description="Channel to use from texture",
        update=updateNode)

    tex_coord_type: EnumProperty(
        name='Texture Coord',
        items=texture_coord_modes,
        default='Texture_Matrix',
        description="Mapping method",
        update=change_mode)

    scale_out_v: FloatVectorProperty(
        name='Axis Scale Out', description='Scale of the added vector',
        size=3, default=(1, 1, 1),
        update=updateNode)

    custom_axis: FloatVectorProperty(
        name='Custom Axis', description='Axis to use in displacement',
        size=3, default=(1, 1, 1),
        update=updateNode)

    strength: FloatProperty(
        name='Strength', description='Scalar displacement multiplier',
        default=1.0, update=updateNode)

    mid_level: FloatProperty(
        name='Middle Level', description='Texture middle level',
        default=0.0, update=updateNode)

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Polygons')
        self.inputs.new('SvStringsSocket', 'Texture').custom_draw = 'draw_texture_socket'
        self.inputs.new('SvVerticesSocket', 'Axis Scale Out').prop_name = 'scale_out_v'
        self.inputs.new('SvMatrixSocket', 'Texture Matrix')
        self.inputs.new('SvStringsSocket', 'Middle Level').prop_name = 'mid_level'
        self.inputs.new('SvStringsSocket', 'Strength').prop_name = 'strength'
        self.inputs.new('SvVerticesSocket', 'Custom Axis').prop_name = 'custom_axis'
        self.inputs['Custom Axis'].hide_safe = True

        self.outputs.new('SvVerticesSocket', 'Vertices')


    def draw_texture_socket(self, socket, context, layout):
        if not socket.is_linked:
            c = layout.split(factor=0.3, align=False)

            c.label(text=socket.name+ ':')
            c.prop_search(self, "name_texture", bpy.data, 'textures', text="")
        else:
            layout.label(text=socket.name+ '. ' + SvGetSocketInfo(socket))
    def draw_buttons(self, context, layout):
        is_vector = self.out_mode in ['RGB to XYZ', 'HSV to XYZ', 'HLS to XYZ']
        self.draw_animatable_buttons(layout, icon_only=True)
        c = layout.split(factor=0.5, align=False)
        r = c.column(align=False)
        r.label(text='Direction'+ ':')
        r.prop(self, 'out_mode', expand=False, text='')

        r = c.column(align=False)
        r.label(text='Texture Coord.'+ ':')
        r.prop(self, 'tex_coord_type', expand=False, text='')
        if not is_vector:
            r = layout.split(factor=0.3, align=False)
            r.label(text='Channel'+ ':')
            r.prop(self, 'color_channel', expand=False, text='')
        # layout.prop(self, 'tex_coord_type', text="Tex. Coord")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        self.draw_buttons(context, layout)
        layout.prop(self, 'list_match', expand=False)

    def rclick_menu(self, context, layout):
        self.node_replacement_menu(context, layout)
        layout.prop_menu_enum(self, "list_match", text="List Match")

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = [si.sv_get(default=[[]], deepcopy=False) for si in inputs[:4]]
        if not inputs[2].is_linked:
            if not self.name_texture:
                params[2] = [[EmptyTexture()]]

            else:
                params[2] = [[self.get_bpy_data_from_name(self.name_texture, bpy.data.textures)]]

        if not self.tex_coord_type == 'UV':
            params.append(inputs[4].sv_get(default=[Matrix()], deepcopy=False))
            mat_level = 2
        else:
            if inputs[4].is_linked:
                params.append(inputs[4].sv_get(default=[[]], deepcopy=False))
            else:
                params.append(params[0])
            mat_level = 3
        params.append(inputs[5].sv_get(default=[[]], deepcopy=False))
        params.append(inputs[6].sv_get(default=[[]], deepcopy=False))
        params.append(inputs[7].sv_get(default=[[]], deepcopy=False))

        matching_f = list_match_func[self.list_match]
        desired_levels = [3, 3, 2, 3, mat_level, 2, 2, 3]
        out_mode = self.out_mode.replace("_", " ")
        ops = [out_mode, displace_funcs[out_mode], self.color_channel.replace("_", " "), self.list_match, self.tex_coord_type.replace("_", " ")]

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

classes = [SvDisplaceNode]
register, unregister = bpy.utils.register_classes_factory(classes)
