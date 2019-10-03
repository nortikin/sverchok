# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_5
from sverchok.nodes.viz.vd_draw_experimental import SvVDExperimental

sock_str = {
    'enum': "SvStringsSocket",
    '3f': "SvVerticesSocket",
    '4f': "SvColorSocket",
    'i': "SvStringsSocket",
    'b': "SvStringsSocket"
}

def props(**x):
    prop = lambda: None
    _ = [setattr(prop, k, v) for k, v in x.items()]
    return prop

# this dict (ordered by default as per python 3.7 ?..) determines the order of sockets
maximum_spec_vd_dict = dict(
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
    extended_matrix=props(name="extended matrix", kind="b"),
    vector_light=props(name="light direction", kind="3f")
)

def property_change(item, context, changed_attr):
    # prior to node initialization this function will be called, but will generate errors until
    # the vd mk 3 item group is also fully initialized.
    if not item.origin_node_name:
        return

    # seems link to the node is lost, but not the nodetree
    ng = item.id_data
    node = ng.nodes[item.origin_node_name]
    socket_name = maximum_spec_vd_dict[item.attr_name].name
    if changed_attr == 'show_socket':
        node.inputs[socket_name].hide_safe = not getattr(item, changed_attr) 

class SvVDMK3Item(bpy.types.PropertyGroup):
    attr_name: StringProperty() 
    show_socket: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'show_socket'))
    use_default: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'use_default'))
    origin_node_name: StringProperty()

class SvVDMK3Properties(bpy.types.PropertyGroup):
    # this populates a property-group using VDExperimental.__annotations__ as the source -
    __annotations__ = {}
    for key, v in maximum_spec_vd_dict.items():
        prop_func, kw_args = SvVDExperimental.__annotations__[key]
        kw_args.pop('update', None)
        __annotations__[key] = prop_func(**kw_args)

class SV_UL_VDMK3ItemList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        
        # is there a nicer way to do this? can we use  .active_node ?
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
            inew(socket_types[socket.kind], socket.name).hide = True
  
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

    def ensure_correct_origin_node_name(self):
        if self.vd_items_group:
           if not self.vd_items_group.item[0].origin_node_name == self.name:
               for item in self.vd_items_group:
                   item.origin_node_name = self.name

    @property
    def attrdict_from_state(self):
        testing_default = {'activate': True, 'display_verts': False, 'draw_gl_polygonoffset': True}
        return testing_default

    def process(self):
        self.ensure_correct_origin_node_name()
        self.outputs['attrs'].sv_set([self.attrdict_from_state])


classes = [SvVDMK3Item, SvVDMK3Properties, SV_UL_VDMK3ItemList, SvVDAttrsNode]
register, unregister = bpy.utils.register_classes_factory(classes)