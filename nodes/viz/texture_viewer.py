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

from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL2

palette_dict = {
    "default": (
        (0.243299, 0.590403, 0.836084, 1.00),  # back_color
        (0.390805, 0.754022, 1.000000, 1.00),  # grid_color
        (1.000000, 0.330010, 0.107140, 1.00)   # line_color
    ),
    "scope": (
        (0.274677, 0.366253, 0.386430, 1.00),  # back_color
        (0.423268, 0.558340, 0.584078, 1.00),  # grid_color
        (0.304762, 1.000000, 0.062827, 1.00)   # line_color
    )

}

size_tex_list=[
    ('EXTRA_SMALL','extra_small 64x64px','extra small squared tex: 64px','',64),
    ('SMALL','small 128x128px','small squared tex: 128px','',128),
    ('MEDIUM','medium 256x256px','medium squared tex: 256px','',256),
    ('LARGE','large 512x512px','large squared tex: 512px','',512),
    ('EXTRA_LARGE','extra_large 1024x1024px','extra large squared tex: 1024px','',1024)
]

size_tex_dict = {
    'EXTRA_SMALL': 64,
    'SMALL': 128,
    'MEDIUM': 256,
    'LARGE': 512,
    'EXTRA_LARGE': 1024
}

def simple_screen(x, y, args):

    back_color, grid_color, line_color = args[0]

    texture = args[1]
    size = args[2]
    texname = args[3]
    #print('size of tex inside simple screen: {0}'.format(size))
    texture = 1
    width = size
    height = size

    def draw_borders(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0)):
        #function to draw a border color around the texture
        bgl.glColor4f(*color)
        bgl.glBegin(bgl.GL_LINE_LOOP)

        for coord in [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]:
            bgl.glVertex2f(*coord)

        bgl.glEnd()

    def draw_texture(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0), texname=texname):
        #function to draw a texture
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glTexEnvf(bgl.GL_TEXTURE_ENV, bgl.GL_TEXTURE_ENV_MODE, bgl.GL_REPLACE)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

        bgl.glBegin(bgl.GL_QUADS)

        bgl.glTexCoord2d(0, 0); bgl.glVertex2f( x, y )
        bgl.glTexCoord2d(1, 0); bgl.glVertex2f( x + w , y )
        bgl.glTexCoord2d(1, 1); bgl.glVertex2f( x + w, y - h )
        bgl.glTexCoord2d(0, 1); bgl.glVertex2f( x, y - h )

        bgl.glEnd()

        bgl.glDisable(bgl.GL_TEXTURE_2D)
        #bgl.glDeleteTextures( 1, Buffer )
        bgl.glFlush()

    draw_texture(x=x, y=y, w=width, h=height, color=back_color,texname=texname)

    draw_borders(x=x, y=y, w=width, h=height, color=(0.243299, 0.590403, 0.836084, 1.00))

class SvTextureViewerNode(bpy.types.Node, SverchCustomTreeNode):
    '''Texture Viewer node'''
    bl_idname = 'SvTextureViewerNode'
    bl_label = 'Texture viewer'

    n_id = StringProperty(default='')
    activate = BoolProperty(
        name='Show', description='Activate texture drawing',
        default=True,
        update=updateNode)

    selected_mode = EnumProperty(
        items=size_tex_list,
        description="offers display sizing",
        default="SMALL",
        update=updateNode
    )

    in_float = FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='input for texture', update=updateNode
    )

    theme_mode_options = [(m, m, '', idx) for idx, m in enumerate(["default", "scope"])]
    selected_theme_mode = EnumProperty(
        items=theme_mode_options, default="default", update=updateNode
    )

    def draw_buttons(self, context, l):
        c = l.column()
        c.label(text="set texture display")
        c.prop(self, "selected_mode", text="")
        c.prop(self, 'activate')

    def draw_buttons_ext(self, context, l):
        l.prop(self, "selected_theme_mode")

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'in_float'

    def process(self):

        data = self.inputs['Float'].sv_get(deepcopy=False)[0]
        n_id = node_id(self)

        # end early
        nvBGL2.callback_disable(n_id)

        #print(_data)
        if self.activate:

            size_tex = size_tex_dict.get(self.selected_mode)
            total_size = size_tex * size_tex
            if len(data) < total_size:
                default_value = 0
                new_data = [default_value for j in range(total_size)]
                new_data[:len(data)] = data[:]
                data = new_data
            elif len(data) > total_size:
                data = data[:total_size]
            # and then in init texture
            texture = bgl.Buffer(bgl.GL_FLOAT, total_size, data)

            palette = palette_dict.get(self.selected_theme_mode)[:]
            x, y = [int(j) for j in (self.location + Vector((self.width + 20, 0)))[:]]

            def init_texture(width,height,texname,texture):
                #function to init the texture
                bgl.glShadeModel(bgl.GL_SMOOTH)
                bgl.glEnable(bgl.GL_DEPTH_TEST)

                bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT,1)

                #bgl.glGenTextures(1,Buffer)
                bgl.glGenTextures(1,texture)
                bgl.glEnable(bgl.GL_TEXTURE_2D)
                #glBindTexture(target, texture): texture (unsigned int) – Specifies the name of a texture.
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

                bgl.glActiveTexture(bgl.GL_TEXTURE0)

                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)

                bgl.glTexImage2D(
                       bgl.GL_TEXTURE_2D, 0, bgl.GL_LUMINANCE, width, height, 0,
                       bgl.GL_LUMINANCE, bgl.GL_FLOAT, texture
                   )

            texname = 0

            init_texture(size_tex,size_tex,texname,texture)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'mode': 'custom_function',
                'custom_function': simple_screen,
                'loc': (x, y),
                'args': (palette, texture, size_tex, texname)
            }

            nvBGL2.callback_enable(n_id, draw_data)

    def free(self):
        nvBGL2.callback_disable(node_id(self))

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''


def register():
    bpy.utils.register_class(SvTextureViewerNode)


def unregister():
    bpy.utils.unregister_class(SvTextureViewerNode)
