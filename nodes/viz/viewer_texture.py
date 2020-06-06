# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# contributors:
#   kalwalt
#   zeffii

import os
import numpy as np

import bpy
import gpu
import bgl

from bpy.props import (
    FloatProperty, EnumProperty, StringProperty, BoolProperty, IntProperty
)

from sverchok.settings import get_params
from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL2
from sverchok.ui import sv_image as svIMG

# shared stuff between implementations
from sverchok.utils.sv_texture_utils import generate_batch_shader
from sverchok.utils.sv_texture_utils import simple_screen, init_texture, get_drawing_location
from sverchok.utils.sv_texture_utils import gl_color_list, gl_color_dict, factor_buffer_dict

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
    ('XL', 'XL', 'extra large squared tex: 1024px', '', 1024),
    ('USER', 'USER', 'extra large squared tex: 1024px', '', 0)
]

size_tex_dict = {item[0]: item[4] for item in size_tex_list}

bitmap_format_list = [
    ('PNG', '.png', 'save texture in .png format', '', 0),
    ('TARGA', '.tga', 'save texture in .tga format', '', 1),
    ('TARGA_RAW', '.tga (raw)', 'save texture in .tga(raw) format', '', 2),
    ('TIFF', '.tiff', 'save texture in .tiff format', '', 3),
    ('BMP', '.bmp', 'save texture in .tiff format', '', 4),
    ('JPEG', '.jpeg', 'save texture in .jpeg format', '', 5),
    ('JPEG2000', '.jp2', 'save texture in .jpeg (2000) format', '', 6),
    ('OPEN_EXR_MULTILAYER', '.exr (multilayer)', 'save texture in .exr (multilayer) format', '', 7),
    ('OPEN_EXR', '.exr', 'save texture in .exr format', '', 8),
]

format_mapping = {
    'TARGA': 'tga',
    'TARGA_RAW': 'tga',
    'JPEG2000': 'jp2',
    'OPEN_EXR_MULTILAYER': 'exr',
    'OPEN_EXR': 'exr',
}



def transfer_to_image(pixels, name, width, height, mode):
    # transfer pixels(data) from Node tree to image viewer
    image = bpy.data.images.get(name)
    if not image:
        image = bpy.data.images.new(name, width, height, alpha=False)
        image.pack
    else:
        image.scale(width, height)
    svIMG.pass_buffer_to_image(mode, image, pixels, width, height)
    image.update_tag()


class SvTextureViewerNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Texture Viewer node
    Tooltip: Generate textures and images from inside Sverchok
    """

    bl_idname = 'SvTextureViewerNode'
    bl_label = 'Texture viewer'
    bl_icon = 'IMAGE'
    sv_icon = 'SV_TEXTURE_VIEWER'
    texture = {}

    def wrapped_update(self, context):
        hide_inputs = not (self.selected_mode == 'USER')
        self.inputs["Width"].hide_safe = hide_inputs
        self.inputs["Height"].hide_safe = hide_inputs
        updateNode(self, context)

    def wrapped_updateNode_(self, context):
        self.activate = False
        updateNode(self, context)

    n_id: StringProperty(default='')
    to_image_viewer: BoolProperty(
        name='Pass', description='Transfer pixels to image viewer',
        default=False, update=wrapped_updateNode_)

    activate: BoolProperty(
        name='Show', description='Activate texture drawing',
        default=True, update=updateNode)

    selected_mode: EnumProperty(
        items=size_tex_list, description="Offers display sizing",
        default="S", update=wrapped_update)

    width_custom_tex: IntProperty(
        min=1, max=1024, default=206, name='Width Tex',
        description="set the custom texture size", update=updateNode)

    height_custom_tex: IntProperty(
        min=1, max=1024, default=124, name='Height Tex',
        description="set the custom texture size", update=updateNode)

    bitmap_format: EnumProperty(
        items=bitmap_format_list,
        description="Offers bitmap saving", default="PNG")

    color_mode: EnumProperty(
        items=gl_color_list, description="Offers color options",
        default="BW", update=updateNode)

    color_mode_save: EnumProperty(
        items=gl_color_list, description="Offers color options",
        default="BW", update=updateNode)

    compression_level: IntProperty(
        min=0, max=100, default=0, name='compression',
        description="set compression level", update=updateNode)

    quality_level: IntProperty(
        min=0, max=100, default=0, name='quality',
        description="set quality level", update=updateNode)

    in_float: FloatProperty(
        min=0.0, max=1.0, default=0.0, name='Float Input',
        description='Input for texture', update=updateNode)

    base_dir: StringProperty(default='/tmp/')
    image_name: StringProperty(default='image_name', description='name (minus filetype)')
    texture_name: StringProperty(
        default='texture',
        description='set name (minus filetype) for exporting to image viewer')
    total_size: IntProperty(default=0)

    properties_to_skip_iojson = ["location_theta"]
    location_theta: FloatProperty(name="location theta")

    @property
    def xy_offset(self):
        a = self.absolute_location
        b = int(self.width) + 20
        return int(a[0] + b), int(a[1])

    @property
    def custom_size(self):
        sockets = self.inputs["Width"], self.inputs["Height"]
        return [s.sv_get(deepcopy=False)[0][0] for s in sockets]

    @property
    def texture_width_height(self):
        #  get the width and height for the texture
        if self.selected_mode == 'USER':
            width, height = self.custom_size
        else:
            size_tex = size_tex_dict.get(self.selected_mode)
            width, height = size_tex, size_tex
        return width, height

    def calculate_total_size(self):
        ''' buffer need adequate size multiplying '''
        width, height = self.texture_width_height
        return width * height * factor_buffer_dict.get(self.color_mode)

    def get_buffer(self):
        data = self.inputs['Float'].sv_get(deepcopy=False)
        self.total_size = self.calculate_total_size()

        texture = bgl.Buffer(bgl.GL_FLOAT, self.total_size, np.resize(data, self.total_size).tolist())
        return texture

    def draw_buttons(self, context, layout):
        c = layout.column()
        c.label(text="Set texture display:")
        row = c.row()
        row.prop(self, "selected_mode", expand=True)

        nrow = c.row()
        nrow.prop(self, 'activate')
        nrow.prop(self, 'to_image_viewer')
        row = layout.row(align=True)
        row.prop(self, 'color_mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        img_format = self.bitmap_format
        callback_to_self = "node.sv_texview_callback"
        directory_select = "node.sv_texview_dirselect"

        layout.label(text="Save texture as a bitmap")

        layout.separator()
        layout.prop(self, "bitmap_format", text='format')
        layout.separator()

        if img_format == 'PNG':
            row = layout.row()
            row.prop(self, 'compression_level', text='set compression')
            layout.separator()
        if img_format in {'JPEG', 'JPEG2000'}:
            row = layout.row()
            row.prop(self, 'quality_level', text='set quality')
            layout.separator()

        row = layout.row(align=True)
        leftside = row.split(factor=0.7)
        leftside.prop(self, 'image_name', text='')
        rightside = leftside.split().row(align=True)
        rightside.operator(callback_to_self, text="Save").fn_name = "save_bitmap"
        rightside.operator(directory_select, text="", icon='FILE_IMAGE').fn_name = "set_dir"
        transfer = layout.column(align=True)
        transfer.separator()
        transfer.label(text="Transfer to image viewer")
        transfer.prop(self, 'texture_name', text='', icon='EXPORT')

    def sv_init(self, context):
        self.width = 180
        inew = self.inputs.new
        inew('SvStringsSocket', "Float").prop_name = 'in_float'

        width_socket = inew('SvStringsSocket', "Width")
        width_socket.prop_name = 'width_custom_tex'
        width_socket.hide_safe = True

        height_socket = inew('SvStringsSocket', "Height")
        height_socket.prop_name = 'height_custom_tex'
        height_socket.hide_safe = True

        self.get_and_set_gl_scale_info()


    def delete_texture(self):
        n_id = node_id(self)
        if n_id in self.texture:
            names = bgl.Buffer(bgl.GL_INT, 1, [self.texture[n_id]])
            bgl.glDeleteTextures(1, names)

    def process(self):
        if not self.inputs['Float'].is_linked:
            return

        n_id = node_id(self)
        self.delete_texture()
        nvBGL2.callback_disable(n_id)

        size_tex = 0
        width = 0
        height = 0

        # why is cMode a sequence like (bool,) ? see uniform_bool(name, seq) in
        # https://docs.blender.org/api/blender2.8/gpu.types.html
        is_multi_channel = self.color_mode in ('RGB', 'RGBA')
        cMode = (is_multi_channel,)

        if self.to_image_viewer:

            mode = self.color_mode
            pixels = np.array(self.inputs['Float'].sv_get(deepcopy=False)).flatten()
            width, height = self.texture_width_height
            resized_np_array = np.resize(pixels, self.calculate_total_size())
            transfer_to_image(resized_np_array, self.texture_name, width, height, mode)

        if self.activate:
            texture = self.get_buffer()
            width, height = self.texture_width_height
            x, y = self.xy_offset
            gl_color_constant = gl_color_dict.get(self.color_mode)


            name = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, name)
            self.texture[n_id] = name[0]
            init_texture(width, height, name[0], texture, gl_color_constant)

            width, height = self.get_dimensions(width, height)
            batch, shader = generate_batch_shader((width, height))

            draw_data = {
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],                
                'mode': 'custom_function',
                'custom_function': simple_screen,
                'loc': get_drawing_location,
                'args': (texture, self.texture[n_id], width, height, batch, shader, cMode)
            }

            nvBGL2.callback_enable(n_id, draw_data)

    def get_preferences(self):
        # supplied with default, forces at least one value :)
        props = get_params({
            'render_scale': 1.0,
            'render_location_xy_multiplier': 1.0})
        return props.render_scale, props.render_location_xy_multiplier

    def get_dimensions(self, width, height):
        """
        this could also return scale for a blf notation in the vacinity of the texture
        """
        scale, multiplier = self.get_preferences()
        self.location_theta = multiplier
        width, height = [width * scale, height * scale]
        return width, height

    def sv_free(self):
        nvBGL2.callback_disable(node_id(self))
        self.delete_texture()

    def sv_copy(self, node):
        # reset n_id on copy
        self.n_id = ''

    def set_dir(self, operator):
        self.base_dir = operator.directory
        print('new base dir:', self.base_dir)
        return {'FINISHED'}

    def push_image_settings(self, scene):
        img_format = self.bitmap_format
        print('img_format is: {0}'.format(img_format))

        img_settings = scene.render.image_settings
        img_settings.quality = self.quality_level
        img_settings.color_depth = '16' if img_format in {'JPEG', 'JPEG2000'} else '8'
        img_settings.compression = self.compression_level
        img_settings.color_mode = self.color_mode
        img_settings.file_format = img_format
        print('settings done!')

    def save_bitmap(self, operator):
        scene = bpy.context.scene
        image_name = self.image_name or 'image_name'
        img_format = self.bitmap_format

        extension = svIMG.get_extension(img_format, format_mapping)
        width, height = self.texture_width_height
        img = svIMG.get_image_by_name(image_name, extension, width, height)
        buf = self.get_buffer()
        svIMG.pass_buffer_to_image(self.color_mode, img, buf, width, height)

        self.push_image_settings(scene)
        desired_path = os.path.join(self.base_dir, self.image_name + extension)
        img.save_render(desired_path, scene)
        print('Bitmap saved!  path is:', desired_path)

    def draw_label(self):
        """ draw the node's header text"""

        text = (self.label or self.name) + " "
        if self.selected_mode == 'USER':
            width, height = self.texture_width_height
            text += f'{width} x {height}'
        else:
            text += str(size_tex_dict.get(self.selected_mode)) + "^2"

        return text


classes = [SvTextureViewerOperator, SvTextureViewerDirSelect, SvTextureViewerNode]
register, unregister = bpy.utils.register_classes_factory(classes)
