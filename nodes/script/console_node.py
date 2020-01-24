# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# pylint: disable=c0103

import bpy
from mathutils import Vector, Matrix

# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.geom import grid
from sverchok.utils.sv_font_xml_parser import get_lookup_dict

"""
import bpy
import gpu
import bgl
from gpu_extras.batch import batch_for_shader

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


def letter_to_uv(letters, fnt):
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


def tri_grid(dim_x, dim_y, nx, ny):
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
grid_data[(30, 30, 120, 80)] = tri_grid(30, 30, 120, 80)


class SvConsoleNode(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: Console 
    Tooltip:  Console for Sverchok node

    This node prints the input to the nodeview using a fixedwidth character map.
    """

    bl_idname = 'SvConsoleNode'
    bl_label = 'Console Node'
    bl_icon = 'GREASEPENCIL'

    num_rows: bpy.props.IntProperty(name="num rows", default=30, min=1, max=140, update=updateNode)
    num_chars: bpy.props.IntProperty(name="num chars", default=30, min=10, max=140, update=updateNode)
    use_char_colors: bpy.props.BoolProperty(name="use char colors", update=updateNode)
    char_image: bpy.props.StringProperty(name="image name", update=updateNode)

    def sv_init(self, context):
        self.inputs("SvStringsSocket", "text")

    def draw_buttons(self, context, layout):
        """
        [ num rows = 30 ] , 
        [ num chars wide = 120 ]
        [ color chars bool ]
        [ charset to use ]

        """
        layout.prop(self, "char_image")

    def process(self):
        
        if self.char_image:
            ...
        ...



classes = [SvConsoleNode]
register, unregister = bpy.utils.register_classes_factory(classes)
