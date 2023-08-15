import bpy

if bpy.app.version >= (3, 5, 0):
    UNIFORM_COLOR = "UNIFORM_COLOR"
    SMOOTH_COLOR = "SMOOTH_COLOR"
else:
    UNIFORM_COLOR = "3D_UNIFORM_COLOR"
    SMOOTH_COLOR = "3D_SMOOTH_COLOR"


drawing = lambda: None


if bpy.app.version >= (3, 5, 0):
    drawing.set_wireframe_line = pass
    drawing.set_wireframe_fill = pass
    drawing.set_line_width = pass
    drawing.reset_line_width = pass
    drawing.set_point_size = pass
    drawing.reset_point_size = pass
    drawing.enable_polygon_offset_fill = pass
    drawing.disable_polygon_offset_fill = pass
    drawing.set_polygon_offset_amounts = pass
    drawing.enable_blendmode = pass 
    drawing.disable_blendmode = pass
    drawing.new_buffer_texture = pass
    drawing.bind_texture_2d = pass
    drawing.init_complex_texture = pass
    drawing.generate_textures = pass

else:
    # from sverchok.utils.modules.drawing_abstractions import drawing 

    import bgl
    drawing.set_wireframe_line = lambda: bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_LINE)
    drawing.set_wireframe_fill = lambda: bgl.glPolygonMode(bgl.GL_FRONT_AND_BACK, bgl.GL_FILL)
    drawing.set_line_width = bgl.glLineWidth
    drawing.reset_line_width = lambda: bgl.glLineWidth(1)
    drawing.set_point_size = bgl.glPointSize
    drawing.reset_point_size = lambda: bgl.glPointSize(1)
    drawing.enable_polygon_offset_fill = lambda: bgl.glEnable(bgl.GL_POLYGON_OFFSET_FILL)
    drawing.disable_polygon_offset_fill = lambda: bgl.glDisable(bgl.GL_POLYGON_OFFSET_FILL)
    drawing.set_polygon_offset_amounts = lambda: bgl.glPolygonOffset(1.0, 1.0)
    drawing.enable_blendmode = lambda: bgl.glEnable(bgl.GL_BLEND)
    drawing.disable_blendmode = lambda: bgl.glDisable(bgl.GL_BLEND)
    drawing.new_buffer_texture = lambda: bgl.Buffer(bgl.GL_INT, 1)
    drawing.new_buffer_texture_sized = lambda size, data: bgl.Buffer(bgl.GL_FLOAT, size, data)
    drawing.bind_texture_2d = lambda texture: bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture)

    def initialize_complex_texture(width, height, texname, texture, data, format):
        if format == 'RGBA':
            format = bgl.GL_RGBA
        texture = drawing.new_buffer_texture_sized(bgl.GL_FLOAT, data.size, data.tolist())
        bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT, 1)
        bgl.glEnable(bgl.GL_TEXTURE_2D)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)
        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
        bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)
        bgl.glTexImage2D(bgl.GL_TEXTURE_2D, 0, format, width, height, 0, format, bgl.GL_FLOAT, texture)        

    drawing.init_complex_texture = initialize_complex_texture
    drawing.generate_textures = lambda name: bgl.glGenTextures(1, name)  # returns an indexable item

