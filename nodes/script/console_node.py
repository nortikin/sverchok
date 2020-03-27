# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import os
import inspect
import numpy as np

import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.settings import get_params
from sverchok.data_structure import updateNode, node_id

from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.sv_font_xml_parser import get_lookup_dict, letters_to_uv
from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, get_console_grid

def make_color(name, default):
    return bpy.props.FloatVectorProperty(name=name, default=default, size=4, min=0, max=1, update=updateNode, subtype="COLOR")

# this data need only be generated once, or at runtime at request (low frequency).
sv_path = os.path.dirname(sv_get_local_path()[0])
bitmap_font_location = os.path.join(sv_path, 'utils', 'modules', 'bitmap_font')

lookup_dict_data = {}

vertex_shader = '''
    uniform mat4 ModelViewProjectionMatrix;

    in vec2 texCoord;
    in vec2 pos;
    in float lexer;

    out float v_lexer;
    out vec2 texCoord_interp;

    void main()
    {
       v_lexer = lexer;
       gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 0.0f, 1.0f);
       gl_Position.z = 1.0;
       texCoord_interp = texCoord;
    }
'''

fragment_shader = '''
    in float v_lexer;
    in vec2 texCoord_interp;

    out vec4 fragColor;
    
    uniform sampler2D image;
    
    void main()
    {
        vec4 test_tint = vec4(0.2, 0.7, 1.0, 1.0);
        int cIndex = int(v_lexer);
        if (cIndex == 3) { test_tint = vec4(0.148, 0.447, 0.040, 1.0); }
        if (cIndex == 2) { test_tint = vec4(0.9, 0.9, 1.0, 1.0); }
        if (cIndex == 1) { test_tint = vec4(0.4, 0.9, 0.8, 1.0); }
        if (cIndex == 53) { test_tint = vec4(1.0, 0.3, 0.7, 1.0); }
        if (cIndex == 90) { test_tint = vec4(0.7, 0.9, 0.3, 1.0); }
        if (cIndex == 91) { test_tint = vec4(0.3, 0.9, 0.4, 1.0); }
        fragColor = texture(image, texCoord_interp) * test_tint;
    }
'''

lexed_colors = [
    'stringColor', 'numberColor', 'name1Color',
    'parenColor', 'braceColor', 'bracketColor', 'equalsColor',
    'opColor', 'commentColor', 'name2Color', 'name3Color'
]

lexed_fragment_shader = '''
    in float v_lexer;
    in vec2 texCoord_interp;

    out vec4 fragColor;
    
    uniform sampler2D image;
    uniform vec4 stringColor;
    uniform vec4 numberColor;
    uniform vec4 name1Color;
    uniform vec4 parenColor;
    uniform vec4 braceColor;
    uniform vec4 bracketColor;
    uniform vec4 opColor;
    uniform vec4 equalsColor;
    uniform vec4 commentColor;
    uniform vec4 name2Color;
    uniform vec4 name3Color;
    
    void main()
    {
        vec4 test_tint = vec4(0.2, 0.7, 1.0, 1.0);
        int cIndex = int(v_lexer);
        if (cIndex == 3) { test_tint = stringColor; }
        if (cIndex == 2) { test_tint = numberColor; }
        if (cIndex == 1) { test_tint = name1Color; }
        if (cIndex == 22) { test_tint = equalsColor; }
        if (cIndex == 7 || cIndex == 8) { test_tint = parenColor; }
        if (cIndex == 25 || cIndex == 26) { test_tint = braceColor; }
        if (cIndex == 9 || cIndex == 10) { test_tint = bracketColor; }
        if (cIndex == 53) { test_tint = opColor; }
        if (cIndex == 55) { test_tint = commentColor; }
        if (cIndex == 90) { test_tint = name2Color; }
        if (cIndex == 91) { test_tint = name3Color; }
        fragColor = texture(image, texCoord_interp) * test_tint;
    }
'''


def get_font_pydata_location():
    return os.path.join(bitmap_font_location, 'consolas_0.npz')

def get_font_fnt_location():
    return os.path.join(bitmap_font_location, 'consolas.fnt')

def random_color_chars(node):
    """
    returns all values [0,1,2,3,...] as floats.
    the reason i'm using floats is because i didn't figure out a better way to a single
    integer per tri-angle, so i am passing a float per vertex, because an int per vertex can not
    be interpolated for all pixels in the fragment.
    """
    array_size = node.terminal_width * node.num_rows
    ints = np.random.randint(0, 4, size=array_size)
    floats = np.array(ints, dtype='int').repeat(6).tolist()
    return floats

