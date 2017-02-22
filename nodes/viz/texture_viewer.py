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

import bgl

from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL2

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

bitmap_save_list=[
    ('PNG','png format', 'save texture in .png fromat','',0),
    ('TGA','tga format','save texture in .tga fromat','',1),
    ('TIFF','tiff format','save texture in .tiff format','',2),
    ('BMP','bmp format','save texture in .tiff format','',3),
    ('JPEG','jpeg format','save texture in .jpeg format','',4)
]

def simple_screen(x, y, args):
    #draw a simple scren display for the texture
    border_color = (0.390805, 0.754022, 1.000000, 1.00)

    texture = args[0]
    size = args[1]
    texname = args[2]

    width = size
    height = size

    def draw_borders(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0)):
        #function to draw a border color around the texture
        bgl.glColor4f(*color)
        bgl.glBegin(bgl.GL_LINE_LOOP)

        for coord in [(x, y), (x+w, y), (w+x, y-h), (x, y-h)]:
            bgl.glVertex2f(*coord)

        bgl.glEnd()

    def draw_texture(x=0, y=0, w=30, h=10, texname=texname):
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

    draw_texture(x=x, y=y, w=width, h=height, texname=texname)

    draw_borders(x=x, y=y, w=width, h=height, color=border_color)

class SvTextureViewerNode(bpy.types.Node, SverchCustomTreeNode):
    '''Texture Viewer node'''
    bl_idname = 'SvTextureViewerNode'
    bl_label = 'Texture viewer'
    texture = []

    n_id = StringProperty(default='')
    activate = BoolProperty(
        name='Show', description='Activate texture drawing',
        default=True,
        update=updateNode)

    selected_mode = EnumProperty(
        items=size_tex_list,
        description="Offers display sizing",
        default="SMALL",
        update=updateNode
    )

    bitmap_save = EnumProperty(
        items=bitmap_save_list,
        description="Offers bitmap saving",
        default="PNG"
    )

    in_float = FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='Input for texture', update=updateNode
    )

    def get_buffer(self):
        data = self.inputs['Float'].sv_get(deepcopy=False)[0]
        size_tex = size_tex_dict.get(self.selected_mode)
        total_size = size_tex * size_tex
        if len(data) < total_size:
            default_value = 0
            new_data = [default_value for j in range(total_size)]
            new_data[:len(data)] = data[:]
            data = new_data
        elif len(data) > total_size:
            data = data[:total_size]

        texture = bgl.Buffer(bgl.GL_FLOAT, total_size, data)
        return texture

    def draw_buttons(self, context, l):
        c = l.column()
        c.label(text="Set texture display:")
        c.prop(self, "selected_mode", text="")
        c.prop(self, 'activate')

    def draw_buttons_ext(self, context, l):
        l.label(text="Save texture as a bitmap image, choose a format:")
        l.separator()
        l.prop(self, "bitmap_save")
        l.separator()
        l.operator("node.scriptlite_ui_callback", text="S A V E").fn_name="save_bitmap"

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'in_float'

    def process(self):
        n_id = node_id(self)

        # end early
        nvBGL2.callback_disable(n_id)

        if self.activate:

            texture = self.get_buffer()

            size_tex = size_tex_dict.get(self.selected_mode)

            x, y = [int(j) for j in (self.location + Vector((self.width + 20, 0)))[:]]

            def init_texture(width,height,texname,texture):
                #function to init the texture
                bgl.glShadeModel(bgl.GL_SMOOTH)
                bgl.glEnable(bgl.GL_DEPTH_TEST)

                bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT,1)

                bgl.glGenTextures(1,texture)

                bgl.glEnable(bgl.GL_TEXTURE_2D)

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
                'args': (texture, size_tex, texname)
            }

            nvBGL2.callback_enable(n_id, draw_data)

    def free(self):
        nvBGL2.callback_disable(node_id(self))

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def save_bitmap(self, image_name='image_name', filepath_raw='', alpha=False, texture=texture):
        import numpy as np
        buf = self.get_buffer()
        img_format = self.bitmap_save
        image_name = image_name + '.' + img_format.lower()
        dim = size_tex_dict[self.selected_mode]
        width, height = dim, dim
        img = []
        if image_name in bpy.data.images:
            img = bpy.data.images[image_name]
        else:
            img = bpy.data.images.new(name=image_name,width=width,height=height,alpha=alpha,float_buffer=True)

        np_buff = np.empty(len(img.pixels), dtype=np.float32)
        np_buff.shape = (-1, 4)
        np_buff[:,:] = np.array(buf)[:,np.newaxis]
        np_buff[:,3] = 1
        np_buff.shape = -1
        img.pixels[:] = np_buff

        img.filepath_raw = "/tmp/" + image_name
        img.save()
        print('saved!')

def register():
    bpy.utils.register_class(SvTextureViewerNode)


def unregister():
    bpy.utils.unregister_class(SvTextureViewerNode)
