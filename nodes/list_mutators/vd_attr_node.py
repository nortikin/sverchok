# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty, 
    FloatVectorProperty, IntProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

"""
items:
    attr_name | show_socket | use_default | default 
                                            (default type, default_property)

https://gist.github.com/zeffii/06e2b5f6ccda02b2854e004afe039f8f

"""

sock_str = lambda: None
sock_str._enum = "SvStringsSocket"
sock_str._3f = "SvVerticesSocket"
sock_str._4f = "SvColorSocket"
sock_str._i = "SvStringsSocket"
sock_str._b = "SvStringsSocket"

maximum_spec_vd_dict = dict(
    vector_light=dict(name="light direction", kind="3f"),
    vert_color=dict(name="points rgba", kind="4f"),
    edge_color=dict(name="edge rgba", kind="4f"),
    face_color=dict(name="face rgba", kind="4f"),
    display_verts=dict(name="display verts", kind="b"),
    display_edges=dict(name="display edges", kind="b"),
    display_faces=dict(name="display faces", kind="b"),
    selected_draw_mode=dict(name="shade mode", kind="enum"),
    draw_gl_wireframe=dict(name="wireframe", kind="b"),
    draw_gl_polygonoffset=dict(name="fix zfighting", kind="b"),
    point_size=dict(name="point size", kind="i"),
    line_width=dict(name="line width", kind="i"),
    extended_matrix=dict(name="extended matrix", kind="b")
)

get_socket_str = lambda socket_type: getattr(sock_str, '_' + socket_type) 

class SvVDMK3Item(bpy.types.PropertyGroup):
    attr_name = bpy.props.StringProperty() 
    show_socket = bpy.props.BoolProperty(default=False)
    use_default = bpy.props.BoolProperty(default=False)
    default_type = bpy.props.StringProperty()
    default_3f =  bpy.props.FloatVectorProperty(
        name='normal', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4)) #, update=updateNode)
    default_4f = bpy.props.FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.5, 1.0, 0.5, 1.0),
        name='color', size=4) #, update=updateNode)
    default_i = bpy.props.IntProperty(min=0)
    default_b = bpy.props.BoolProperty(default=False)
    default_enum = bpy.props.IntProperty(min=0, default=0)


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

    vd_items_group: bpy.props.CollectionProperty(name="vd attrs", type=SvVDMK3Item)

    def vd_init_sockets(self, context):
        self.outputs.new("SvStringsSocket", name="attrs")
        inew = self.inputs.new
        for prop_name, socket in maximum_spec_vd_dict.items():
            inew(get_socket_str(socket.kind), socket.name).hide = True
  
    def vd_init_uilayout_data(self, context):
        for key, value in maximum_spec_vd_dict.items()
            item = self.vd_items_group.new()
            item.attr_name = key
            item.show_socket = False
            item.default_type = value[1]


    def sv_init(self, context):
        self.vd_init_sockets(context)
        self.vd_init_uilayout_data(context)

    def draw_buttons(self, context, layout):
        ...
        # maybe offer to show here..

    def draw_buttons_ext(self, context, layout):
        self.draw_group(context, layout)

    def draw_group(self, context, layout):
        box = layout.box()
        for item in self.vd_items_group:
            row = box.row()
            row.label(text=item.attr_name)
            row.prop(item, "show_socket", text="Show Socket")
            row.prop(item, "use_default", text="Use Default")

    def process(self):

        testing_default = {'activate': True, 'display_verts': False, 'draw_gl_polygonoffset': True}
        self.outputs['attrs'].sv_set([testing_default])


classes = [SvVDMK3Item, SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)