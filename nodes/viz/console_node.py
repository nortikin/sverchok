# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import os
import numpy as np
import itertools

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, node_id

from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.utils.sv_update_utils import sv_get_local_path
from sverchok.utils.sv_font_xml_parser import get_lookup_dict, letters_to_uv
from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, get_console_grid
#from sverchok.utils.decorators_compilation import njit

def get_desired_xy(node):
    x, y = node.xy_offset
    return x * node.location_theta, y * node.location_theta

def make_color(name, default):
    return bpy.props.FloatVectorProperty(name=name, default=default, size=4, min=0, max=1, update=updateNode, subtype="COLOR")

# this data need only be generated once, or at runtime at request (low frequency).
sv_path = os.path.dirname(sv_get_local_path()[0])
bitmap_font_location = os.path.join(sv_path, 'utils', 'modules', 'bitmap_font')

lookup_dict_data = {}

no_vertex_shader = '''
    uniform mat4 viewProjectionMatrix;

    in vec2 texCoord;
    in vec2 pos;
    uniform float x_offset;
    uniform float y_offset;    

    out vec2 texCoord_interp;

    void main()
    {
       gl_Position = viewProjectionMatrix * vec4(pos.x + x_offset, pos.y + y_offset, 0.0f, 1.0f);
       gl_Position.z = 1.0;
       texCoord_interp = texCoord;
    }
'''
no_fragment_shader = '''
    in vec2 texCoord_interp;

    out vec4 fragColor;
    
    uniform sampler2D image;
    
    void main()
    {
        fragColor = texture(image, texCoord_interp);
    }
'''

