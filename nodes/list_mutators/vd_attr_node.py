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
https://gist.github.com/zeffii/06e2b5f6ccda02b2854e004afe039f8f
"""

sock_str = lambda: None
sock_str._enum = "SvStringsSocket"
sock_str._3f = "SvVerticesSocket"
sock_str._4f = "SvColorSocket"
sock_str._i = "SvStringsSocket"
sock_str._b = "SvStringsSocket"

def props(**x):
    prop = lambda: None
    prop.name = x['name']
    prop.kind = x['kind']
    return prop

maximum_spec_vd_dict = dict(
    vector_light=props(name="light direction", kind="3f"),
    vert_color=props(name="points rgba", kind="4f"),
    edge_color=props(name="edge rgba", kind="4f"),
    face_color=props(name="face rgba", kind="4f"),
    display_verts=props(name="display verts", kind="b"),
    display_edges=props(name="display edges", kind="b"),
    display_faces=props(name="display faces", kind="b"),
    selected_draw_mode=props(name="shade mode", kind="enum"),
    draw_gl_wireframe=props(name="wireframe", kind="b"),
    draw_gl_polygonoffset=props(name="fix zfighting", kind="b"),
    point_size=props(name="point size", kind="i"),
    line_width=props(name="line width", kind="i"),
    extended_matrix=props(name="extended matrix", kind="b")
)

get_socket_str = lambda socket_type: getattr(sock_str, '_' + socket_type) 

def property_change(self, context):
    #    self.inputs[socket_name].hide = 
    print(self.index)
    print(self, dir(self))

    # self here is not node, but SvVDMK3Item instance
    # self.process_node(context)

class SvVDMK3Item(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(min=0)
    attr_name: bpy.props.StringProperty() 
    show_socket: bpy.props.BoolProperty(default=False)
    use_default: bpy.props.BoolProperty(default=False, update=property_change)
    default_type: bpy.props.StringProperty()

    default_i: bpy.props.IntProperty(min=0)
    default_b: bpy.props.BoolProperty(default=False)
    default_enum: bpy.props.IntProperty(min=0, default=0)
    default_3f: bpy.props.FloatVectorProperty(
        name='normal', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4)) #, update=updateNode)

    default_4f: bpy.props.FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.5, 1.0, 0.5, 1.0),
        name='color', size=4) #, update=updateNode)


class SvVDMK3ItemList(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout
        
        row.label(text=item.attr_name)
        postfix = item.default_type
        row.prop(item, "default_"+postfix, text="")
        row.prop(item, "show_socket", text="", icon='TRACKING', toggle=True)
        row.prop(item, "use_default", text="", icon='SETTINGS', toggle=True)

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

    property_index: IntProperty(name='index', default=0)
    vd_items_group: bpy.props.CollectionProperty(name="vd attrs", type=SvVDMK3Item)

    def draw_group(self, context, layout):
        if self.vd_items_group:
            layout.template_list("SvVDMK3ItemList", "", self, "vd_items_group", self, "property_index")

    def vd_init_sockets(self, context):
        self.outputs.new("SvStringsSocket", name="attrs")
        inew = self.inputs.new
        for prop_name, socket in maximum_spec_vd_dict.items():
            inew(get_socket_str(socket.kind), socket.name).hide = True
  
    def vd_init_uilayout_data(self, context):
        for key, value in maximum_spec_vd_dict.items():
            item = self.vd_items_group.add()
            item.attr_name = key
            item.show_socket = False
            item.default_type = value.kind

    def sv_init(self, context):
        self.vd_init_sockets(context)
        self.vd_init_uilayout_data(context)

    def draw_buttons(self, context, layout):
        ...
        # maybe offer to show here..

    def draw_buttons_ext(self, context, layout):
        self.draw_group(context, layout)


    def process(self):
        print('here')

        testing_default = {'activate': True, 'display_verts': False, 'draw_gl_polygonoffset': True}
        self.outputs['attrs'].sv_set([testing_default])


classes = [SvVDMK3Item, SvVDMK3ItemList, SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)