# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
# import mathutils
# from mathutils import Vector
# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

sock_str = lambda: None
sock_str._enum = "SvStringsSocket"
sock_str._3f = "SvVerticesSocket"
sock_str._4f = "SvColorSocket"
sock_str._i = "SvStringsSocket"
sock_str._b = "SvStringsSocket"

maximum_spec_vd_dict = dict(
    vector_light=["light direction", "3f"],
    vert_color=["points rgba", "4f"],
    edge_color=["edge rgba", "4f"],
    face_color=["face rgba", "4f"],
    display_verts=["display verts", "b"],
    display_edges=["display edges", "b"],
    display_faces=["display faces", "b"],
    selected_draw_mode=["shade mode", "enum"],
    draw_gl_wireframe=["wireframe", "b"],
    draw_gl_polygonoffset=["fix zfighting", "b"],
    point_size=["point size", "i"],
    line_width=["line width", "i"],
    extended_matrix=["extended matrix", "b"]
)

get_socket_str = lambda socket_type: getattr(sock_str, '_' + socket_type) 

"""
items:
    attr_name | show_socket | use_default | default 
                                            (default type, default_property)

https://gist.github.com/zeffii/06e2b5f6ccda02b2854e004afe039f8f

"""



class SvVDAttrsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: vd attr 
    Tooltip: Attribute Node for Viewer Draw Experimental
    
    Allows access to VD Experimental's attributes which control how the
    node draws faces/edges. It can also switch off the node.
    """

    bl_idname = 'SvVDAttrsNode'
    bl_label = 'VD Attributes'
    bl_icon = 'MOD_HUE_SATURATION'

    def vd_init_sockets(self, context):
        self.outputs.new("SvStringsSocket", name="attrs")
        inew = self.inputs.new
        for prop_name, (socket_name, socket_type) in maximum_spec_vd_dict.items():
            inew(get_socket_str(socket_type), socket_name).hide = True
  
    def vd_init_uilayout_data(self, context):
        ...
 

    def sv_init(self, context):
        self.vd_init_sockets(context)
        self.vd_init_uilayout_data(context)

    def draw_buttons(self, context, layout):
        ...
        # maybe offer to show here..

    def draw_buttons_ext(self, context, layout):
        ...
        ...
        ...

    def process(self):

        testing_default = {'activate': True, 'display_verts': False, 'draw_gl_polygonoffset': True}
        self.outputs['attrs'].sv_set([testing_default])


classes = [SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)