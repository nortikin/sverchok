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

import os
import numpy as np

import bgl
import bpy
from bpy.props import FloatProperty, EnumProperty, StringProperty, BoolProperty

from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import nodeview_bgl_viewer_draw_mk2 as nvBGL2

from sverchok.utils.sv_operator_mixins import (
    SvGenericDirectorySelector, SvGenericCallbackWithParams
)


class SvTextureViewerOperator(bpy.types.Operator, SvGenericCallbackWithParams):
    """ Save the image with passed settings """
    bl_idname = "node.sv_texview_callback"
    bl_label = "Execute a function on the calling node"

class SvTextureViewerDirSelect(bpy.types.Operator, SvGenericDirectorySelector):
    """ Pick the directory to store images in """
    bl_idname = "node.sv_texview_dirselect"
    bl_label = "Pick directory"



size_tex_list = [
    ('XS', 'XS', 'extra small squared tex: 64px', '', 64),
    ('S', 'S', 'small squared tex: 128px', '', 128),
    ('M', 'M', 'medium squared tex: 256px', '', 256),
    ('L', 'L', 'large squared tex: 512px', '', 512),
    ('XL', 'XL', 'extra large squared tex: 1024px', '', 1024)
]

size_tex_dict = {item[0]: item[4] for item in size_tex_list}

bitmap_format_list = [
    ('PNG', 'png format', 'save texture in .png fromat', '', 0),
    ('TARGA', 'tga format', 'save texture in .tga fromat', '', 1),
    ('TIFF', 'tiff format', 'save texture in .tiff format', '', 2),
    ('BMP', 'bmp format', 'save texture in .tiff format', '', 3),
    ('JPEG', 'jpeg format', 'save texture in .jpeg format', '', 4)
]


def simple_screen(x, y, args):
    # draw a simple scren display for the texture
    border_color = (0.390805, 0.754022, 1.000000, 1.00)

    texture = args[0]
    size = args[1]
    texname = args[2]

    width = size
    height = size

    def draw_borders(x=0, y=0, w=30, h=10, color=(0.0, 0.0, 0.0, 1.0)):
        # function to draw a border color around the texture
        bgl.glColor4f(*color)
        bgl.glBegin(bgl.GL_LINE_LOOP)

        for coord in [(x, y), (x + w, y), (w + x, y - h), (x, y - h)]:
            bgl.glVertex2f(*coord)

        bgl.glEnd()

    def draw_texture(x=0, y=0, w=30, h=10, texname=texname):
        # function to draw a texture
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glTexEnvf(bgl.GL_TEXTURE_ENV,
                      bgl.GL_TEXTURE_ENV_MODE,
                      bgl.GL_REPLACE)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

        bgl.glBegin(bgl.GL_QUADS)

        bgl.glTexCoord2d(0, 1)
        bgl.glVertex2f(x, y)
        bgl.glTexCoord2d(1, 1)
        bgl.glVertex2f(x + w, y)
        bgl.glTexCoord2d(1, 0)
        bgl.glVertex2f(x + w, y - h)
        bgl.glTexCoord2d(0, 0)
        bgl.glVertex2f(x, y - h)

        bgl.glEnd()

        bgl.glDisable(bgl.GL_TEXTURE_2D)
        # bgl.glDeleteTextures( 1, Buffer )
        bgl.glFlush()

    draw_texture(x=x, y=y, w=width, h=height, texname=texname)

    draw_borders(x=x, y=y, w=width, h=height, color=border_color)


