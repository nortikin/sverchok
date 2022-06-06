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

import numpy as np
import pprint
import re
import bpy
import blf, bgl, gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import BoolProperty, FloatVectorProperty, StringProperty, IntProperty
from bpy.props import FloatProperty
from mathutils import Vector

from sverchok.settings import get_params
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode
from sverchok.ui import bgl_callback_nodeview as nvBGL

from sverchok.utils.sv_nodeview_draw_helper import (
    SvNodeViewDrawMixin, 
    get_console_grid, 
    advanced_parse_socket,
    advanced_text_decompose,
    )
from sverchok.nodes.viz.console_node import (
    simple_console_xy, 
    terminal_text_to_uv, 
    syntax_highlight_basic, 
    make_color, 
    process_grid_for_shader, 
    process_uvs_for_shader, 
    vertex_shader, 
    lexed_fragment_shader, 
    lexed_colors,
    random_color_chars, 
    get_font_pydata_location,
)


# status colors
FAIL_COLOR = (0.1, 0.05, 0)
READY_COLOR = (1, 0.3, 0)


def adjust_location(_x, _y, location_theta):
    return _x * location_theta, _y * location_theta

def get_xy_for_bgl_drawing(node):
    # adjust proposed text location in case node is framed.
    # take into consideration the hidden state
    node_width = node.width
    _x, _y = node.absolute_location
    _x, _y = Vector((_x, _y)) + Vector((node_width + 20, 0))

    # this alters location based on DPI/Scale settings.
    draw_location = adjust_location(_x, _y, node.location_theta)
    return draw_location

def parse_socket(socket, rounding, element_index, view_by_element, props):

    data = socket.sv_get(deepcopy=False)
    num_data_items = len(data)
    if num_data_items > 0 and view_by_element:
        if element_index < num_data_items:
            data = data[element_index]

    str_width = props.line_width

    # okay, here we should be more clever and extract part of the list
    # to avoid the amount of time it take to format it.
    
    content_str = pprint.pformat(data, width=str_width, depth=props.depth, compact=props.compact)
    content_array = content_str.split('\n')

    if len(content_array) > 20:
        ''' first 10, ellipses, last 10 '''
        ellipses = ['... ... ...']
        head = content_array[0:10]
        tail = content_array[-10:]
        display_text = head + ellipses + tail
    elif len(content_array) == 1:
        ''' split on subunit - case of no newline to split on. '''
        content_array = content_array[0].replace("), (", "),\n (")
        display_text = content_array.split("\n")
    else:
        display_text = content_array

    # http://stackoverflow.com/a/7584567/1243487
    rounded_vals = re.compile(r"\d*\.\d+")

    def mround(match):
        format_string = "{{:.{0}g}}".format(rounding)
        return format_string.format(float(match.group()))

    out = []
    for line in display_text:
        if (rounding == 0) or ("bpy." in line):
            out.append(line)
        else:
            out.append(re.sub(rounded_vals, mround, line))
    return out


def high_contrast_color(c):
    g = 2.2  # gamma
    L = 0.2126 * (c.r**g) + 0.7152 * (c.g**g) + 0.0722 * (c.b**g)
    return [(.1, .1, .1), (.95, .95, .95)][int(L < 0.5)]

def process_uvs_for_shader(node):
    uv_indices = terminal_text_to_uv(node.terminal_text)
    uvs = []
    add_uv = uvs.append
    _ = [[add_uv(uv) for uv in uvset] for uvset in uv_indices]
    return uvs


