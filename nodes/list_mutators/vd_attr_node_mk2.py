# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import json
import copy

import bpy
from bpy.props import BoolProperty, StringProperty, IntProperty, CollectionProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_5
from sverchok.nodes.viz.viewer_3d import SvViewerDrawMk4


sock_str = {
    'enum': "SvStringsSocket",
    '3f': "SvVerticesSocket",
    '4f': "SvColorSocket",
    'i': "SvStringsSocket",
    'b': "SvStringsSocket"
}


socket_colors = {
    "SvStringsSocket": (0.6, 1.0, 0.6, 1.0),
    "SvVerticesSocket": (0.9, 0.6, 0.2, 1.0),
    "SvColorSocket": (0.9, 0.8, 0.0, 1.0),
}


def props(**x):
    prop = lambda: None
    _ = [setattr(prop, k, v) for k, v in x.items()]
    return prop

# this dict (ordered by default as per python 3.7 ?..) determines the order of sockets
maximum_spec_vd_dict = dict(
    activate=props(name="activate", kind="b"),
    display_verts=props(name="display verts", kind="b"),
    display_edges=props(name="display edges", kind="b"),
    display_faces=props(name="display faces", kind="b"),
    color_per_point=props(name="Color per point", kind="b"),
    color_per_edge=props(name="Color per edge", kind="b"),
    color_per_polygon=props(name="Color per face", kind="b"),
    vector_random_colors=props(name="Random Vertices Color", kind="b"),
    random_seed=props(name="Random Seed", kind="i"),
    edges_use_vertex_color=props(name="Edges Vertex Color", kind="b"),
    polygon_use_vertex_color=props(name="Polys Vertex Color", kind="b"),
    selected_draw_mode=props(name="shade mode", kind="enum"),
    draw_gl_wireframe=props(name="wireframe", kind="b"),
    draw_gl_polygonoffset=props(name="fix zfighting", kind="b"),
    point_size=props(name="point size", kind="i"),
    line_width=props(name="edge width", kind="i"),
    vector_light=props(name="light direction", kind="3f"),
    extended_matrix=props(name="extended matrix", kind="b"),
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

class SvVDMK4Item(bpy.types.PropertyGroup):
    attr_name: StringProperty(options={'SKIP_SAVE'})
    show_socket: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'show_socket'))
    use_default: BoolProperty(default=False, update=lambda s, c: property_change(s, c, 'use_default'))
    origin_node_name: StringProperty(options={'SKIP_SAVE'})

class SvVDMK4Properties(bpy.types.PropertyGroup):
    # this populates a property-group using VDExperimental.__annotations__ as the source -
    __annotations__ = {}
    for key, v in maximum_spec_vd_dict.items():
        prop_func, kw_args = SvViewerDrawMk4.__annotations__[key]
        copy_kw_args = copy.deepcopy(kw_args)
        copy_kw_args.pop('update', None)
        __annotations__[key] = prop_func(**copy_kw_args)

class SV_UL_VDMK4ItemList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        # is there a nicer way to do this? can we use  .active_node ?
        node = context.space_data.edit_tree.nodes[item.origin_node_name]

        attr_name = item.attr_name
        socket_string_name = sock_str[maximum_spec_vd_dict[attr_name].kind]
        layout.template_node_socket(color=socket_colors[socket_string_name])
        layout.prop(item, "show_socket", text="", icon='TRACKING', toggle=True)
        layout.prop(item, "use_default", text="", icon='SETTINGS', toggle=True)
        layout.label(text=attr_name)
        layout.prop(node.vd_items_props_mk2[0], attr_name, text='')

class SvVDAttrsNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: vd attr
    Tooltip: Attribute Node for Viewer Draw Experimental

    Allows access to VD Experimental's attributes which control how the
    node draws faces/edges. It can also switch off the node.
    """
    bl_idname = 'SvVDAttrsNodeMk2'
    bl_label = 'VD Attributes'
    bl_icon = 'MOD_HUE_SATURATION'

    property_index: IntProperty(name='index', default=0)
    vd_items_group_mk2: CollectionProperty(name="vd attrs", type=SvVDMK4Item)
    vd_items_props_mk2: CollectionProperty(name="vd props", type=SvVDMK4Properties)

    def draw_group(self, context, layout):
        if self.vd_items_group_mk2:
            layout.template_list("SV_UL_VDMK4ItemList", "", self, "vd_items_group_mk2", self, "property_index")

    def vd_init_sockets(self, context):
        self.outputs.new("SvStringsSocket", name="attrs")
        inew = self.inputs.new
        for prop_name, socket in maximum_spec_vd_dict.items():
            socket = inew(sock_str[socket.kind], socket.name)
            socket.hide = True
            if prop_name == 'vector_light':
                socket.quick_link_to_node = "GenVectorsNode"

    def vd_init_uilayout_data(self, context):
        for key, value in maximum_spec_vd_dict.items():
            item = self.vd_items_group_mk2.add()
            item.attr_name = key
            item.show_socket = False
            item.origin_node_name = self.name

        self.vd_items_props_mk2.add()

    def sv_init(self, context):
        self.vd_init_sockets(context)
        self.vd_init_uilayout_data(context)

    def draw_buttons(self, context, layout):
        layout.prop(context.space_data, "show_region_ui", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_group(context, layout)

    def ensure_correct_origin_node_name(self):
        if self.vd_items_group_mk2:
            if not self.vd_items_group_mk2[0].origin_node_name == self.name:
                for item in self.vd_items_group_mk2:
                    item.origin_node_name = self.name

    def get_repr_and_socket_from_attr_name(self, attr_name):
        socket_repr = maximum_spec_vd_dict[attr_name]
        return socket_repr, self.inputs[socket_repr.name]

    def get_attr_from_input(self, item):

        socket_repr, associated_socket = self.get_repr_and_socket_from_attr_name(item.attr_name)

        if associated_socket.is_linked:
            data = associated_socket.sv_get()

            if socket_repr.kind in {'4f', '3f', 'i'}:
                return data[0][0]
            elif socket_repr.kind in {'b'}:
                return bool(data[0][0])
            elif socket_repr.kind in {'enum'}:
                prop_signature = self.vd_items_props_mk2.__annotations__[item.attr_name][1]
                enum_index = data[0][0]
                enum_item = prop_signature['items'][enum_index]
                return enum_item[0]
        else:
            return None

    def make_value_serializable(self, attr, value):
        if maximum_spec_vd_dict[attr].kind in {'3f', '4f'}:
            value = value[:]
        return value

    @property
    def attrdict_from_state(self):

        current_attr_dict = {}
        if self.vd_items_group_mk2 and self.vd_items_props_mk2:
            for item in self.vd_items_group_mk2:
                attr = item.attr_name
                if not item.show_socket and not item.use_default:
                    # apparantly no desire to pass this attr
                    continue
                if item.use_default or not item.show_socket:
                    value = getattr(self.vd_items_props_mk2[0], attr)
                    value = self.make_value_serializable(attr, value)
                else:
                    value = self.get_attr_from_input(item)
                    if value is None:
                        continue
                current_attr_dict[attr] = value

        return current_attr_dict

    def migrate_from(self, old_node):
        self.location.y += 150
        raise Exception('Migration has to be done manually')

    def process(self):
        self.ensure_correct_origin_node_name()
        self.outputs['attrs'].sv_set([self.attrdict_from_state])

    ## ---- UI JSON STORAGE SECTION BELOW THIS LINE

    def load_from_json(self, node_data: dict, import_version: float):
        """ this gets triggered by IOJSON to populate this node from json """
        if import_version <= 0.08:
            strings_json = node_data['attr_storage']
            attrs_dict = json.loads(strings_json)['attrs']
            state_dict = json.loads(strings_json)['state']

            self.id_data.freeze(hard=True)

            # repopulate vd_items_group_mk2
            for item in self.vd_items_group_mk2:
                attr_details = attrs_dict[item.attr_name]
                socket_repr, associated_socket = self.get_repr_and_socket_from_attr_name(item.attr_name)
                if attr_details['show_socket']:
                    item.show_socket = True
                if attr_details['use_default']:
                    item.use_default = True

            # repopulate vd_items_props_mk2
            for item, value in state_dict.items():
                setattr(self.vd_items_props_mk2[0], item, value)

            self.id_data.unfreeze(hard=True)


classes = [SvVDMK4Item, SvVDMK4Properties, SV_UL_VDMK4ItemList, SvVDAttrsNodeMk2]
register, unregister = bpy.utils.register_classes_factory(classes)
