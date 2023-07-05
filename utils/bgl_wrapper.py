# sverchok/utils/bgl_wrapper.py

import bpy

if bpy.app.version >= (3, 5, 0):
    import gpu


    BLEND = "ALPHA"
    GL_FRONT_AND_BACK = None
    GL_LINE = None
    GL_POLYGON_OFFSET_FILL = "GL_POLYGON_OFFSET_FILL"
    glLineWidth = gpu.state.line_width_set 
    glPointSize = gpu.state.point_size_set

    def glEnable(param):
        if param == "GL_POLYGON_OFFSET_FILL":
            pass
        elif param == "ALPHA":
            return gpu.state.blend_set(param)
        else:
            print(f"glEnable unhandled {param=}")


    def glPolygonOffset(*params): pass
    def glPolygonMode(*params): pass

else:
    # we use only a finite subset of the module
    import bgl
    from bgl import glPolygonMode, glEnable, glPolygonOffset
    from bgl import BLEND, GL_FRONT_AND_BACK, GL_LINE, GL_POLYGON_OFFSET_FILL
