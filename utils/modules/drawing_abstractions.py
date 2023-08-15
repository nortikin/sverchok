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
else:
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