class SvTextureViewerNode(bpy.types.Node, SverchCustomTreeNode):
    '''Texture Viewer node'''
    bl_idname = 'SvTextureViewerNode'
    bl_label = 'Texture viewer'
    texture = {}

    n_id = StringProperty(default='')
    activate = BoolProperty(
        name='Show', description='Activate texture drawing',
        default=True,
        update=updateNode)

    selected_mode = EnumProperty(
        items=size_tex_list,
        description="Offers display sizing",
        default="S",
        update=updateNode
    )

    bitmap_format = EnumProperty(
        items=bitmap_format_list,
        description="Offers bitmap saving",
        default="PNG"
    )

    in_float = FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='Input for texture', update=updateNode
    )

    base_dir = StringProperty(default='/tmp/')
    image_name = StringProperty(default='image_name', description='name (minus filetype)')

    @property
    def xy_offset(self):
        a = self.location[:]
        b = int(self.width) + 20
        return int(a[0] + b), int(a[1])

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

    def draw_buttons(self, context, layout):
        c = layout.column()
        c.label(text="Set texture display:")
        row = c.row()
        row.prop(self, "selected_mode", expand=True)
        c.prop(self, 'activate')

    def draw_buttons_ext(self, context, layout):
        callback_to_self = "node.sv_texview_callback"
        directory_select = "node.sv_texview_dirselect"
        
        layout.label(text="Save texture as a bitmap")
        
        layout.separator()
        layout.prop(self, "bitmap_format", text='format')
        layout.separator()

        row = layout.row(align=True)
        leftside = row.split(0.7)
        leftside.prop(self, 'image_name', text='')
        rightside = leftside.split().row(align=True)
        rightside.operator(callback_to_self, text="Save").fn_name = "save_bitmap"
        rightside.operator(directory_select, text="", icon='IMASEL').fn_name = "set_dir"

    def draw_label(self):
        return (self.label or self.name) + ' ' + str(size_tex_dict.get(self.selected_mode)) + "^2"

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Float").prop_name = 'in_float'

    def delete_texture(self):
        n_id = node_id(self)
        if n_id in self.texture:
            names = bgl.Buffer(bgl.GL_INT, 1, [self.texture[n_id]])
            bgl.glDeleteTextures(1, names)

    def process(self):
        n_id = node_id(self)

        # end early
        nvBGL2.callback_disable(n_id)
        self.delete_texture()
        if self.activate:

            texture = self.get_buffer()
            size_tex = size_tex_dict.get(self.selected_mode)
            x, y = self.xy_offset

            def init_texture(width, height, texname, texture):
                # function to init the texture
                bgl.glShadeModel(bgl.GL_SMOOTH)

                bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT, 1)

                bgl.glEnable(bgl.GL_TEXTURE_2D)
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)
                bgl.glActiveTexture(bgl.GL_TEXTURE0)

                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
                bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)

                bgl.glTexImage2D(
                    bgl.GL_TEXTURE_2D,
                    0, bgl.GL_LUMINANCE, width, height,
                    0, bgl.GL_LUMINANCE, bgl.GL_FLOAT, texture
                )

            name = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, name)
            self.texture[n_id] = name[0]
            init_texture(size_tex, size_tex, name[0], texture)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'mode': 'custom_function',
                'custom_function': simple_screen,
                'loc': (x, y),
                'args': (texture, size_tex, self.texture[n_id])
            }

            nvBGL2.callback_enable(n_id, draw_data)

    def free(self):
        nvBGL2.callback_disable(node_id(self))
        self.delete_texture()

    # reset n_id on copy
    def copy(self, node):
        self.n_id = ''

    def set_dir(self, operator):
        self.base_dir = operator.directory
        print('new base dir:', self.base_dir)   #####
        return {'FINISHED'}

    def save_bitmap(self, operator):
        alpha = False

        # if self.image_name was empty it will give a default
        image_name = self.image_name or 'image_name'

        # save a texture in a bitmap image
        # in different formats supported by blender
        buf = self.get_buffer()
        img_format = self.bitmap_format
        extension = '.' + img_format.lower().replace('targa', 'tga')
        image_name = image_name + extension
        dim = size_tex_dict[self.selected_mode]
        width, height = dim, dim

        if image_name in bpy.data.images:
            img = bpy.data.images[image_name]
        else:
            img = bpy.data.images.new(name=image_name, width=width,
                                      height=height, alpha=alpha,
                                      float_buffer=True)
        img.scale(width, height)
        np_buff = np.empty(len(img.pixels), dtype=np.float32)
        np_buff.shape = (-1, 4)
        np_buff[:, :] = np.array(buf)[:, np.newaxis]
        np_buff[:, 3] = 1
        np_buff.shape = -1
        img.pixels[:] = np_buff

        # get the scene context
        scene = bpy.context.scene
        scene.render.image_settings.file_format = img_format
        # get the path for the file and save the image
        
        desired_path = os.path.join(self.base_dir, self.image_name + extension)   #####


        img.save_render(desired_path, scene)
        print('Saved!  path is:', desired_path)


def register():
    bpy.utils.register_class(SvTextureViewerOperator)
    bpy.utils.register_class(SvTextureViewerDirSelect)
    bpy.utils.register_class(SvTextureViewerNode)


def unregister():
    bpy.utils.unregister_class(SvTextureViewerNode)
    bpy.utils.unregister_class(SvTextureViewerDirSelect)
    bpy.utils.unregister_class(SvTextureViewerOperator)