def syntax_highlight_basic(node):
    """
    this uses the built in lexer/tokenizer in python to identify part of code
    will return a meaningful lookuptable for index colours per character
    """
    import tokenize
    import io
    import token

    text = node.terminal_text
    # print(token.tok_name) #   <--- dict of token-kinds.

    array_size = node.terminal_width * node.num_rows
    ones = np.ones(array_size)

    with io.StringIO(text) as f:

        tokens = tokenize.generate_tokens(f.readline)

        for token in tokens:
            if token.type in (0, 4, 56, 256):
                continue
            if not token.string or (token.start == token.end):
                continue

            token_type = token.type
            
            if token.type == 1:
                if token.string in {
                        'print', 'def', 'class', 'break', 'continue', 'return', 'while', 'or', 'and',
                        'dir', 'if', 'in', 'as', 'out', 'with', 'from', 'import', 'with', 'for'}:
                    token_type = 90
                elif token.string in {'False', 'True', 'yield', 'repr', 'range', 'enumerate'}:
                    token_type = 91

            elif token.type == 53:
                # OPS
                # 7: 'LPAR', 8: 'RPAR
                # 9: 'LSQB', 10: 'RSQB'
                # 25: 'LBRACE', 26: 'RBRACE'
                if token.exact_type in {7, 8, 9, 10, 25, 26}:
                    token_type = token.exact_type

                elif token.exact_type == 22:
                    token_type = token.exact_type

            # print(token)
            #  start = (line number, 1 indexed) , (char index, 0 indexed)
            # print('|start:', token.start, '|end:', token.end, "[", token.exact_type, token.type, "]")
            current_type = float(token_type)
            row_start, char_start = token.start[0]-1, token.start[1]
            row_end, char_end = token.end[0]-1, token.end[1]
            index1 = (row_start * node.terminal_width) + char_start
            index2 = (row_end * node.terminal_width) + char_end

            np.put(ones, np.arange(index1, index2), [current_type])
            

    final_ones = ones.reshape((-1, node.terminal_width))
    return final_ones

def filter_incoming(socket_data):
    """
    a preprocessing step, inefficient, to replace all long string tokens with an abbreviated line + [...]
    """

    import tokenize
    import io
    import token
    import textwrap

    text = socket_data[0]
    line_indices_done = set()

    replacements = {}
    with io.StringIO(text) as f:
        tokens = tokenize.generate_tokens(f.readline)

        for token in tokens:
            if not token.type == 3:
                continue
            if not token.start[0] == token.end[0]:
                # this is a multiline nicely formatted textstring.. should be OK.
                continue
            if not ((token.end[1] - token.start[1]) > 80):
                continue

            # if reaches here, then we have a single line, very long string
            # print(token.string)
            suggested_line = textwrap.shorten(token.string, width=80) + "\""
            replacements[(token.start, token.end)] = suggested_line
            # print(suggested_line)

    socket_data = socket_data[0].splitlines()
    for ridx, proposal in replacements.items():

        # because i am not storing multiline strings, this will be enough
        (linenum, char_start), (_, char_end) = ridx
        linenum -= 1
        if linenum in line_indices_done:
            continue
        
        # if reaching here.. means we are going to replace a string. hold tight!
        found_line = socket_data[linenum]
        new_line = found_line[:char_start] + proposal + found_line[char_end:]
        socket_data[linenum] = new_line
        line_indices_done.add(linenum)

    return ["\n".join(socket_data)]

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
        
def get_last_n_lines(content, last_n_lines):
    content = content.strip()
    try:
        return '\n'.join(content.rsplit("\n", last_n_lines)[1:])
        
    except Exception as err:
        print(err)
        
    return "\n".join(content.split('\n')[-last_n_lines:])


def text_decompose(content, last_n_lines):
    """
    input: 
        expects to receive a newline separated string, to indicate multiline text
        if anything else is received a "no valid text found..." message is passed.
    return:
        return_str : a a list of strings, padded with " " to match the longest line
        dims       : 1. number of lines high, 
                     2. length of longest line (its char count)
    """
    return_str = ""
    if isinstance(content, str):
        if last_n_lines > 0:
            content = get_last_n_lines(content, last_n_lines)

        return_str, width = ensure_line_padding(content)
    else:
        return_str, width = ensure_line_padding("no valid text found\nfeed it multiline\ntext")

    dims = width, len(return_str)
    return return_str, dims

def get_fnt_lookup():
    # this caches the fnt lookup function, and reuses it in any subsequent call to process.
    # this is the same lookup table for all instances of this node. This is conscious limitation. for now.
    if not lookup_dict_data.get('fnt'):
        lookup_dict_data['fnt'] = get_lookup_dict(get_font_fnt_location())
    return lookup_dict_data['fnt']

