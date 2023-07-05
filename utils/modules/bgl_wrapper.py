# sverchok/utils/bgl_wrapper.py

"""
The bgl module is deprecated From Blender 3.5 onwards, this means we must use the gpu module to 
achieve any/all features formerly provided by bgl. This wrapper aims to keep the code changes to
a minimum while supporting the old bgl code where possbile. The module is also a test to see if
we can achieve some type of feature parity between the versions.


"""


import bpy

if bpy.app.version >= (3, 5, 0):

    import gpu

    GL_BLEND = "ALPHA"
    GL_FRONT_AND_BACK = None
    GL_LINE = None
    GL_POLYGON_OFFSET_FILL = "GL_POLYGON_OFFSET_FILL"
    glLineWidth = gpu.state.line_width_set 
    glPointSize = gpu.state.point_size_set


    def glEnable(param):
        if param == "GL_POLYGON_OFFSET_FILL":
            pass
        elif param == GL_BLEND:
            gpu.state.blend_set(param)
        else:
            print(f"glEnable unhandled {param=}")

    def glDisable(param):
        if param == GL_BLEND:
            gpu.state.blend_set("NONE")
        else:
            print(f"glDisable unhandled {param=}")

    def glPolygonOffset(*params): pass
    def glPolygonMode(*params): pass

else:
    # we use only a finite subset of the module
    import bgl
    from bgl import glPolygonMode, glEnable, glDisable, glPolygonOffset
    from bgl import GL_BLEND, GL_FRONT_AND_BACK, GL_LINE, GL_POLYGON_OFFSET_FILL, GL_FLOAT, GL_INT
    from bgl import Buffer
