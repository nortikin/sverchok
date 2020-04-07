# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from sverchok.utils.sv_node_utils import frame_adjust
from sverchok.menu import draw_add_node_operator

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
supported_mesh_viewers = {'SvBmeshViewerNodeMK2', 'ViewerNode2'}

# for rclick i want convenience..
common_nodes = [
    ['GenVectorsNode', 'VectorsOutNode'],
    ['SvNumberNode', 'SvGenNumberRange'],
    ['SvScalarMathNodeMK4', 'SvVectorMathNodeMK3'],
    ['SvComponentAnalyzerNode'],
    ['---', 'NodeReroute', 'ListLengthNode']
]


def connect_idx_viewer(tree, existing_node, new_node):
    # get connections going into vdmk2 and make a new idxviewer and connect the same sockets to that.
    links = tree.links
    links.new(existing_node.inputs[0].other, new_node.inputs[0])


def valid_active_node(nodes):
    if nodes:
        # a previously active node can remain active even when no nodes are selected.
        if nodes.active and nodes.active.select:
            return nodes.active

def has_outputs(node):
    return node and len(node.outputs)

def get_verts_edge_poly_output_sockets(node):
    """
    because of inconsistent socket naming, we will use pattern matching (ignoring capitalization)
    - verts: verts, vers, vertices, vectors, vecs  (ve)
    - edges: edges, edgs, edgpol  (edg)
    - faces: faces, poly, pols, edgpol, (pol, fac)

    > generally the first 3 outputs of a node will contain these
    > generally if a node outputs polygons, it won't be necessary to connect edges
    > if a node doesn't output polygons, only edges need to be connected

    if the following code is in master, it will find the vast majority of mesh sockets,
    in the case that it does not, dedicated lookup-tables for specific nodes are a consideration.

    """
    output_map = {}
    got_verts = False
    got_edges = False
    got_faces = False

    # we can surely use regex for this, but for now this will work.
    for socket in node.outputs:
        socket_name = socket.name.lower()

        if not got_verts and 've' in socket_name:
            output_map['verts'] = socket.name
            got_verts = True

        elif not got_edges and 'edg' in socket_name:
            output_map['edges'] = socket.name
            got_edges = True

        elif not got_faces and ('face' in socket_name or 'pol' in socket_name):
            output_map['faces'] = socket.name
            got_faces = True

    return output_map

def offset_node_location(existing_node, new_node, offset):
    new_node.location = existing_node.location.x + offset[0] + existing_node.width, existing_node.location.y  + offset[1]

def add_connection(tree, bl_idname_new_node, offset):

    nodes = tree.nodes
    links = tree.links

    output_map = get_verts_edge_poly_output_sockets(nodes.active)

    existing_node = nodes.active

    if isinstance(bl_idname_new_node, str):
        # single new node..

        new_node = nodes.new(bl_idname_new_node)
        offset_node_location(existing_node, new_node, offset)
        frame_adjust(existing_node, new_node)

        outputs = existing_node.outputs
        inputs = new_node.inputs

        # first scenario not handelled in b28 yet.
        if existing_node.bl_idname in supported_mesh_viewers and bl_idname_new_node == 'IndexViewerNode':
            new_node.draw_bg = True
            connect_idx_viewer(tree, existing_node, new_node)

        elif bl_idname_new_node == 'SvStethoscopeNodeMK2':
            # we can't determin thru cursor location which socket was nearest the rightclick
            # maybe in the future.. or if someone does know :)
            for socket in outputs:
                if socket.hide:
                    continue
                # connect_stethoscope to first visible output socket of active node
                links.new(socket, inputs[0])
                break

            tree.update()   # without this the node won't show output until an update is triggered manually
            # existing_node.process_node(None)

        elif bl_idname_new_node == 'SvVDExperimental':

            if 'verts' in output_map:
                links.new(outputs[output_map['verts']], inputs[0])
                if 'faces' in output_map:
                    links.new(outputs[output_map['faces']], inputs[2])
                if 'edges' in output_map:
                    links.new(outputs[output_map['edges']], inputs[1])

            tree.update()
            # existing_node.process_node(None)

        else:
            ...
    elif isinstance(bl_idname_new_node, list):
        # maybe vdmk2 + indexviewer
        ...



class SvGenericDeligationOperator(bpy.types.Operator):

    bl_idname = "node.sv_deligate_operator"
    bl_label = "Execute generic code"

    fn: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = context.space_data.edit_tree

        if self.fn == 'vdmk2':
            add_connection(tree, bl_idname_new_node="SvVDExperimental", offset=[60, 0])
        elif self.fn == 'vdmk2 + idxv':
            add_connection(tree, bl_idname_new_node=["ViewerNode2", "IndexViewerNode"], offset=[180, 0])
        elif self.fn == '+idxv':
            add_connection(tree, bl_idname_new_node="IndexViewerNode", offset=[180, 0])
        elif self.fn == 'stethoscope':
            add_connection(tree, bl_idname_new_node="SvStethoscopeNodeMK2", offset=[60, 0])

        return {'FINISHED'}

class SvNodeviewRClickMenu(bpy.types.Menu):
    bl_label = "Right click menu for Sverchok"
    bl_idname = "NODEVIEW_MT_sv_rclick_menu"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        return tree_type in sv_tree_types

    def draw(self, context):
        layout = self.layout
        tree = context.space_data.edit_tree

        try:
            nodes = tree.nodes
        except:
            layout.operator("node.new_node_tree", text="New Sverchok Node Tree", icon="RNA_ADD")
            return

        node = valid_active_node(nodes)

        if node:
            if hasattr(node, "rclick_menu"):
                node.rclick_menu(context, layout)
                layout.separator()

            if node.bl_idname in {'ViewerNode2', 'SvBmeshViewerNodeMK2'}:
                layout.operator("node.sv_deligate_operator", text="Connect IDXViewer").fn = "+idxv"
            else:
                if has_outputs(node):
                    layout.operator("node.sv_deligate_operator", text="Connect ViewerDraw").fn = "vdmk2"
                    # layout.operator("node.sv_deligate_operator", text="Connect ViewerDraw + IDX").fn="vdmk2 + idxv"
            if len(node.outputs):
                layout.operator("node.sv_deligate_operator", text="Connect stethoscope").fn = "stethoscope"

            layout.separator()

        if node and node.bl_idname == 'NodeFrame':
            # give options for Frame nodes..
            col = layout.column(align=True)
            col.prop(node, 'label', text='', icon='NODE')
            col.prop(node, 'use_custom_color')
            if node.use_custom_color:
                col.prop(node, 'color', text='')
            col.prop(node, 'label_size', slider=True)
            col.prop(node, 'shrink')

        if node and hasattr(node, 'monad'):
            layout.operator("node.sv_monad_make_unique", icon="RNA_ADD").use_transform=True

        layout.separator()
        layout.menu("NODEVIEW_MT_Dynamic_Menu", text='node menu')
        # layout.operator("node.duplicate_move")
        self.draw_conveniences(context, node)

    def draw_conveniences(self, context, node):
        layout = self.layout
        layout.separator()
        for nodelist in common_nodes:
            for named_node in nodelist:
                if named_node == '---':
                    layout.separator()
                else:
                    draw_add_node_operator(layout, named_node)



def register():
    bpy.utils.register_class(SvGenericDeligationOperator)
    bpy.utils.register_class(SvNodeviewRClickMenu)


def unregister():
    bpy.utils.unregister_class(SvNodeviewRClickMenu)
    bpy.utils.unregister_class(SvGenericDeligationOperator)