def terminal_text_to_uv(lines):
    fnt = get_fnt_lookup()
    uvs = []
    for line in lines.split("\n"):
        uvs.extend(letters_to_uv(line, fnt))
    return uvs

def simple_console_xy(context, args):
    texture, config = args
    act_tex = bgl.Buffer(bgl.GL_INT, 1)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture.texture_dict['texture'])
    
    config.shader.bind()
    
    if not config.syntax_mode == "None":
        matrix = gpu.matrix.get_projection_matrix()
        config.shader.uniform_float("ModelViewProjectionMatrix", matrix)
    
    if config.syntax_mode == "Code":
        for color_name, color_value in config.colors.items():
            config.shader.uniform_float(color_name, color_value)

    config.shader.uniform_int("image", act_tex)
    config.batch.draw(config.shader)

def process_grid_for_shader(grid, loc):
    x, y = loc
    positions, poly_indices = grid
    translated_positions = [(p[0] + x, p[1] + y) for p in positions]
    verts = []
    for poly in poly_indices:
        for v_idx in poly:
            verts.append(translated_positions[v_idx])
    return verts

def process_uvs_for_shader(node):
    uv_indices = terminal_text_to_uv(node.terminal_text)
    uvs = []
    add_uv = uvs.append
    _ = [[add_uv(uv) for uv in uvset] for uvset in uv_indices]
    return uvs


