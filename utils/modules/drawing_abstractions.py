# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


# from sverchok.utils.modules.drawing_abstractions import drawing 

import bpy
import gpu
import blf
from typing import NamedTuple


class shading_3d(NamedTuple):
    if bpy.app.version <= (3, 4):
        UNIFORM_COLOR = "3D_UNIFORM_COLOR"
        SMOOTH_COLOR = "3D_SMOOTH_COLOR"
    else:
        UNIFORM_COLOR = "UNIFORM_COLOR"
        SMOOTH_COLOR = "SMOOTH_COLOR"

class shading_2d(NamedTuple):
    if bpy.app.version <= (3, 4):
        UNIFORM_COLOR = "2D_UNIFORM_COLOR"
        SMOOTH_COLOR = "2D_SMOOTH_COLOR"
    else:
        UNIFORM_COLOR = "UNIFORM_COLOR"
        SMOOTH_COLOR = "SMOOTH_COLOR"


"""
These classes encapsulate any and all sets of bgl instructions that Sverchok used prior to
the deprecation of the bgl module. It's not clear yet if the gpu module will achieve parity,
some Nodes might need considerable revision - here we attempt to make at least some viz nodes
draw in a useful way in B3.5 and up. Certain nodes that use elaborate buffer and texture 
configurations will need additional attention and might even not reach parity for some time, 
or indeed at all. Replacement techniques will be investigated. 

"""

if bpy.app.version >= (3, 5, 0):

    def placeholder_function(*params):
        return

    class Drawing:

        set_wireframe_line = placeholder_function

        def set_wireframe_fill(self):
            gpu.state.face_culling_set("BACK")
            gpu.state.front_facing_set(False)

        set_line_width = gpu.state.line_width_set
        reset_line_width = lambda self: gpu.state.line_width_set(1)
        set_point_size = gpu.state.point_size_set
        reset_point_size = lambda self: gpu.state.point_size_set(1)
        enable_polygon_offset_fill = lambda self: gpu.state.face_culling_set("BACK")
        disable_polygon_offset_fill = placeholder_function
        set_polygon_offset_amounts = placeholder_function

        enable_blendmode = lambda self: gpu.state.blend_set("ALPHA")
        disable_blendmode = lambda self: gpu.state.blend_set("NONE")
        enable_depth_test = lambda self: gpu.state.depth_test_set("LESS_EQUAL")
        disable_depth_test = lambda self: gpu.state.depth_test_set("NONE")

        new_buffer_texture = placeholder_function
        get_buffer = placeholder_function
        bind_texture_2d = placeholder_function
        init_complex_texture = placeholder_function
        generate_textures = placeholder_function
        delete_texture = placeholder_function

        blf_size = lambda self, font_id, height, dpi: blf.size(font_id, height)


else:

    import bgl

    class Drawing:

        blf_size = blf.size

        set_wireframe_line = lambda self: bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_LINE)
        set_wireframe_fill = lambda self: bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_FILL)
        set_line_width = bgl.glLineWidth
        reset_line_width = lambda self: bgl.glLineWidth(1)
        set_point_size = bgl.glPointSize
        reset_point_size = lambda self: bgl.glPointSize(1)
        enable_polygon_offset_fill = lambda self: bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
        disable_polygon_offset_fill = lambda self: bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)
        set_polygon_offset_amounts = lambda self: bgl.glPolygonOffset(1.0, 1.0)
        
        enable_blendmode = lambda self: bgl.glEnable(bgl.GL_BLEND)
        disable_blendmode = lambda self: bgl.glDisable(bgl.GL_BLEND)
        enable_depth_test = lambda self: bgl.glEnable(bgl.GL_DEPTH_TEST)
        disable_depth_test = lambda self: bgl.glDisable(bgl.GL_DEPTH_TEST)
        disable_texture_2d = lambda self: bgl.glDisable(bgl.GL_TEXTURE_2D)

        new_buffer_texture = lambda self: bgl.Buffer(bgl.GL_INT, 1)
        get_buffer = lambda self, indexed_buffer: bgl.Buffer(bgl.GL_INT, 1, indexed_buffer)
        new_buffer_texture_sized = lambda self, size, data: bgl.Buffer(bgl.GL_FLOAT, size, data)
        bind_texture_2d = lambda self, texture: bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture)
        delete_texture = lambda self, texture: bgl.glDeleteTextures(1, texture)

        def init_image_from_texture(self, width, height, texname, texture, format):

            if format in {bgl.GL_RGBA, bgl.GL_RGB, bgl.GL_RED}:
                ...
            else:
                format = {'BW': bgl.GL_RED, 'RGB': bgl.GL_RGB, 'RGBA': bgl.GL_RGBA}.get(format)

            bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT, 1)
            bgl.glEnable(bgl.GL_TEXTURE_2D)
            bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)
            bgl.glActiveTexture(bgl.GL_TEXTURE0)
            bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
            bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
            bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
            bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
            bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, format, width, height, 0, format, bgl.GL_FLOAT, texture)

        def init_complex_texture(self, width, height, texname, data, format):
            texture = self.new_buffer_texture_sized(bgl.GL_FLOAT, data.size, data.tolist())
            self.init_image_from_texture(width, height, texname, texture, format)
            

        generate_textures = lambda self, name: bgl.glGenTextures(1, name)  # returns an indexable item


drawing = Drawing()
