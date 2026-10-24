# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import io
import os
import token
import tokenize
import itertools
import numpy as np

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

# shader bodies only, declarations come from GPUShaderCreateInfo (see build_shader)
vertex_shader = '''
    void main()
    {
       v_lexer = lexer;
       gl_Position = viewProjectionMatrix * vec4(pos.x + x_offset, pos.y + y_offset, 0.0, 1.0);
       texCoord_interp = texCoord;
    }
'''

no_fragment_shader = '''
    void main()
    {
        fragColor = texture(image, texCoord_interp);
    }
'''

fragment_shader = '''
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


_gpu_cache = {}


def get_font_texture():
    """
    the 256*256 greyscale atlas, uploaded once and shared by all console nodes.
    replaces the bgl glGenTextures / glTexImage2D path (no-ops since Blender 3.5)
    """
    tex = _gpu_cache.get('texture')
    if tex is None:
        data = np.load(get_font_pydata_location())['a'].astype(np.float32)
        rgba = np.empty((data.size, 4), dtype=np.float32)
        rgba[:, :3] = data[:, None]
        rgba[:, 3] = 1.0
        buf = gpu.types.Buffer('FLOAT', rgba.size, rgba.ravel())
        tex = _gpu_cache['texture'] = gpu.types.GPUTexture((256, 256), format='RGBA16F', data=buf)
        if hasattr(tex, 'filter_mode'):
            tex.filter_mode(True)
    return tex


def build_shader(syntax_mode):
    shader = _gpu_cache.get(syntax_mode)
    if shader is not None:
        return shader

    iface = gpu.types.GPUStageInterfaceInfo(f"sv_console_iface_{syntax_mode}")
    iface.smooth('VEC2', "texCoord_interp")
    iface.flat('FLOAT', "v_lexer")

    info = gpu.types.GPUShaderCreateInfo()
    info.push_constant('MAT4', "viewProjectionMatrix")
    info.push_constant('FLOAT', "x_offset")
    info.push_constant('FLOAT', "y_offset")
    if syntax_mode == "Code":
        for color_name in lexed_colors:
            info.push_constant('VEC4', color_name)
    info.sampler(0, 'FLOAT_2D', "image")
    info.vertex_in(0, 'VEC2', "pos")
    info.vertex_in(1, 'VEC2', "texCoord")
    info.vertex_in(2, 'FLOAT', "lexer")
    info.vertex_out(iface)
    info.fragment_out(0, 'VEC4', "fragColor")
    info.vertex_source(vertex_shader)
    info.fragment_source({
        "None": no_fragment_shader, "f1": fragment_shader, "Code": lexed_fragment_shader}[syntax_mode])

    shader = _gpu_cache[syntax_mode] = gpu.shader.create_from_info(info)
    return shader


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

def safe_tokens(text):
    """
    yields (token, row_offset). Since Python 3.12 tokenize uses the C tokenizer and raises on
    anything that isn't valid Python (it used to emit ERRORTOKEN and carry on). On an error we
    skip the offending line and resume tokenizing from the next one, so one bad line doesn't
    stop the rest of the text from being processed.
    """
    lines = text.splitlines(keepends=True)
    offset = 0
    while offset < len(lines):
        with io.StringIO("".join(lines[offset:])) as f:
            try:
                for tok in tokenize.generate_tokens(f.readline):
                    yield tok, offset
                return
            except (tokenize.TokenError, SyntaxError) as err:
                if isinstance(err, SyntaxError):
                    lineno = err.lineno
                else:
                    lineno = err.args[1][0] if len(err.args) > 1 and err.args[1] else None
                if not lineno:
                    return
                offset += lineno


# color categories, these are the indices the shaders switch on (kept stable, independent of
# the token module whose numbering changes between Python versions)
LEX_NAME, LEX_NUMBER, LEX_STRING = 1, 2, 3
LEX_PAREN, LEX_BRACKET, LEX_EQUALS, LEX_BRACE = 7, 9, 22, 25
LEX_OP, LEX_COMMENT = 54, 55
LEX_KEYWORD, LEX_BUILTIN, LEX_QUALIFIER = 90, 91, 92

KEYWORDS = {
    'print', 'break', 'continue', 'return', 'while', 'or', 'and', 'not', 'is', 'dir', 'pass',
    'if', 'elif', 'else', 'in', 'as', 'with', 'from', 'import', 'for', 'global', 'nonlocal',
    'try', 'except', 'finally', 'raise', 'assert', 'del', 'async', 'await'}
QUALIFIERS = {'def', 'class', 'lambda'}
BUILTINS = {'False', 'True', 'None', 'yield', 'repr', 'range', 'enumerate', 'len', 'zip', 'self'}

STRING_TYPES = {token.STRING} | {getattr(token, n) for n in ('FSTRING_START', 'FSTRING_MIDDLE', 'FSTRING_END',
                                                           'TSTRING_START', 'TSTRING_MIDDLE', 'TSTRING_END')
                                 if hasattr(token, n)}
SKIP_TYPES = {token.ENDMARKER, token.NEWLINE, token.NL, token.INDENT, token.DEDENT, token.ENCODING}
OP_CATEGORIES = {
    token.LPAR: LEX_PAREN, token.RPAR: LEX_PAREN,
    token.LSQB: LEX_BRACKET, token.RSQB: LEX_BRACKET,
    token.LBRACE: LEX_BRACE, token.RBRACE: LEX_BRACE,
    token.EQUAL: LEX_EQUALS}


def token_category(tok):
    if tok.type == token.NAME:
        if tok.string in KEYWORDS:
            return LEX_KEYWORD
        if tok.string in QUALIFIERS:
            return LEX_QUALIFIER
        if tok.string in BUILTINS:
            return LEX_BUILTIN
        return LEX_NAME
    if tok.type == token.NUMBER:
        return LEX_NUMBER
    if tok.type in STRING_TYPES:
        return LEX_STRING
    if tok.type == token.COMMENT:
        return LEX_COMMENT
    if tok.type == token.OP:
        return OP_CATEGORIES.get(tok.exact_type, LEX_OP)
    return LEX_NAME


def syntax_highlight_basic(node):
    """
    uses python's tokenizer to identify parts of code, returns a color category per character
    """
    width = node.terminal_width
    array_size = width * node.num_rows
    categories = np.full(array_size, float(LEX_NAME))

    # terminal_text is padded with trailing spaces to a rectangular grid. Tokenize the unpadded
    # lines instead: positions are identical, and a padded "\\" line continuation is a syntax error
    text = "\n".join(line.rstrip() for line in node.terminal_text.split("\n"))

    for tok, row_offset in safe_tokens(text):
        if tok.type in SKIP_TYPES or not tok.string or tok.start == tok.end:
            continue
        (row_start, char_start), (row_end, char_end) = tok.start, tok.end
        index1 = (row_start - 1 + row_offset) * width + char_start
        index2 = (row_end - 1 + row_offset) * width + char_end
        categories[max(index1, 0):min(index2, array_size)] = token_category(tok)

    return categories.reshape((-1, width))

def filter_incoming(socket_data):
    """
    a preprocessing step, inefficient, to replace all long string tokens with an abbreviated line + [...]
    """

    import textwrap

    text = socket_data[0]
    line_indices_done = set()

    replacements = {}
    for tok, row_offset in safe_tokens(text):
        if tok.type != token.STRING:
            continue
        if not tok.start[0] == tok.end[0]:
            # this is a multiline nicely formatted textstring.. should be OK.
            continue
        if not ((tok.end[1] - tok.start[1]) > 80):
            continue

        # if reaches here, then we have a single line, very long string
        suggested_line = textwrap.shorten(tok.string, width=80) + "\""
        start = (tok.start[0] + row_offset, tok.start[1])
        end = (tok.end[0] + row_offset, tok.end[1])
        replacements[(start, end)] = suggested_line

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
    _, config = args
    if config.failed:
        return
    try:
        _draw_console(config, loc)
    except Exception as err:
        # report once, then stay silent until the node is processed again
        config.failed = True
        print(f"Console node: drawing disabled, {type(err).__name__}: {err}")


def _draw_console(config, loc):
    shader = build_shader(config.syntax_mode)
    if config.batch is None:
        verts, uvs, lexer = config.data
        if lexer is None:
            lexer = [0.0] * len(verts)
        config.batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uvs, "lexer": lexer})

    shader.bind()
    shader.uniform_float("viewProjectionMatrix", gpu.matrix.get_projection_matrix())

    if config.syntax_mode == "Code":
        for color_name, color_value in config.colors.items():
            shader.uniform_float(color_name, color_value)

    x, y = loc
    shader.uniform_float("x_offset", x)
    shader.uniform_float("y_offset", y)
    shader.uniform_sampler("image", get_font_texture())
    config.batch.draw(shader)

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

        config = lambda: None

        lexer = self.get_lexer()
        grid = self.prepare_for_grid()

        self.adjust_position_and_dimensions(*self.dims)
        verts = process_grid_for_shader(grid)
        uvs = process_uvs_for_shader(self)

        config.data = (verts, uvs, lexer)
        config.batch = None   # built on first draw, needs the GPU context
        config.failed = False
        config.syntax_mode = self.syntax_mode

        if self.syntax_mode == "Code":
            config.colors = {color_name: getattr(self, color_name)[:] for color_name in lexed_colors}

        draw_data = {
            'tree_name': self.id_data.name[:],
            'node_name': self.name[:],
            'loc': get_desired_xy,
            'mode': 'custom_function_context', 
            'custom_function': simple_console_xy,
            'args': (None, config)
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
