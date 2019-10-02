# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import (
    FloatProperty, BoolProperty, StringProperty, EnumProperty,
    FloatVectorProperty, IntProperty, CollectionProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_5

sock_str = lambda: None
sock_str._enum = "SvStringsSocket"
sock_str._3f = "SvVerticesSocket"
sock_str._4f = "SvColorSocket"
sock_str._i = "SvStringsSocket"
sock_str._b = "SvStringsSocket"

def props(**x):
    prop = lambda: None
    _ = [setattr(prop, k, v) for k, v in x.items()]
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

def property_change(self, context, changed_attr):
    """ self here is not node, but SvVDMK3Item instance """

    # seems link to the node is lost, but not the nodetree
    # self.inputs[socket_name].hide = 
    print(self.attr_name, '---', changed_attr)
    print('nodetree:', self.id_data)

class SvVDMK3Item(bpy.types.PropertyGroup):
    attr_name: StringProperty() 
    show_socket: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'show_socket'))
    use_default: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'use_default'))
    origin_node_name: StringProperty()

class SvVDMK3Properties(bpy.types.PropertyGroup):
    
    # these props should be totally possible to obtain from 
    # SvVDExperimental.__annotations__  , and drop any update=function
    # for now i'm reduplicating.

    activate: BoolProperty(name='Show', description='Activate', default=True)

    vert_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.8, 0.8, 0.8, 1.0),
        name='vert color', size=4)

    edge_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.5, 1.0, 0.5, 1.0),
        name='edge color', size=4)

    face_color: FloatVectorProperty(
        subtype='COLOR', min=0, max=1, default=(0.14, 0.54, 0.81, 1.0),
        name='face color', size=4)

    vector_light: FloatVectorProperty(
        name='vector light', subtype='DIRECTION', min=0, max=1, size=3,
        default=(0.2, 0.6, 0.4))

    extended_matrix: BoolProperty(
        default=False, description='Allows mesh.transform(matrix) operation, quite fast!')

    point_size: FloatProperty(description="glPointSize( GLfloat size)", default=4.0, min=1.0, max=15.0)
    line_width: IntProperty(description="glLineWidth( GLfloat width)", default=1, min=1, max=5)

    display_verts: BoolProperty(default=True, name="display verts")
    display_edges: BoolProperty(default=True, name="display edges")
    display_faces: BoolProperty(default=True, name="display faces")
    draw_gl_wireframe: BoolProperty(default=False, name="draw gl wireframe")
    draw_gl_polygonoffset: BoolProperty(default=False, name="draw gl polygon offset")

    selected_draw_mode: EnumProperty(
        items=enum_item_5(["flat", "facet", "smooth", "fragment"], ['SNAP_VOLUME', 'ALIASED', 'ANTIALIASED', 'SCRIPTPLUGINS']),
        description="pick how the node will draw faces",
        default="flat")    

class SV_UL_VDMK3ItemList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        # is there a nicer way to do this?
        # can be use  .active_node ?
        node = context.space_data.edit_tree.nodes[item.origin_node_name]
        
        layout.label(text=item.attr_name)
        layout.prop(node.vd_items_props[0], item.attr_name, text='') 
        layout.prop(item, "show_socket", text="", icon='TRACKING', toggle=True)
        layout.prop(item, "use_default", text="", icon='SETTINGS', toggle=True)

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
    vd_items_group: CollectionProperty(name="vd attrs", type=SvVDMK3Item)
    vd_items_props: CollectionProperty(name="vd props", type=SvVDMK3Properties)

    def draw_group(self, context, layout):
        if self.vd_items_group:
            layout.template_list("SV_UL_VDMK3ItemList", "", self, "vd_items_group", self, "property_index")

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
            item.origin_node_name = self.name

        self.vd_items_props.add()

    def sv_init(self, context):
        self.vd_init_sockets(context)
        self.vd_init_uilayout_data(context)

    def draw_buttons(self, context, layout):
        ...

    def draw_buttons_ext(self, context, layout):
        self.draw_group(context, layout)

    def process(self):  
        #if self.vd_items_group:
        #    if not self.vd_items_group.item[0].origin_node_name == self.name:
        #        for item in self.vd_items_group:
        #            item.origin_node_name = self.name

        testing_default = {'activate': True, 'display_verts': False, 'draw_gl_polygonoffset': True}
        self.outputs['attrs'].sv_set([testing_default])


classes = [SvVDMK3Item, SvVDMK3Properties, SV_UL_VDMK3ItemList, SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)