def generate_batch_shader(node, data):
    verts, uv_indices, lexer = data
    # print("len(verts)", len(verts), "len(uv_indices)", len(uv_indices))

    if node.syntax_mode == "None":
        shader = gpu.shader.from_builtin('2D_IMAGE')
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices})
    elif node.syntax_mode == "Code":
        shader = gpu.types.GPUShader(vertex_shader, lexed_fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
    elif node.syntax_mode == "f1":
        shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
    
    return batch, shader

class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode, SvNodeViewDrawMixin):
    
    """
    Triggers: Console 
    Tooltip:  Console for Sverchok node

    This node prints the input to the nodeview using a fixedwidth character map.

    at the moment this node expects to find a 256*256 png ( actually, npy ..a numpy array saved to disk in a binary form)


    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'CONSOLE'

    @throttled
    def local_updateNode(self, context):
        # self.process()
        ...

    snlite_mode: bpy.props.BoolProperty(name="Snlite mode", description="read script str from snlite node", update=updateNode)
    num_rows: bpy.props.IntProperty(name="num rows", default=3, min=1) #, update=updateNode)
    terminal_width: bpy.props.IntProperty(name="terminal width", default=10, min=2) #, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    terminal_text: bpy.props.StringProperty(name="terminal text", default="1234567890\n0987654321\n098765BbaA")
    
    # for now all such nodes will use the same texture.
    texture_dict = {}

    n_id: bpy.props.StringProperty(default='')
    local_scale: bpy.props.FloatProperty(default=1.0, min=0.2, name="scale", update=updateNode)
    show_me: bpy.props.BoolProperty(default=True, name="show me", update=updateNode)

    syntax_mode: bpy.props.EnumProperty(
        items=[(k, k, '', i) for i, k in enumerate(["Code", "f1", "None"])],
        description="Code (useful code highlighting\nf1 (useful general text highlighting", default="None", update=updateNode
    )

    last_n_lines: bpy.props.IntProperty(min=0, name="last n lines", description="show n number of last lines", update=updateNode)
    filter_long_strings: bpy.props.BoolProperty(default=True, name="Filter", description="Filter long strings", update=updateNode)

    stringColor: make_color("string color", (0.148, 0.447, 0.040, 1.0))  # 3
    numberColor: make_color("number color", (0.9, 0.9, 1.0, 1.0))  # 2
    name1Color: make_color("name1 color", (0.4, 0.9, 0.8, 1.0))  # 1
    parenColor: make_color("parenthesis color", (0.4, 0.3, 0.7, 1.0))  # 53     7/8
    bracketColor: make_color("brackets color", (0.5, 0.7, 0.7, 1.0))  # 53      9/10
    braceColor: make_color("braces color", (0.4, 0.5, 0.7, 1.0))  # 53         25/26
    opColor: make_color("op color", (1.0, 0.3, 0.7, 1.0))  # 53
    name2Color: make_color("name2 color", (0.7, 0.9, 0.3, 1.0))  # 90
    name3Color: make_color("name3 color", (0.3, 0.9, 0.4, 1.0))  # 91
    commentColor: make_color("comment color", (0.2, 0.2, 0.2, 1.0))
    equalsColor: make_color("equals color", (0.9, 0.7, 0.6, 1.0))

    def get_lexed_colors(self):
        return [(lex_name, getattr(self, lex_name)[:]) for lex_name in lexed_colors]

    def prepare_for_grid(self):
        char_width = int(15 * self.local_scale)
        char_height = int(32 * self.local_scale)
        return get_console_grid(char_width, char_height, self.terminal_width, self.num_rows)

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
           
        # return self.texture_dict.get('texture')

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "text")
        self.get_and_set_gl_scale_info()
        
    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "show_me", text="", icon="HIDE_OFF")
        row.prop(self, "snlite_mode", text="", icon="CONSOLE")
        row.separator()
        row.prop(self, "local_scale")
        if not self.snlite_mode:
            row.separator()
            row.prop(self, "filter_long_strings", text="", icon="FILTER")
        row2 = layout.row(align=True)
        row2.prop(self, "syntax_mode", expand=True)
        row3 = layout.row()
        row3.prop(self, "last_n_lines")

    def draw_buttons_ext(self, context, layout):
        col = layout.column()
        for color_name in lexed_colors:
            row = col.row()
            row.prop(self, color_name)

    
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

    def set_node_props(self, socket_data):
        multiline, (chars_x, chars_y) = text_decompose('\n'.join(socket_data), self.last_n_lines)
        valid_multiline = '\n'.join(multiline)
        self.terminal_text = valid_multiline
        self.num_rows = chars_y
        self.terminal_width = chars_x

    def terminal_text_to_config(self, update=False):

        with self.sv_throttle_tree_update():

            if not self.snlite_mode:
                socket_data = self.inputs[0].sv_get()

                # this will find the newline delimited text from Object ID selector.
                if len(socket_data) == 1:
                    socket_data = socket_data[0]
                    if isinstance(socket_data, list) and len(socket_data) and isinstance(socket_data[0], str):

                        if self.filter_long_strings:
                            socket_data = filter_incoming(socket_data)
                        self.set_node_props(socket_data)

            else:
                # if the origin node for this socket is a snlite node, we read the node.script_str instead of the data
                if self.inputs[0].other.node.bl_idname == "SvScriptNodeLite":
                    socket_data = list(self.inputs[0].other.node.script_str.splitlines())
                    self.set_node_props(socket_data)

        if update:
            updateNode(self, None)


    def process(self):
        n_id = node_id(self)
        nvBGL2.callback_disable(n_id)

        if self.end_early():
            return

        self.terminal_text_to_config()
        self.get_font_texture()
        self.init_texture(256, 256)

        config = lambda: None
        texture = lambda: None
        texture.texture_dict = self.texture_dict

        lexer = self.get_lexer()
        grid = self.prepare_for_grid()

        x, y, width, height = self.adjust_position_and_dimensions(*self.dims)
        verts = process_grid_for_shader(grid, loc=(x, y))
        uvs = process_uvs_for_shader(self)

        batch, shader = generate_batch_shader(self, (verts, uvs, lexer))
        config.loc = (x, y)
        config.batch = batch
        config.shader = shader
        config.syntax_mode = self.syntax_mode

        if self.syntax_mode == "Code":
            config.colors = {}
            for color_name in lexed_colors:
                config.colors[color_name] = getattr(self, color_name)[:]

        draw_data = {
            'tree_name': self.id_data.name[:],
            'mode': 'custom_function_context', 
            'custom_function': simple_console_xy,
            'args': (texture, config)
        }
        nvBGL2.callback_enable(n_id, draw_data)

    @property
    def dims(self):
        x, y = self.xy_offset
        width = self.terminal_width * 15
        height = self.num_rows * 32
        return (x, y, width, height)

    def free(self):
        nvBGL2.callback_disable(node_id(self))
        # self.delete_texture()

    def sv_copy(self, node):
        self.n_id = ''

    def get_lexer(self):
        if self.syntax_mode == "Code":
            lexer = syntax_highlight_basic(self).repeat(6).tolist()
        elif self.syntax_mode == "f1":
            lexer = random_color_chars(self)
        else:
            lexer = None
        return lexer

    def end_early(self):
        if not self.show_me:
            return True

        if not self.inputs[0].is_linked or not self.inputs[0].sv_get():
            return True

    def update(self):
        if not ("text" in self.inputs):
            return
        try:
            if not self.inputs[0].other:
                self.free()
        except:
            # print('ConsoleNode was disconnected, holdout (not a problem)')
            pass

classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
