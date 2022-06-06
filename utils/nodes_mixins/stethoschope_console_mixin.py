# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import numpy as np
import blf, bgl, gpu
from mathutils import Vector
from gpu_extras.batch import batch_for_shader

import sverchok

from sverchok.utils.sv_nodeview_draw_helper import get_console_grid
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

def adjust_location(_x, _y, location_theta):
    return _x * location_theta, _y * location_theta

# yep, this is a repeat function.
def get_xy_for_bgl_drawing(node):
    # adjust proposed text location in case node is framed.
    # take into consideration the hidden state
    node_width = node.width
    _x, _y = node.absolute_location
    _x, _y = Vector((_x, _y)) + Vector((node_width + 20, 0))

    # this alters location based on DPI/Scale settings.
    draw_location = adjust_location(_x, _y, node.location_theta)
    return draw_location

def advanced_parse_socket(socket, node):

    out = "...."
    if (fulldata := socket.sv_get()):
        if len(fulldata) > 0:
            try:

                # could potentially chop up fulldata here before turning it
                # into nparray. maybe it's faster?
                index = abs(node.element_index) % len(fulldata)
                prefix = f"data[{index}] = "
                a = np.array(fulldata[index])
                str_array = np.array2string(
                    a, 
                    max_line_width=node.line_width, 
                    precision=node.rounding or None, 
                    prefix=prefix, 
                    separator=' ', 
                    threshold=30,
                    edgeitems=10)
                
                if "list" in str_array:
                    str_array = re.sub("list\((?P<list>.+?)\)", "\g<list>", str_array)
                #print(str_array)
                return (prefix + str_array).split("\n")
            except:
                ...
    return out



def find_longest_linelength(lines):
    return len(max(lines, key=len))


def ensure_line_padding(text, filler=" "):
    """ expects a single string, with newlines """
    lines = text.split('\n')
    longest_line = find_longest_linelength(lines)
    
    new_lines = []
    new_line = new_lines.append
    for line in lines:
        new_line(line.ljust(longest_line, filler))
    
    return new_lines, longest_line

def advanced_text_decompose(content):
    """
    input:
        expects to receive a newline separated string, to indicate multiline text
        if anything else is received a "no valid text found..." message is passed.
    return:
        return_str : a list of strings, padded with " " to match the longest line
        dims       : 1. number of lines high, 
                     2. length of longest line (its char count)
    """
    return_str = ""
    if isinstance(content, str):
        return_str, width = ensure_line_padding(content)
    else:
        return_str, width = ensure_line_padding("no valid text found\nfeed it multiline\ntext")

    dims = width, len(return_str)
    return return_str, dims


class LexMixin():

    texture_dict = {}
    console_grid_dict = {}   # shared over all insntances.

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

        params = char_width, char_height, self.terminal_width, self.num_rows
        if params in self.console_grid_dict:
            geom = self.console_grid_dict.get(params)
        else:
            geom = get_console_grid(char_width, char_height, self.terminal_width, self.num_rows)
            self.console_grid_dict[params] = geom

        return geom

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

    @property
    def draw_data(self):          
        texture = lambda: None
        config = lambda: None

        processed_data = advanced_parse_socket(self.inputs[0], self)
        self.set_node_props(processed_data)
        self.adjust_position_and_dimensions(*self.dims)  # low impact i think..

        lexer = syntax_highlight_basic(self).repeat(6).tolist()
        self.get_font_texture()  # [x] this is cached after 1st run
        self.init_texture(256, 256)  # this must be done each redraw
        grid = self.prepare_for_grid()  # [x] is cached   

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
        return draw_data