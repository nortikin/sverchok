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

from mathutils import Vector
import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty, BoolProperty

import blf
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.utils.context_managers import sv_preferences
from sverchok.data_structure import updateNode, node_id, enum_item_4
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL

# star imports easing_dict and all easing functions.
from sverchok.utils.sv_easing_functions import *

easing_list = []
for k in sorted(easing_dict.keys()):
    fname = easing_dict[k].__name__
    easing_list.append(tuple([str(k), fname, "", k]))


palette_dict = {
    "default": (
        (0.243299, 0.590403, 0.836084, 1.00),  # back_color
        (0.390805, 0.754022, 1.000000, 0.70),  # grid_color
        (1.000000, 0.330010, 0.107140, 1.00)   # line_color
    ),
    "scope": (
        (0.274677, 0.366253, 0.386430, 1.00),  # back_color
        (0.423268, 0.558340, 0.584078, 1.00),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    ),
    "sniper": (
        (0.2, 0.2, 0.2, 0.20),  # back_color
        (0.423268, 0.558340, 0.584078, 0.40),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    )
}


def simple28_grid_xy(x, y, args):
    """ x and y are passed by default so you could add font content """

    geom, config = args
    back_color, grid_color, line_color = config.palette

    # draw background, this could be cached......
    shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    batch = batch_for_shader(shader, 'TRIS', {"pos": geom.background_coords}, indices=geom.background_indices)
    shader.bind()
    shader.uniform_float("color", back_color)
    batch.draw(shader)

    # draw grid and graph
    config.batch.draw(config.shader)



class SvEasingNode(bpy.types.Node, SverchCustomTreeNode):
    '''Curved interpolation'''
    bl_idname = 'SvEasingNode'
    bl_label = 'Easing 0..1'
    sv_icon = 'SV_EASING'

    n_id: StringProperty(default='')

    activate: BoolProperty(
        name='Show', description='Activate drawing',
        default=True, update=updateNode
    )

    selected_mode: EnumProperty(
        items=easing_list, description="Set easing Function to:",
        default="0", update=updateNode
    )

    in_float: FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='input to the easy function', update=updateNode
    )

    selected_theme_mode: EnumProperty(
        items=enum_item_4(["default", "scope", "sniper"]), default="default", update=updateNode
    )

    def custom_draw_socket(self, socket, context, l):
        info = socket.get_socket_info()

        r = l.row(align=True)
        split = r.split(factor=0.85)
        r1 = split.row(align=True)
        r1.prop(self, "selected_mode", text="")
        r1.prop(self, 'activate', icon='NORMALIZE_FCURVES', text="")
        if info:
            r2 = split.row()
            r2.label(text=info)

    def draw_buttons_ext(self, context, l):
        l.prop(self, "selected_theme_mode")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Float").prop_name = 'in_float'
        self.outputs.new('SvStringsSocket', "Float").custom_draw = 'custom_draw_socket'
        self.get_and_set_gl_scale_info()

    def get_drawing_attributes(self):
        """
        adjust render location based on preference multiplier setting
        """
        x, y = [int(j) for j in (Vector(self.absolute_location) + Vector((self.width + 20, 0)))[:]]

        try:
            with sv_preferences() as prefs:
                multiplier = prefs.render_location_xy_multiplier
                scale = prefs.render_scale
        except:
            # print('did not find preferences - you need to save user preferences')
            multiplier = 1.0
            scale = 1.0
        x, y = [x * multiplier, y * multiplier]

        return x, y, scale, multiplier

    def generate_shader(self, geom):
        shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": geom.vertices, "color": geom.vertex_colors}, indices=geom.indices)
        return batch, shader

    def generate_graph_geom(self, config):

        geom = lambda: None
        x, y = config.loc
        size = 140 * config.scale
        back_color, grid_color, line_color = config.palette
        easing_func = config.easing_func

        # background geom
        w = size
        h = size
        geom.background_coords = [(x, y), (x + w, y), (w + x, y - h), (x, y - h)]
        geom.background_indices = [(0, 1, 2), (0, 2, 3)]

        # grid geom and associated vertex colors
        num_divs = 8
        offset = size / num_divs

        vertices = []
        vertex_colors = []
        indices = []
        for i in range(num_divs + 1):
            xpos1 = x + (i * offset)
            ypos1 = y
            ypos2 = y - size
            vertices.extend([[xpos1, ypos1], [xpos1, ypos2]])

            ypos = y - (i * offset)
            vertices.extend([[x, ypos], [x + size, ypos]])
            vertex_colors.extend([grid_color,] * 4)

        for i in range(0, (num_divs+1)*4, 2):
            indices.append([i, i+1])


        # graph-line geom and associated vertex colors
        idx_offset = len(vertices)
        graphline = []
        num_points = 100
        seg_diff = 1 / num_points
        for i in range(num_points+1):
            _px = x + ((i * seg_diff) * size)
            _py = y - (1 - easing_func(i * seg_diff) * size) - size
            graphline.append([_px, _py])
            vertex_colors.append(line_color)

        vertices.extend(graphline)

        for i in range(num_points):
            indices.append([idx_offset + i, idx_offset + i + 1])

        geom.vertices = vertices
        geom.vertex_colors = vertex_colors
        geom.indices = indices
        return geom

    def process(self):
        p = self.inputs['Float'].sv_get()
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)

        float_out = self.outputs['Float']
        easing_func = easing_dict.get(int(self.selected_mode))
        if float_out.is_linked:
            out = []
            for obj in p:
                r = []
                for i in obj:
                    r.append(easing_func(i))
                out.append(r)
            float_out.sv_set(out)
        else:
            float_out.sv_set([[None]])

        if self.activate:

            config = lambda: None
            x, y, scale, multiplier = self.get_drawing_attributes()

            config.loc = (x, y)
            config.palette = palette_dict.get(self.selected_theme_mode)[:]
            config.scale = scale
            config.easing_func = easing_func

            geom = self.generate_graph_geom(config)
            config.batch, config.shader = self.generate_shader(geom)

            draw_data = {
                'mode': 'custom_function',
                'tree_name': self.id_data.name[:],
                'loc': (x, y),
                'custom_function': simple28_grid_xy,
                'args': (geom, config)
            }
            nvBGL.callback_enable(n_id, draw_data)

    def free(self):
        nvBGL.callback_disable(node_id(self))

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def sv_update(self):
        # handle disconnecting sockets, also disconnect drawing to view?
        if not ("Float" in self.inputs):
            return
        try:
            if not self.inputs[0].other:
                nvBGL.callback_disable(node_id(self))
        except:
            print('Easing node update holdout (not a problem)')


classes = [SvEasingNode,]
register, unregister = bpy.utils.register_classes_factory(classes)
