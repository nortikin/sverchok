# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import os
import numpy as np
import bgl
import gpu
import bpy
from bpy.props import EnumProperty, StringProperty, IntProperty, PointerProperty, FloatProperty

from sverchok.settings import get_params
from sverchok.data_structure import updateNode, node_id
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.ui import bgl_callback_nodeview as nvBGL2

from sverchok.utils.sv_texture_utils import generate_batch_shader
from sverchok.utils.sv_texture_utils import simple_screen, init_texture, get_drawing_location
from sverchok.utils.sv_texture_utils import gl_color_list, gl_color_dict, factor_buffer_dict


out_modes = [
    ('image_editor', 'UV\image editor', 'insert values into image editor (only RGBA mode!)', '', 0),
    ('bgl', 'bgl', 'create texture inside nodetree', '', 1),
]

class SvTextureViewerNodeLite(bpy.types.Node, SverchCustomTreeNode):
    '''Texture Viewer node Lite'''
    bl_idname = 'SvTextureViewerNodeLite'
    bl_label = 'Texture viewer lite'
    bl_icon = 'IMAGE'
    sv_icon = 'SV_TEXTURE_VIEWER_LITE'
    texture = {}

    def pointer_update(self, context):
        if self.image_pointer:
            self.image = self.image_pointer.name
        else:
            self.image = ""

    # image = direct use depreciated, retained only to allow loading old blenders
    image: StringProperty(default='') #, update=updateNode)
    image_pointer: PointerProperty(type=bpy.types.Image, poll=lambda s, o: True, update=pointer_update)

    width_custom_tex: IntProperty(
        min=1, max=2024, default=206, name='Width',
        description="set the custom texture size", update=updateNode)

    height_custom_tex: IntProperty(
        min=1, max=2024, default=124, name='Height',
        description="set the custom texture size", update=updateNode)

    color_mode: EnumProperty(
        items=gl_color_list, description="Offers color options",
        default="BW", update=updateNode)

    output_mode: EnumProperty(
        items=out_modes, description="how to output values",
        default="bgl", update=updateNode)

    location_theta: FloatProperty(name="location theta")

    @property
    def xy_offset(self):
        a = self.absolute_location
        b = int(self.width) + 20
        return int(a[0] + b), int(a[1])

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'output_mode', expand=True)
        col = layout.column(align=True)
        if not self.output_mode == 'bgl':
            col.prop_search(self, 'image_pointer', bpy.data, "images", text="")
        else:
            row = layout.row(align=True)
            row.prop(self, 'color_mode', expand=True)
            row2 = col.row(align=True)
            # row2.label(text='Dims Tex')
            row2.prop(self, 'width_custom_tex')
            row2.prop(self, 'height_custom_tex')

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('SvStringsSocket', "pixel value")
        self.get_and_set_gl_scale_info()

    def delete_texture(self):
        n_id = node_id(self)
        if n_id in self.texture:
            names = bgl.Buffer(bgl.GL_INT, 1, [self.texture[n_id]])
            bgl.glDeleteTextures(1, names)

    def process(self):
        n_id = node_id(self)
        self.delete_texture()
        nvBGL2.callback_disable(n_id)

        # why is cMode a sequence like (bool,) ? see uniform_bool(name, seq) in
        # https://docs.blender.org/api/blender2.8/gpu.types.html
        gl_color_constant = gl_color_dict.get(self.color_mode)
        is_multi_channel = self.color_mode in ('RGB', 'RGBA')
        cMode = (is_multi_channel,)

        if self.output_mode == 'bgl':

            # x, y = self.xy_offset
            width, height, colm = self.width_custom_tex, self.height_custom_tex, self.color_mode
            total_size = width * height * factor_buffer_dict.get(colm)
            texture = bgl.Buffer(bgl.GL_FLOAT, total_size, np.resize(self.inputs[0].sv_get(), total_size).tolist())

            name = bgl.Buffer(bgl.GL_INT, 1)
            bgl.glGenTextures(1, name)
            self.texture[n_id] = name[0]
            init_texture(width, height, name[0], texture, gl_color_constant)

            width, height = self.get_dimensions(width, height)
            batch, shader = generate_batch_shader((width, height))

            draw_data = {
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'mode': 'custom_function_context',
                'custom_function': simple_screen,
                'loc': get_drawing_location,
                'args': (texture, self.texture[n_id], width, height, batch, shader, cMode)
            }

            nvBGL2.callback_enable(n_id, draw_data)

        else:

            Im = bpy.data.images[self.image]
            Im.pixels = np.resize(self.inputs[0].sv_get(), len(Im.pixels))

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

    def set_pointer_from_filename(self):
        """ this function upgrades older versions of ProfileMK3 to the version that has self.file_pointer """
        if hasattr(self, "image_pointer") and not self.image_pointer:
            image = self.get_bpy_data_from_name(self.image, bpy.data.images)
            if image:
                self.image_pointer = image

classes = [SvTextureViewerNodeLite,]
register, unregister = bpy.utils.register_classes_factory(classes)
