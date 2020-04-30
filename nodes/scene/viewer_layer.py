# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import FloatProperty, BoolProperty, StringProperty, CollectionProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.handlers import subscribe_to_changes, sverchok_trees
from sverchok.utils.logging import debug


layer_names = [
    "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta",
    "Iota", "Kappa", "Lambda", "Mu", "Nu", "Xi", "Omicron", "Pi", "Rho",
    "Sigma", "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"]

# set of supported viewer nodes + mapping of their various respective attributes
viewer_dict = {
    'SvVDExperimental': {
        'display': {
            'vert': "display_verts",
            'edge': "display_edges",
            'face': "display_faces"
        },
        'colors': {
            'vert': "vert_color",
            'edge': "edge_color",
            'face': "face_color"
        }
    },
    'SvIDXViewer28': {
        'display': {
            'vert': "display_vert_index",
            'edge': "display_edge_index",
            'face': "display_face_index"
        },
        'colors': {
            'vert': "numid_verts_col",
            'edge': "numid_edges_col",
            'face': "numid_faces_col"
        }
    }
}

elements = {'vert': 'UV_VERTEXSEL', 'edge': 'UV_EDGESEL', 'face': 'UV_FACESEL'}


def viewer_name_change_callback(self):
    ''' Subscription callback for viewer node name change (calls from handlers.py) '''
    debug("* VLN: viewer_name_change_callback")
    # propagate the name change callback to all Viewer Layer nodes
    for node_tree in sverchok_trees():
        layer_nodes = [n for n in node_tree.nodes if n.bl_idname == "SvViewerLayerNode"]
        for node in layer_nodes:
            debug("VLN: propagate name change callback to: %s", node.bl_idname)
            node.viewer_changed_name()


def subscribe_to_viewer_nodes_name_changes():
    ''' Subscribe to name change of various viewer nodes (calls to handlers.py) '''
    debug("* VLN: layer_nodes_subscribe_to_viewer_changes")
    VIZ_NODE1 = sverchok.nodes.viz.vd_draw_experimental.SvVDExperimental
    VIZ_NODE2 = sverchok.nodes.viz.viewer_idx28.SvIDXViewer28

    subscribe_to_list = [(VIZ_NODE1, "name"), (VIZ_NODE2, "name")]

    for subscribe_to in subscribe_to_list:
        subscribe_to_changes(subscribe_to, "Viewer node name changed", viewer_name_change_callback)


def update_viewer_list(self, context):
    ''' Update callback (wrapper) when a viewer entry name changes in the layer node '''
    debug("* VLN: SvViewerGroup: update_viewer_list")
    viewer_name_change_callback(None)


class SvLayerOperatorCallback(bpy.types.Operator):
    ''' Delegate layer changes to the layer node '''
    bl_idname = "nodes.sv_viewer_layer_callback"
    bl_label = "Sv Ops Layer callback"

    function_name: StringProperty()  # what function to call
    layer_name: StringProperty()  # layer name
    layer_id: IntProperty() # unique id to find layer in the node
    element_type: StringProperty()  # "vert", "edge" or "face"

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(self)
        return {"FINISHED"}


class SvViewerOperatorCallback(bpy.types.Operator):
    ''' Delegate viewer changes to the layer node '''
    bl_idname = "nodes.sv_viewer_callback"
    bl_label = "Sv Ops Viewer callback"

    function_name: StringProperty()  # what function to call
    layer_name: StringProperty()  # layer name
    layer_id: IntProperty()  # unique id to find layer in the node
    viewer_id: IntProperty()  # unique id to find viewer in the layer

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(self.layer_id, self.viewer_id)
        return {"FINISHED"}


class SvViewerGroup(bpy.types.PropertyGroup):
    ''' Property group for the viewer entries '''
    collection_name: CollectionProperty(name="List of Viewers", type=bpy.types.PropertyGroup)
    node_name: StringProperty(update=update_viewer_list)
    viewer_id: IntProperty(name="Viewer ID", description="ID of the viewer's entry in the layer")


class SvViewerLayerGroup(bpy.types.PropertyGroup):
    ''' Property group for the layer entries '''
    collection_name: CollectionProperty(name="List of Layers", type=bpy.types.PropertyGroup)
    viewers: CollectionProperty(name="Viewers", type=SvViewerGroup)
    expand: BoolProperty(name="Expand Layer", default=True)
    layer_id: IntProperty(name="Layer ID", description="ID of the layer's entry in the node")


class SvViewerLayerNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Layer, Viewer
    Tooltip: Group viewer nodes into layers to easily manipulate their settings
    """
    bl_idname = 'SvViewerLayerNode'
    bl_label = 'Viewer Layers'
    bl_icon = 'HIDE_OFF'

    layers: CollectionProperty(name="Layers", type=SvViewerLayerGroup)
    layer_id: IntProperty(name="Layer ID", default=0)
    viewer_id: IntProperty(name="Viewer ID", default=0)

    def viewer_changed_name(self):
        ''' Callback used when external viewer nodes name changed '''
        debug("* VLN: SvViewerLayerNode: viewer_changed_name")
        self.update_layers_viewers_lists()

    def number_of_viewer_nodes(self):
        ''' Total number of viewer nodes in the tree '''
        count = 0
        for node in self.id_data.nodes:
            if node.bl_idname in viewer_dict.keys():
                count += 1
        return count

    def get_next_default_layer_name(self):
        return layer_names[len(self.layers)-1]

    def get_next_layer_id(self):
        self.layer_id += 1
        return self.layer_id

    def get_next_viewer_id(self):
        self.viewer_id += 1
        return self.viewer_id

    def status_icon(self, status):
        #  status all ON                 status all OFF               status MIX
        return "HIDE_OFF" if status == 1 else "HIDE_ON" if status == 2 else "DOT"

    def new_status(self, status):
        if status == 1:  # all ON => next will make all OFF
            new_status = False
        elif status == 2:  # all OFF => next will make all ON
            new_status = True
        else:  # a MIX => next will make all ON
            new_status = True

        return new_status

    def layer_visibility_status(self, layer):
        """
        Return the layer's cummulative viewer [ON/OFF/MIX] status: [1, 2 or 3]
        status = (hidden bit) | (visible bit)
        1 = 0x01 : status all ON (visible)
        2 = 0x10 : status all OFF (hidden)
        3 = 0x11 : status MIX (both visible & hidden)
        """
        tree_nodes = self.id_data.nodes
        status = 0
        for viewer in layer.viewers:
            viewer_node = tree_nodes.get(viewer.node_name)
            if viewer_node:
                if viewer_node.activate:  # mark that the layer has active viewers
                    status = status | 1
                else:  # mark that the layer has inactive viewers
                    status = status | 2

        return status

    def all_layer_visibility_status(self):
        ''' Return the cummulative visibility status of all layers '''
        status = 0
        for layer in self.layers:
            status = status | self.layer_visibility_status(layer)

        return status

    def setup_subscriptions(self):
        """
        Setup node/attribute subscriptions

        This is called from the handlers.py after loading blender file to allow
        existing viewer layer node to subscribe to viewer node name changes.
        """
        debug("* setup_subscriptions in class: %s", self.bl_idname)
        subscribe_to_viewer_nodes_name_changes()
        # also, update all layers viewers lists (if any exist)
        self.update_layers_viewers_lists()

    def update_layers_viewers_lists(self):
        ''' Update the viewer name lists for viwers in all layers '''
        debug("* update_layers_viewers_lists")

        all_viewer_names = [n.name for n in self.id_data.nodes if n.bl_idname in viewer_dict.keys()]
        debug("all viewer names = {}".format(all_viewer_names))

        if self.layers:
            debug("update node ({0} layers)".format(len(self.layers)))
            for layer in self.layers:
                debug(" update layer \"{0}\" ({1} viewers): ".format(layer.name, len(layer.viewers)))

                layer_viewer_names = list(set([v.node_name for v in layer.viewers if v.node_name != ""]))
                debug("layer viewer names = {}".format(layer_viewer_names))

                unused_names = [name for name in all_viewer_names if name not in layer_viewer_names]
                debug("unused names = {}".format(unused_names))

                if layer.viewers:
                    for viewer in layer.viewers:
                        debug("  update viewer: %s", viewer.name)

                        viewer.collection_name.clear()

                        for name in unused_names:
                            debug("   adding viewer %s to the list", name)
                            viewer.collection_name.add().name = name

                        if viewer.node_name in all_viewer_names and viewer.node_name not in unused_names:
                            viewer.collection_name.add().name = viewer.node_name
                else:
                    debug("layer \"{0}\" has no viewers".format(layer.name))
        else:
            debug("node has no layers")

    def draw_buttons(self, context, layout):
        lcb = SvLayerOperatorCallback.bl_idname  # LAYER callback
        vcb = SvViewerOperatorCallback.bl_idname  # VIEWER callback

        tree_nodes = self.id_data.nodes

        if self.layers:
            # overall controls
            box = layout.box()
            row = box.row(align=True)
            split = row.split(factor=0.5)

            all_expand = split.operator(lcb, text='', icon='COLLAPSEMENU')
            all_expand.function_name = 'ops_toggle_all_layer_expansion'

            for element in elements:
                toggle_element = split.operator(lcb, text='', icon=elements[element])
                toggle_element.function_name = "ops_toggle_element_visibility"
                toggle_element.element_type = element

            status = self.all_layer_visibility_status()
            all_toggle = split.operator(lcb, text='', icon=self.status_icon(status))
            all_toggle.function_name = 'ops_toggle_all_layer_visibility'

        for layer in self.layers:
            row = layout.row(align=True)
            split = row.split(factor=0.1)

            split.prop(layer, "expand", icon="COLLAPSEMENU", text="")
            split = split.split(factor=0.6)
            row = split.row(align=True)
            row.prop(layer, "name", text="")

            # show the REMOVE LAYER button
            rm_button = row.operator(lcb, text='', icon='REMOVE')
            rm_button.function_name = "ops_remove_layer"
            rm_button.layer_name = layer.name
            rm_button.layer_id = layer.layer_id

            # show the LAYER VISIBILITY button
            status = self.layer_visibility_status(layer)
            viz_button = split.operator(lcb, text='', icon=self.status_icon(status))
            viz_button.function_name = "ops_toggle_layer_visibility"
            viz_button.layer_name = layer.name
            viz_button.layer_id = layer.layer_id

            if layer.expand:
                # show entries for all the viewers in the layer
                box = layout.box()
                for viewer in layer.viewers:
                    row = box.row(align=True)
                    part1 = row.split(factor=0.7 if self.width < 300 else 0.5 if self.width < 400 else 0.4)
                    part1.prop_search(viewer, "node_name", viewer, 'collection_name', icon='NODE', text='')

                    viewer_node = tree_nodes.get(viewer.node_name)
                    if viewer_node:
                        display = viewer_dict[viewer_node.bl_idname]['display']
                        color = viewer_dict[viewer_node.bl_idname]['colors']

                        part2 = part1.split(align=True)
                        if self.width > 400:
                            for element in elements:
                                part2.prop(viewer_node, display[element], text='', icon=elements[element])

                        if self.width > 300:
                            for element in elements:
                                part2.prop(viewer_node, color[element], text='')

                        if viewer_node.bl_idname == "SvIDXViewer28":
                            if self.width > 400:
                                part2.prop(viewer_node, "draw_bface", text='', icon="GHOST_ENABLED")

                        icon_name = "HIDE_OFF" if viewer_node.activate else "HIDE_ON"
                        part2.prop(viewer_node, "activate", toggle=True, icon=icon_name, text='')

                    else:  # no viewer node for viewer entry => show remove option
                        part2 = part1.split(align=True)
                        # add the REMOVE VIEWER button
                        rm_button = part2.operator(vcb, text='', icon='REMOVE')
                        rm_button.function_name = "ops_remove_viewer"
                        rm_button.layer_name = layer.name
                        rm_button.layer_id = layer.layer_id
                        rm_button.viewer_id = viewer.viewer_id

                # show the ADD NEW VIEWER to layer button
                # max number of viewer enties <= number of available viewers
                if len(layer.viewers) < self.number_of_viewer_nodes():
                    add_button = box.row().operator(lcb, text='', icon='PLUS')
                    add_button.function_name = "ops_add_new_viewer"
                    add_button.layer_name = layer.name
                    add_button.layer_id = layer.layer_id

        # show the ADD NEW LAYER button
        layout.row().operator(lcb, text='', icon='COLLECTION_NEW').function_name = "ops_add_new_layer"

    def ops_add_new_viewer(self, op):
        debug("* VLN: SvViewerLayerNode: ops_add_new_viewer")
        layer_name = op.layer_name
        layer_id = op.layer_id
        debug("add new viewer to layer: %s", layer_name)
        debug("number of layers: %d", len(self.layers))
        for layer in self.layers:
            if layer.layer_id == layer_id:
                viewer_id = self.get_next_viewer_id()
                debug("creating viewer with entry id: %d", viewer_id)
                viewer = layer.viewers.add()
                viewer.name = str(viewer_id)
                viewer.viewer_id = viewer_id
                debug("mark viewer name empty")
                viewer.node_name = ''  # trigger a list update

        self.update_layers_viewers_lists()

    def ops_remove_viewer(self, layer_id, viewer_id):
        debug("* VLN: SvViewerLayerNode: ops_remove_viewer")
        debug("remove viewer in layer_id: %d with viewer_id: %d", layer_id, viewer_id)
        for layer in self.layers:
            if layer.layer_id == layer_id:
                for index, viewer in enumerate(layer.viewers):
                    if viewer.viewer_id == viewer_id:
                        debug("removing viewer from index: %d with viewer_id: %d", index, viewer_id)
                        debug("viewer name: %s", viewer.node_name)
                        layer.viewers.remove(index)
                        self.update_layers_viewers_lists()
                        return

    def ops_add_new_layer(self, dummy):
        debug("* VLN: SvViewerLayerNode: ops_add_new_layer")
        layer = self.layers.add()
        layer.name = self.get_next_default_layer_name()
        layer.layer_id = self.get_next_layer_id()
        debug("add new layer: %s", layer.name)

    def ops_remove_layer(self, op):
        debug("* VLN: SvViewerLayerNode: ops_remove_layer")
        layer_name = op.layer_name
        layer_id = op.layer_id
        debug("remove layer: %s", layer_name)
        for index, layer in enumerate(self.layers):
            if layer.layer_id == layer_id:
                debug("removing layer from index: %d", index)
                self.layers.remove(index)
                return

    def ops_toggle_layer_visibility(self, op):
        debug("* VLN: SvViewerLayerNode: ops_toggle_layer_visibility")
        layer_name = op.layer_name
        layer_id = op.layer_id
        debug("toggle layer: %s", layer_name)
        tree_nodes = self.id_data.nodes
        for layer in self.layers:
            if layer.layer_id == layer_id:
                # check layer's viewers active state
                status = self.layer_visibility_status(layer)

                new_status = self.new_status(status)

                for viewer in layer.viewers:
                    viewer_node = tree_nodes.get(viewer.node_name)
                    if viewer_node:
                        viewer_node.activate = new_status

    def ops_toggle_all_layer_visibility(self, dummy):
        debug("* VLN: SvViewerLayerNode: ops_toggle_all_layer_visibility")
        status = 0
        for layer in self.layers:
            status = status | self.layer_visibility_status(layer)

        new_status = self.new_status(status)

        tree_nodes = self.id_data.nodes
        for layer in self.layers:
            for viewer in layer.viewers:
                viewer_node = tree_nodes.get(viewer.node_name)
                if viewer_node:
                    viewer_node.activate = new_status

    def ops_toggle_all_layer_expansion(self, dummy):
        debug("* VLN: SvViewerLayerNode: ops_toggle_all_layer_expansion")
        status = 0
        for layer in self.layers:
            if layer.expand:
                status = status | 1
            else:
                status = status | 2

        new_status = self.new_status(status)

        for layer in self.layers:
            layer.expand = new_status

    def ops_toggle_element_visibility(self, op):
        ''' Toggle visibility for vert, edge or face elements '''
        debug("* VLN: ops_toggle_element_visibility")

        element = op.element_type  # vert, edge or face

        tree_nodes = self.id_data.nodes

        status = 0
        for layer in self.layers:
            for viewer in layer.viewers:
                viewer_node = tree_nodes.get(viewer.node_name)

                if viewer_node:
                    attribute = viewer_dict[viewer_node.bl_idname]['display'][element]
                    viewer_status = getattr(viewer_node, attribute)

                    if viewer_status:  # accumulate visible and invisible status
                        status = status | 1
                    else:
                        status = status | 2

        new_status = self.new_status(status)

        for layer in self.layers:
            for viewer in layer.viewers:
                viewer_node = tree_nodes.get(viewer.node_name)
                if viewer_node:
                    attribute = viewer_dict[viewer_node.bl_idname]['display'][element]
                    setattr(viewer_node, attribute, new_status)

    def sv_init(self, context):
        self.width = 432

    def process(self):
        ...


classes = SvLayerOperatorCallback, SvViewerOperatorCallback, SvViewerGroup, SvViewerLayerGroup, SvViewerLayerNode


def register():
    debug("* VLN: REGISTER the SvViewerLayerNode classes")
    _ = [bpy.utils.register_class(cls) for cls in classes]
    # setup subscriptions (useful when reloading the addon)
    subscribe_to_viewer_nodes_name_changes()


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]
