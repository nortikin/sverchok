# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import inspect

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
from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin, tri_grid


demo_text = inspect.getsource(tri_grid)

# this data need only be generated once, or at runtime at request (low frequency).
grid_data = {}

def terminal_text_to_uv(lines):
    fnt = get_lookup_dict(r"C:\Users\zeffi\Desktop\GITHUB\sverchok\utils\modules\bitmap_font\consolas.fnt") 
    uvs = []
    for line in lines.split():
        uvs.extend(letters_to_uv(line, fnt))
    return uvs


def simple_console_xy(context, args):
    image, config = args

    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)
    config.shader.bind()
    config.shader.uniform_int("image", 0)
    config.batch.draw(config.shader)

def generate_batch_shader(node, args):
    x, y, w, h, data = args
    positions, poly_indices = data
    uv_indices = terminal_text_to_uv(node.terminal_text)
    positions = [vec[:2] for vec in positions]


    print(len(positions), len(uv_indices), len(poly_indices))

    shader = gpu.shader.from_builtin('2D_IMAGE')
    batch = batch_for_shader(shader, 'TRIS', {"pos": positions, "texCoord": uv_indices}, indices=poly_indices)
    return batch, shader

class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode, SvNodeViewDrawMixin):
    
    """
    Triggers: Console 
    Tooltip:  Console for Sverchok node

    This node prints the input to the nodeview using a fixedwidth character map.
    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'GREASEPENCIL'

    @throttled
    def local_updateNode(self, context):
        ...



    num_rows: bpy.props.IntProperty(name="num rows", default=3, min=1, max=140, update=updateNode)
    terminal_width: bpy.props.IntProperty(name="terminal width", default=10, min=10, max=140, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    char_image: bpy.props.StringProperty(name="image name", update=local_updateNode, default="consolas_0.png")
    terminal_text: bpy.props.StringProperty(name="terminal text", default="012356 8922\n012356 8922\n012356 8922")

    texture = {}
    n_id: bpy.props.StringProperty(default='')


    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "text")
        self.get_and_set_gl_scale_info()
        initial_state = (15, 32, self.terminal_width+1, self.num_rows+1)
        grid_data[initial_state] = tri_grid(dim_x=15, dim_y=32, nx=self.terminal_width+1, ny=self.num_rows+1)

    def draw_buttons(self, context, layout):
        layout.prop(self, "char_image")

    def process(self):
        n_id = node_id(self)
        nvBGL2.callback_disable(n_id)

        if not self.char_image:
            return
        
        image = bpy.data.images.get(self.char_image)
        if not image: # or image.gl_load():
            raise Exception()

        config = lambda: None

        grid = grid_data[(15, 32, self.terminal_width+1, self.num_rows+1)]
        if not grid:
            grid_data[(15, 32, self.terminal_width+1, self.num_rows+1)] = tri_grid(dim_x=15, dim_y=32, nx=self.terminal_width+1, ny=self.num_rows+1)
            grid = grid_data[(15, 32, self.terminal_width+1, self.num_rows+1)]
        
        x, y = self.xy_offset
        
        width = self.terminal_width * 15
        height = self.num_rows * 32

        x, y, width, height = self.adjust_position_and_dimensions(x, y, width, height)
        batch, shader = generate_batch_shader(self, (x, y, width, height, grid))

        dims = (w, h)
        loc = (x, y)
        config.loc = loc
        config.scale = scale
        config.batch = batch
        config.shader = shader
        config.grid_data = grid

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