vertex_shader = '''
    uniform mat4 viewProjectionMatrix;

    in vec2 texCoord;
    in vec2 pos;
    in float lexer;
    uniform float x_offset;
    uniform float y_offset;    

    out float v_lexer;
    out vec2 texCoord_interp;

    void main()
    {
       v_lexer = lexer;
       gl_Position = viewProjectionMatrix * vec4(pos.x + x_offset, pos.y + y_offset, 0.0f, 1.0f);
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
    'opColor', 'commentColor', 'name2Color', 'name3Color', 'qualifierColor', 'bgColor'
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
    uniform vec4 qualifierColor;
    uniform vec4 bgColor;
    
    void main()
    {
        vec4 test_tint = vec4(0.0, 0.0, 1.0, 1.0);
        vec4 background_black = vec4(0.0, 0.0, 0.0, 1.0);

        int cIndex = int(v_lexer);

        if (cIndex == 1) { test_tint = name1Color; }
        else if (cIndex == 2) { test_tint = numberColor; }
        else if (cIndex == 3) { test_tint = stringColor; }
        else if (cIndex == 7 || cIndex == 8) { test_tint = parenColor; }
        else if (cIndex == 9 || cIndex == 10) { test_tint = bracketColor; }
        else if (cIndex == 22) { test_tint = equalsColor; }
        else if (cIndex == 25 || cIndex == 26) { test_tint = braceColor; }
        else if (cIndex == 53 || cIndex == 54) { test_tint = opColor; }
        else if (cIndex == 55 || cIndex == 61 || cIndex == 58) { test_tint = commentColor; }
        else if (cIndex == 90) { test_tint = name2Color; }
        else if (cIndex == 91) { test_tint = name3Color; }
        else if (cIndex == 92) { test_tint = qualifierColor; }

        vec4 pixelColor = texture(image, texCoord_interp);

        if (length(pixelColor.xyz) < 0.0001){
            fragColor = mix(bgColor, texture(image, texCoord_interp) * test_tint, 0.5);
        }
        else{
            fragColor = texture(image, texCoord_interp) * test_tint;
        }

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
    token_dict = tokenize.tok_name
    """
    in py3.7 this is different than py3.9+ 

    print(tokenize.tok_name) #   <--- dict of token-kinds.

    {0: 'ENDMARKER', 1: 'NAME', 2: 'NUMBER', 3: 'STRING', 4: 'NEWLINE', 5: 'INDENT', 
    6: 'DEDENT', 7: 'LPAR', 8: 'RPAR', 9: 'LSQB', 10: 'RSQB', 11: 'COLON', 
    12: 'COMMA', 13: 'SEMI', 14: 'PLUS', 15: 'MINUS', 16: 'STAR', 17: 'SLASH', 
    18: 'VBAR', 19: 'AMPER', 20: 'LESS', 21: 'GREATER', 22: 'EQUAL', 23: 'DOT', 
    24: 'PERCENT', 25: 'LBRACE', 26: 'RBRACE', 27: 'EQEQUAL', 28: 'NOTEQUAL', 
    29: 'LESSEQUAL', 30: 'GREATEREQUAL', 31: 'TILDE', 32: 'CIRCUMFLEX', 
    33: 'LEFTSHIFT', 34: 'RIGHTSHIFT', 35: 'DOUBLESTAR', 36: 'PLUSEQUAL', 
    37: 'MINEQUAL', 38: 'STAREQUAL', 39: 'SLASHEQUAL', 40: 'PERCENTEQUAL', 
    41: 'AMPEREQUAL', 42: 'VBAREQUAL', 43: 'CIRCUMFLEXEQUAL', 44: 'LEFTSHIFTEQUAL', 
    45: 'RIGHTSHIFTEQUAL', 46: 'DOUBLESTAREQUAL', 47: 'DOUBLESLASH', 48: 'DOUBLESLASHEQUAL', 
    49: 'AT', 50: 'ATEQUAL', 51: 'RARROW', 52: 'ELLIPSIS', 53: 'COLONEQUAL', 
    54: 'OP', 55: 'AWAIT', 56: 'ASYNC', 57: 'TYPE_IGNORE', 58: 'TYPE_COMMENT', 
    59: 'ERRORTOKEN', 60: 'COMMENT', 61: 'NL', 62: 'ENCODING', 63: 'N_TOKENS', 256: 'NT_OFFSET'
    }
    """

    array_size = node.terminal_width * node.num_rows
    ones = np.ones(array_size)

    with io.StringIO(text) as f:

        tokens = tokenize.generate_tokens(f.readline)
        for token in tokens:

            if token.type in (0, 4, 56, 256):
                continue
            if not token.string or (token.start == token.end):
                continue

            # if token.type != 1:
            #    print(f"token.type, {token.type} , precise token={token.exact_type} ({token_dict.get(token.exact_type)}) ---> {token.string}")

            token_type = token.type
            
            if token.type == 1:
                if token.string in {
                        'print', 'break', 'continue', 'return', 'while', 'or', 'and', 'dir',
                        'if', 'else', 'in', 'as', 'out', 'with', 'from', 'import', 'with', 'for',
                        'try', 'except', 'finally'}:
                    token_type = 90
                elif token.string in {'def', 'class', 'lambda'}:
                    token_type = 92
                elif token.string in {'False', 'True', 'yield', 'repr', 'range', 'enumerate'}:
                    token_type = 91

            elif token.type == 54:
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
            

    # print(ones.tolist())
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
        return_str : a list of strings, padded with " " to match the longest line
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

def simple_console_xy(context, args, loc):
    texture, config = args
    act_tex = drawing.new_buffer_texture()
    drawing.bind_texture_2d(texture.texture_dict['texture'])
    config.shader.bind()
    
    # if not config.syntax_mode == "None":
    matrix = gpu.matrix.get_projection_matrix()
    config.shader.uniform_float("viewProjectionMatrix", matrix)
    
    if config.syntax_mode == "Code":
        for color_name, color_value in config.colors.items():
            config.shader.uniform_float(color_name, color_value)

    x, y = loc

    config.shader.uniform_float("x_offset", x)
    config.shader.uniform_float("y_offset", y)
    config.shader.uniform_int("image", act_tex)
    config.batch.draw(config.shader)

#@njit(cache=True)
def process_grid_for_shader(grid):
    positions, poly_indices = grid
    verts = []
    for poly in poly_indices:
        for v_idx in poly:
            verts.append(positions[v_idx])
    return verts

def process_uvs_for_shader(node):
    uv_indices = terminal_text_to_uv(node.terminal_text)
    return list(itertools.chain.from_iterable(uv_indices))


def generate_batch_shader(node, data):
    verts, uv_indices, lexer = data
    # print("len(verts)", len(verts), "len(uv_indices)", len(uv_indices))

    if node.syntax_mode == "None":
        shader = gpu.types.GPUShader(no_vertex_shader, no_fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices})
    elif node.syntax_mode == "Code":
        shader = gpu.types.GPUShader(vertex_shader, lexed_fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
    elif node.syntax_mode == "f1":
        shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
        batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
    
    return batch, shader

class SvConsoleNode(SverchCustomTreeNode, bpy.types.Node, SvNodeViewDrawMixin):
    
    """
    Triggers: Console 
    Tooltip:  Console for Sverchok node. This is a developer’s node

    This node prints the input to the nodeview using a fixedwidth character map.

    at the moment this node expects to find a 256*256 png ( actually, npy ..a numpy array saved to disk in a binary form)


    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'CONSOLE'

    def local_updateNode(self, context):
        # self.process()
        updateNode(self, context)

    snlite_mode: bpy.props.BoolProperty(name="Snlite mode", description="read script str from snlite node", update=updateNode)
    num_rows: bpy.props.IntProperty(name="num rows", default=3, min=1) #, update=updateNode)
    terminal_width: bpy.props.IntProperty(name="terminal width", default=10, min=2) #, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    terminal_text: bpy.props.StringProperty(name="terminal text", default="1234567890\n0987654321\n098765BbaA")
    
    # for now all such nodes will use the same texture.
    texture_dict = {}

    local_scale: bpy.props.FloatProperty(default=1.0, min=0.2, name="scale", update=updateNode)
    show_me: bpy.props.BoolProperty(default=True, name="show me", update=updateNode)

    syntax_mode: bpy.props.EnumProperty(
        items=[(k, k, '', i) for i, k in enumerate(["Code", "f1", "None"])],
        description="Code (useful code highlighting\nf1 (useful general text highlighting", default="None", update=updateNode
    )

    last_n_lines: bpy.props.IntProperty(min=0, name="last n lines", description="show n number of last lines", update=updateNode)
    filter_long_strings: bpy.props.BoolProperty(default=True, name="Filter", description="Filter long strings", update=updateNode)

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
        self.id_data.update_gl_scale_info()
        
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
        texname = self.texture_dict['texture']
        data = self.texture_dict['texture_data']
        initialize_complex_texture(width, height, texname, texture, data, 'RGBA')


    def set_node_props(self, socket_data):
        multiline, (chars_x, chars_y) = text_decompose('\n'.join(socket_data), self.last_n_lines)
        valid_multiline = '\n'.join(multiline)
        self.terminal_text = valid_multiline
        self.num_rows = chars_y
        self.terminal_width = chars_x

    def terminal_text_to_config(self, update=False):

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
            connected_bl_idname = self.inputs[0].other.node.bl_idname
            if connected_bl_idname == "SvScriptNodeLite":
                socket_data = list(self.inputs[0].other.node.script_str.splitlines())

                self.set_node_props(socket_data)

            elif connected_bl_idname == "SvExecNodeMod":
                node = self.inputs[0].other.node
                socket_data = [j.line for j in node.dynamic_strings]
                # socket_data =  '\n'.join([j.line for j in self.dynamic_strings]
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

        self.adjust_position_and_dimensions(*self.dims)
        verts = process_grid_for_shader(grid)
        uvs = process_uvs_for_shader(self)

        batch, shader = generate_batch_shader(self, (verts, uvs, lexer))
        config.batch = batch
        config.shader = shader
        config.syntax_mode = self.syntax_mode

        if self.syntax_mode == "Code":
            config.colors = {color_name: getattr(self, color_name)[:] for color_name in lexed_colors}

        draw_data = {
            'tree_name': self.id_data.name[:],
            'node_name': self.name[:],
            'loc': get_desired_xy,
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

    def sv_free(self):
        nvBGL2.callback_disable(node_id(self))

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

classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