class LexMixin():

    texture_dict = {}
    console_grid_dict = {}

    name1Color: make_color("name1 color",      (0.83, 0.91, 1.00, 1.0))  # 1
    numberColor: make_color("number color",    (0.08, 0.70, 0.98, 1.0))  # 2
    stringColor: make_color("Strings",         (0.96, 0.85, 0.00, 1.0))  # 3
    parenColor: make_color("parenthesis"  ,    (0.70, 0.07, 0.01, 1.0))  # 7, 8
    bracketColor: make_color("Brackets color", (0.65, 0.68, 0.70, 1.0))  # 9, 10
    equalsColor: make_color("Equals",          (0.90, 0.70, 0.60, 1.0))  # 22
    braceColor: make_color("Braces",           (0.40, 0.50, 0.70, 1.0))  # 25, 26
    opColor: make_color("Operators",           (1.00, 0.18, 0.00, 1.0))  # 53, 54
    commentColor: make_color("Comments",       (0.49, 0.49, 0.49, 1.0))  # 55, 60
    name2Color: make_color("Main syntax",      (0.90, 0.01, 0.02, 1.0))  # 90
    name3Color: make_color("Bool etc,..",      (0.30, 0.90, 0.40, 1.0))  # 91
    qualifierColor: make_color("Qualifiers",   (0.18, 0.77, 0.01, 1.0))  # 92
    bgColor: make_color("Background",          (0.06, 0.06, 0.06, 1.0))  # there are nicer ways to calculate the background overlay.

    terminal_width: bpy.props.IntProperty(name="terminal width", default=10, min=2) #, update=updateNode)
    terminal_text: bpy.props.StringProperty(name="terminal text", default="1234567890\n0987654321\n098765BbaA")
    num_rows: bpy.props.IntProperty(name="num rows", default=3, min=1) #, update=updateNode)


    def init_texture(self, width, height):
        clr = bgl.GL_RGBA
        texname = self.texture_dict['texture']
        data = self.texture_dict['texture_data']

        texture = bgl.Buffer(bgl.GL_FLOAT, data.size, data.tolist())
        bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT, 1)
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, clr, width, height, 0, clr, bgl.GL_FLOAT, texture)

    def get_font_texture(self):
        if not self.texture_dict:
            filepath = get_font_pydata_location()
            # this is a compressed npz, which we can dict lookup.
            found_data = np.load(filepath)
            data = found_data['a']

            dsize = data.size
            data = data.repeat(3).reshape(-1, 3)
            data = np.concatenate((data, np.ones(dsize)[:,None]),axis=1).flatten()
            name = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, name)
            self.texture_dict['texture'] = name[0]
            self.texture_dict['texture_data'] = data # bgl.Buffer(bgl.GL_FLOAT, data.size, data.tolist())        

    def get_lexed_colors(self):
        return [(lex_name, getattr(self, lex_name)[:]) for lex_name in lexed_colors]

    def prepare_for_grid(self):
        char_width = int(15 * self.local_scale)
        char_height = int(32 * self.local_scale)

        params = tuple(char_width, char_height, self.terminal_width, self.num_rows)
        if params in console_grid_dict:
            coords, cfaces = console_grid_dict.get(params)
        else:
            coords, cfaces = get_console_grid(char_width, char_height, self.terminal_width, self.num_rows)
            console_grid_dict[params] = coords, cfaces

        return coords, cfaces

    @property
    def dims(self):
        x, y = self.xy_offset
        width = self.terminal_width * 15
        height = self.num_rows * 32
        return (x, y, width, height)

    def set_node_props(self, socket_data):
        multiline, (chars_x, chars_y) = advanced_text_decompose('\n'.join(socket_data))
        valid_multiline = '\n'.join(multiline)
        self.terminal_text = valid_multiline
        self.num_rows = chars_y
        self.terminal_width = chars_x


