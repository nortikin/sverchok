# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.settings import get_params
from sverchok.data_structure import updateNode, node_id

from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.utils.geom import grid
from sverchok.utils.sv_font_xml_parser import get_lookup_dict
from sverchok.utils.sv_nodeview_draw_helper import SvNodeViewDrawMixin

"""

IMAGE_NAME = "Untitled"
image = bpy.data.images[IMAGE_NAME]

shader = gpu.shader.from_builtin('2D_IMAGE')
batch = batch_for_shader(
    shader, 'TRI_FAN',
    {
        "pos": ((100, 100), (200, 100), (200, 200), (100, 200)),
        "texCoord": ((0, 0), (1, 0), (1, 1), (0, 1)),
    },
)

if image.gl_load():
    raise Exception()


def draw():
    bgl.glActiveTexture(bgl.GL_TEXTURE0)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, image.bindcode)

    shader.bind()
    shader.uniform_int("image", 0)
    batch.draw(shader)


bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_PIXEL')
"""


def letters_to_uv(letters, fnt):
    """
    expects a 1 or more list of letters, converts to ordinals
    """
    uvs = []
    add_uv = uvs.extend
    unrecognized = fnt.get(ord(':')) 

    for letter in ordinals:
        ordinal = ord(letter)
        details = fnt.get(ordinal, unrecognized)
        add_uv(details)

    return uvs

def process_string_to_charmap(node, str):
    for line in str.split():
        line_limited = line[:node.terminal_width]
        # ord(char) , a = 65

def triangles_from_quads(faces):
    r"""
    this splits up the quad from geom.grid to triangles

                (ABCD)                   (ABC, ACD)

    go from:    A - - - B           to    A - B            A 
                |       |                  \  |            | \
                |       |                   \ |            |  \
                D - - - C                     C            D - C

    """
    tri_faces = []
    tris_add = tri_faces.extend
    _ = [tris_add(((poly[0], poly[1], poly[2]), (poly[0], poly[2], poly[3]))) for poly in faces]
    return tri_faces


def tri_grid(dim_x=3, dim_y=2, nx=3, ny=3):
    """
    This generates 2d grid, into which we texture each polygon with it's associated character UV

    AA -  -  -AB -  -  -AC -  -  -AD -  -  - n
     | -       | -       | -       |
     |    -    |    -    |    -    |
     |       - |       - |       - |
    BA -  -  -BB -  -  -BC -  - 
     | -       | -
     |    -    |    -
     |       - |       -
    CA -  -  -CB -  -  -
     | -
     |    -
     |       -
    etc

    There's a mapping between int(char) to uv coordinates, charmap will support ascii only.

    """
    neg_y = Matrix(((1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))
    verts, _, faces = grid(dim_x, dim_y, nx, ny, anchor=7, matrix=neg_y, mode='pydata')
    tri_faces = triangles_from_quads(faces)
    return verts, tri_faces


# this data need only be generated once, or at runtime at request (low frequency).
grid_data = {}


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



    num_rows: bpy.props.IntProperty(name="num rows", default=30, min=1, max=140, update=updateNode)
    terminal_width: bpy.props.IntProperty(name="terminal width", default=30, min=10, max=140, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    char_image: bpy.props.StringProperty(name="image name", update=local_updateNode)
    terminal_text: bpy.props.StringProperty(name="terminal text")

    texture = {}
    n_id: StringProperty(default='')


    def sv_init(self, context):
        self.inputs("SvStringsSocket", "text")
        self.get_and_set_gl_scale_info()
        initial_state = (15, 32, self.terminal_width, self.num_rows)
        grid_data[initial_state] = tri_grid(dim_x=15, dim_y=32, nx=self.terminal_width, ny=self.num_rows)

    def draw_buttons(self, context, layout):
        layout.prop(self, "char_image")


    def process(self):
    
        n_id = node_id(self)
        nvBGL2.callback_disable(n_id)

        # nope
        if not self.char_image:
            return
        
        # yep
        x, y = self.xy_offset
        x, y, width, height = self.adjust_position_and_dimensions(x, y, width, height)
        batch, shader = self.generate_batch_shader((x, y, width, height))

        draw_data = {
            'tree_name': self.id_data.name[:],
            'mode': 'custom_function',
            'custom_function': simple_screen,
            'loc': (x, y),
            'args': (texture, self.texture[n_id], width, height, batch, shader, cMode)
        }

        nvBGL2.callback_enable(n_id, draw_data)


    def free(self):
        nvBGL2.callback_disable(node_id(self))
        self.delete_texture()

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''



classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
