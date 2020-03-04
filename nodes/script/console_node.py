# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

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
from sverchok.utils.sv_font_xml_parser import get_lookup_dict, letters_to_uv
from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, get_console_grid

# this data need only be generated once, or at runtime at request (low frequency).
grid_data = {}

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
    uniform bool ColorMode;
    
    void main()
    {
        vec4 test_tint = vec4(0.2, 0.7, 1.0, 1.0);
        if (ColorMode) {
            int cIndex = int(v_lexer);
            if (cIndex == 0) { test_tint = vec4(0.9, 0.4, 1.0, 1.0); }
        }
        fragColor = texture(image, texCoord_interp) * test_tint;
        
    }
'''

def random_color_chars(self):
    """
    returns all values [0,1,2,3,...] as floats.
    the reason i'm using floats is because i didn't figure out a better way to a single
    integer per tri-angle, so i am passing a float per vertex, because an int per vertex can not
    be interpolated for all pixels in the fragment.
    """
    array_size = self.terminal_width * self.num_rows
    ints = np.random.randint(0, 4, size=array_size)
    floats = np.array(ints, dtype='int').repeat(6).tolist()
    return floats

def syntax_highlight_basic(text):
    """
    this uses the built in lexer/tokenizer in python to identify part of code
    will return a meaningful lookuptable for index colours per character
    """
    import tokenize
    import io
    import token

    # token.tok_name  <--- dict of token-kinds.

    with io.StringIO(text) as f:

        tokens = tokenize.generate_tokens(f.readline)
        # for token in tokens:
        #    print(token)


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
        

def text_decompose(content):
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
        return_str, width = ensure_line_padding(content)
    else:
        return_str, width = ensure_line_padding("no valid text found\nfeed it multiline\ntext")

    dims = width, len(return_str)
    return return_str, dims


def terminal_text_to_uv(lines):
    fnt = get_lookup_dict(r"C:\Users\zeffi\Desktop\GITHUB\sverchok\utils\modules\bitmap_font\consolas.fnt") 
    uvs = []
    for line in lines.split("\n"):
        uvs.extend(letters_to_uv(line, fnt))
    return uvs


def simple_console_xy(context, args):
    image, config = args
    # matrix = bpy.context.region_data.perspective_matrix
    matrix = gpu.matrix.get_projection_matrix()

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)
    config.shader.bind()
    config.shader.uniform_float("ModelViewProjectionMatrix", matrix)
    config.shader.uniform_int("image", 0)
    config.shader.uniform_bool("ColorMode", [bool(config.color_mode)])
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


def generate_batch_shader(node, args):
    x, y, w, h, data = args
    verts, uv_indices, lexer = data
    print(len(verts), len(lexer))

    # shader = gpu.shader.from_builtin('2D_IMAGE')
    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
    batch = batch_for_shader(shader, 'TRIS', {"pos": verts, "texCoord": uv_indices, "lexer": lexer})
    return batch, shader

class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode, SvNodeViewDrawMixin):
    
    """
    Triggers: Console 
    Tooltip:  Console for Sverchok node

    This node prints the input to the nodeview using a fixedwidth character map.
    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'CONSOLE'

    @throttled
    def local_updateNode(self, context):
        # self.process()
        ...

    num_rows: bpy.props.IntProperty(name="num rows", default=3, min=1, max=140) #, update=updateNode)
    terminal_width: bpy.props.IntProperty(name="terminal width", default=10, min=2, max=140) #, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    char_image: bpy.props.StringProperty(name="image name", update=local_updateNode, default="consolas_0.png")
    terminal_text: bpy.props.StringProperty(name="terminal text", default="1234567890\n0987654321\n098765BbaA")
    
    texture = {}
    n_id: bpy.props.StringProperty(default='')
    local_scale: bpy.props.FloatProperty(default=1.0, min=0.2, update=updateNode)
    show_me: bpy.props.BoolProperty(default=True, name="show me", update=updateNode)
    color_mode: bpy.props.BoolProperty(default=True, name="show colors", update=updateNode)

    # num_chars: bpy.props.IntProperty(min=2, default=20, update=updateNode)

    def prepare_for_grid(self):
        char_width = int(15 * self.local_scale)
        char_height = int(32 * self.local_scale)
        return get_console_grid(char_width, char_height, self.terminal_width, self.num_rows)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "text")
        self.get_and_set_gl_scale_info()

    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "show_me", text="", icon="HIDE_OFF")
        row.separator()
        row.prop(self, "local_scale")
        row2 = layout.row(align=True)
        row2.prop(self, "color_mode", toggle=True)
    
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "char_image")

    def terminal_text_to_config(self, update=False):

        with self.sv_throttle_tree_update():

            socket_data = self.inputs[0].sv_get()

            # this will find the newline delimited text from Object ID selector.
            if len(socket_data) == 1:
                socket_data = socket_data[0]
                if isinstance(socket_data, list) and len(socket_data) and isinstance(socket_data[0], str):

                    multiline, (chars_x, chars_y) = text_decompose('\n'.join(socket_data))
                    valid_multiline = '\n'.join(multiline)
                    self.terminal_text = valid_multiline
                    self.num_rows = chars_y
                    self.terminal_width = chars_x

        if update:
            updateNode(self, None)


    def process(self):
        n_id = node_id(self)
        nvBGL2.callback_disable(n_id)

        if not self.char_image or not self.show_me:
            return
        
        image = bpy.data.images.get(self.char_image)
        if not image or image.gl_load():
            raise Exception()

        if not self.inputs[0].is_linked or not self.inputs[0].sv_get():
            return

        self.terminal_text_to_config()
        # syntax_highlight_basic(self.terminal_text)
        lexer = random_color_chars(self)

        config = lambda: None
        grid = self.prepare_for_grid()
        x, y = self.xy_offset
        width = self.terminal_width * 15
        height = self.num_rows * 32

        x, y, width, height = self.adjust_position_and_dimensions(x, y, width, height)
        verts = process_grid_for_shader(grid, loc=(x, y))
        uvs = process_uvs_for_shader(self)

        batch, shader = generate_batch_shader(self, (x, y, width, height, (verts, uvs, lexer)))

        dims = (width, height)
        config.loc = (x, y)
        config.batch = batch
        config.shader = shader
        config.color_mode = self.color_mode

        draw_data = {
            'tree_name': self.id_data.name[:],
            'mode': 'custom_function_context', 
            'custom_function': simple_console_xy,
            'args': (image, config)
        }
        nvBGL2.callback_enable(n_id, draw_data)


    def free(self):
        nvBGL2.callback_disable(node_id(self))
        # self.delete_texture()

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''



classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
