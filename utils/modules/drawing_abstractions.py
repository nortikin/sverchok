import bpy

shading_3d = lambda: None

if bpy.app.version <= (3, 4):
    shading_3d.UNIFORM_COLOR = "3D_UNIFORM_COLOR"
    shading_3d.SMOOTH_COLOR = "3D_SMOOTH_COLOR"
else:
    shading_3d.UNIFORM_COLOR = "UNIFORM_COLOR"
    shading_3d.SMOOTH_COLOR = "SMOOTH_COLOR"


drawing = lambda: None

if bpy.app.version >= (3, 5, 0):
    drawing.set_wireframe_line = pass
    drawing.set_wireframe_fill = pass
    drawing.set_line_width = gpu.state.line_width_set
    drawing.reset_line_width = lambda: gpu.state.line_width_set(1)
    drawing.set_point_size = gpu.state.point_size_set
    drawing.reset_point_size = lambda: gpu.state.point_size_set(1)
    drawing.enable_polygon_offset_fill = pass
    drawing.disable_polygon_offset_fill = pass
    drawing.set_polygon_offset_amounts = pass

    drawing.enable_blendmode = pass
    drawing.disable_blendmode = pass
    drawing.enable_depth_test = pass
    drawing.disable_depth_test = pass

    drawing.new_buffer_texture = pass
    drawing.get_buffer = pass
    drawing.bind_texture_2d = pass
    drawing.init_complex_texture = pass
    drawing.generate_textures = pass
    drawing.delete_texture = pass
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
    drawing.enable_depth_test = lambda: bgl.glEnable(bgl.GL_DEPTH_TEST)
    drawing.disable_depth_test = lambda: bgl.glDisable(bgl.GL_DEPTH_TEST)

    drawing.new_buffer_texture = lambda: bgl.Buffer(bgl.GL_INT, 1)
    drawing.get_buffer = lambda indexed_buffer: bgl.Buffer(bgl.GL_INT, 1, indexed_buffer)
    drawing.new_buffer_texture_sized = lambda size, data: bgl.Buffer(bgl.GL_FLOAT, size, data)
    drawing.bind_texture_2d = lambda texture: bgl.glBindTexture(bgl.GL_TEXTURE_2D, texture)
    drawing.delete_texture = lambda texture: bgl.glDeleteTextures(1, texture)

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