class SvStethoscopeNodeMK2(bpy.types.Node, SverchCustomTreeNode, LexMixin, SvNodeViewDrawMixin):
    """
        Triggers: scope 
        Tooltip: Display data output of a node in nodeview
        
        this node uses nodeview bgl callbacks to display text/numbers/structures
        generated by other nodes.
        """
        
    bl_idname = 'SvStethoscopeNodeMK2'
    bl_label = 'Stethoscope MK2'
    bl_icon = 'LONGDISPLAY'

    font_id: IntProperty(default=0, update=updateNode)

    text_color: FloatVectorProperty(
        name="Color", description='Text color',
        size=3, min=0.0, max=1.0,
        default=(.1, .1, .1), subtype='COLOR',
        update=updateNode)

    activate: BoolProperty(
        name='Show', description='Activate node?',
        default=True,
        update=updateNode)

    mode_options = [(i, i, '', idx) for idx, i in enumerate(["text-based", "graphical", "sv++"])]
    selected_mode: bpy.props.EnumProperty(
        items=mode_options,
        description="offers....",
        default="text-based", update=updateNode
    )

    view_by_element: BoolProperty(update=updateNode)
    num_elements: IntProperty(default=0)
    element_index: IntProperty(default=0, update=updateNode)
    rounding: IntProperty(min=0, max=5, default=3, update=updateNode)
    line_width: IntProperty(default=60, min=20, update=updateNode, name='Line Width (chars)')
    compact: BoolProperty(default=False, update=updateNode)
    depth: IntProperty(default=5, min=0, update=updateNode)

    local_scale: bpy.props.FloatProperty(default=1.0, min=0.2, name="scale", update=updateNode)


    def get_theme_colors_for_contrast(self):
        try:
            current_theme = bpy.context.preferences.themes.items()[0][0]
            editor = bpy.context.preferences.themes[current_theme].node_editor
            self.text_color = high_contrast_color(editor.space.back)
        except:
            print('-', end='')

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Data')
        self.get_theme_colors_for_contrast()
        if hasattr(self.id_data, 'update_gl_scale_info'):  # node groups does not have the method
            self.id_data.update_gl_scale_info()

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def draw_buttons(self, context, layout):
        row = layout.row()
        icon = 'RESTRICT_VIEW_OFF' if self.activate else 'RESTRICT_VIEW_ON'
        row.prop(self, "activate", icon=icon, text='')

        layout.prop(self, 'selected_mode', expand=True)
        if self.selected_mode == 'text-based':

            row.prop(self, "text_color", text='')
            row1 = layout.row(align=True)
            row1.prop(self, "rounding")
            row1.prop(self, "compact", toggle=True)
            row2 = layout.row(align=True)
            row2.prop(self, "line_width")
            row2.prop(self, "depth")
            # layout.prop(self, "socket_name")
            layout.label(text='input has {0} elements'.format(self.num_elements))
            layout.prop(self, 'view_by_element', toggle=True)
            if self.num_elements > 0 and self.view_by_element:
                layout.prop(self, 'element_index', text='get index')

        elif self.selected_mode == "sv++":
            row1 = layout.row(align=True)
            row1.prop(self, "line_width")
            row1.prop(self, "rounding")
            layout.prop(self, 'element_index', text='get index')
            layout.prop(self, "local_scale")
        else:
            pass

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'font_id')

    def get_preferences(self):
        return get_params({
            'stethoscope_view_scale': 1.0, 'render_location_xy_multiplier': 1.0}, direct=True)

    def process(self):
        inputs = self.inputs
        n_id = node_id(self)

        # end early
        nvBGL.callback_disable(n_id)

        if self.activate and inputs[0].is_linked:
            scale, self.location_theta = self.get_preferences()

            # gather vertices from input
            data = inputs[0].sv_get(deepcopy=False)
            self.num_elements = len(data)

            if self.selected_mode == 'text-based':
                props = lambda: None
                props.line_width = self.line_width
                props.compact = self.compact
                props.depth = self.depth or None

                processed_data = parse_socket(
                    inputs[0],
                    self.rounding,
                    self.element_index,
                    self.view_by_element,
                    props
                )

            elif self.selected_mode == "sv++":

                texture = lambda: None
                config = lambda: None

                processed_data = advanced_parse_socket(inputs[0], self)
                self.set_node_props(processed_data)

                # lexer = random_color_chars(self) # <-- this can be used for a much lighter lexer.
                lexer = syntax_highlight_basic(self).repeat(6).tolist()
                self.get_font_texture()  # this is cached after 1st run
                self.init_texture(256, 256)  # this must be done each redraw
                grid = self.prepare_for_grid()  # could be cached, certainly if width/numrows dont change   

                self.adjust_position_and_dimensions(*self.dims)  # low impact i think..
                verts = process_grid_for_shader(grid)  # [ ] ? cacheable?
                uv_indices = process_uvs_for_shader(self)  # could cache if terminal text is unchanged.

                texture.texture_dict = self.texture_dict
                shader = gpu.types.GPUShader(vertex_shader, lexed_fragment_shader)
                batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
                config.batch = batch
                config.shader = shader
                config.syntax_mode = "Code"
                config.colors = {color_name: getattr(self, color_name)[:] for color_name in lexed_colors}

                draw_data = {
                  'tree_name': self.id_data.name[:],
                  'node_name': self.name[:],
                  'loc': get_xy_for_bgl_drawing,
                  'mode': 'custom_function_context', 
                  'custom_function': simple_console_xy,
                  'args': (texture, config)
                }
                nvBGL.callback_enable(n_id, draw_data)
                return

            else:
                # display the __repr__ version of the incoming data
                processed_data = data


            draw_data = {
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'content': processed_data,
                'location': get_xy_for_bgl_drawing,
                'color': self.text_color[:],
                'scale' : float(scale),
                'mode': self.selected_mode[:],
                'font_id': int(self.font_id)
            }
            nvBGL.callback_enable(n_id, draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

    def sv_update(self):
        if not ("Data" in self.inputs):
            return
        try:
            if not self.inputs[0].other:
                nvBGL.callback_disable(node_id(self))        
        except:
            print('stethoscope update holdout (not a problem)')


def register():
    bpy.utils.register_class(SvStethoscopeNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvStethoscopeNodeMK2)
