# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from sverchok.utils.sv_node_utils import frame_adjust
from sverchok.menu import draw_add_node_operator
from sverchok.ui.presets import node_supports_presets, apply_default_preset
from sverchok.core.sockets import SvCurveSocket, SvSurfaceSocket, SvStringsSocket, SvSolidSocket


supported_mesh_viewers = {'SvMeshViewer', 'SvViewerDrawMk4'}

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

def get_output_sockets_map(node):
    """
    because of inconsistent socket naming, we will use pattern matching (ignoring capitalization)
    - verts: verts, vers, vertices, vectors, vecs  (ver, vec)
    - edges: edges, edgs, edgpol  (edg)
    - faces: faces, poly, pols, edgpol, (pol, fac)
    For curves and surfaces checks if they belong to the corresponding class

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
    got_curves = False
    got_surface = False
    got_solid = False
    # we can surely use regex for this, but for now this will work.
    for socket in node.outputs:

        if socket.hide or socket.hide_safe:
            continue

        socket_name = socket.name.lower()

        if not got_verts and ('ver' in socket_name or 'vec' in socket_name):
            output_map['verts'] = socket.name
            got_verts = True

        elif not got_edges and 'edg' in socket_name and isinstance(socket, SvStringsSocket):
            output_map['edges'] = socket.name
            got_edges = True

        elif not got_faces and ('face' in socket_name or 'pol' in socket_name) and isinstance(socket, SvStringsSocket):
            output_map['faces'] = socket.name
            got_faces = True

        elif not got_curves and isinstance(socket, SvCurveSocket):
            output_map['curve'] = socket.name
            got_curves = True

        elif not got_surface and isinstance(socket, SvSurfaceSocket):
            output_map['surface'] = socket.name
            got_surface = True

        elif not got_solid and isinstance(socket, SvSolidSocket):
            output_map['solid'] = socket.name
            got_solid = True

    return output_map

def offset_node_location(existing_node, new_node, offset):
    new_node.location = existing_node.location.x + offset[0] + existing_node.width, existing_node.location.y  + offset[1]


def conect_to_3d_viewer(tree):
    if hasattr(tree.nodes.active, 'viewer_map'):
        view_node(tree)
    else:
        add_connection(tree, bl_idname_new_node="SvViewerDrawMk4", offset=[60, 0])

def view_node(tree):
    '''viewer map is a node attribute to inform to the operator how to visualize
    the node data
    it is a list with two items.
    The first item is a list with tuples, every tuple need to have the node bl_idanme and offset to the previous node
    The second item is a list with tuples, every tuple indicates a link.
    The link is defined by two pairs of numbers, referring to output and input
    The first number of every pair indicates the node being 0 the active node 1 the first needed node and so on
    The second nmber of every pair indicates de socket index.

    So to say: create a Viewer Draw with a offset of 60,0 and connect the first output to the vertices input
    the node would need to have this:

        viewer_map = [
            ("SvViewerDrawMk4", [60, 0])
            ], [
            ([0, 0], [1, 0])
            ]

    '''
    nodes = tree.nodes
    links = tree.links
    existing_node = nodes.active
    node_list = [existing_node]
    output_map = existing_node.viewer_map

    for node in output_map[0]:
        bl_idname_new_node, offset = node
        new_node = nodes.new(bl_idname_new_node)
        apply_default_preset(new_node)
        offset_node_location(node_list[-1], new_node, offset)
        frame_adjust(node_list[-1], new_node)
        node_list.append(new_node)
    for link in output_map[1]:
        output_s, input_s = link
        links.new(node_list[output_s[0]].outputs[output_s[1]],
                  node_list[input_s[0]].inputs[input_s[1]])


def add_connection(tree, bl_idname_new_node, offset):

    nodes = tree.nodes
    links = tree.links

    output_map = get_output_sockets_map(nodes.active)

    existing_node = nodes.active

    if isinstance(bl_idname_new_node, str):
        # single new node..

        new_node = nodes.new(bl_idname_new_node)
        apply_default_preset(new_node)
        offset_node_location(existing_node, new_node, offset)
        frame_adjust(existing_node, new_node)

        outputs = existing_node.outputs
        inputs = new_node.inputs

        if existing_node.bl_idname in supported_mesh_viewers and bl_idname_new_node == 'SvIDXViewer28':
            new_node.draw_bg = True
            connect_idx_viewer(tree, existing_node, new_node)

        elif bl_idname_new_node == 'SvStethoscopeNodeMK2':
            # we can't determine thru cursor location which socket was nearest the rightclick
            # maybe in the future.. or if someone does know :)
            for socket in outputs:
                if socket.hide:
                    continue
                # connect_stethoscope to first visible output socket of active node
                links.new(socket, inputs[0])
                break

            tree.update()   # without this the node won't show output until an update is triggered manually
            # existing_node.process_node(None)

        elif bl_idname_new_node == 'SvViewerDrawMk4':
            if 'verts' in output_map:
                links.new(outputs[output_map['verts']], inputs[0])
                if 'faces' in output_map:
                    links.new(outputs[output_map['faces']], inputs[2])
                if 'edges' in output_map:
                    links.new(outputs[output_map['edges']], inputs[1])
            elif 'curve' in output_map:

                eval_node = nodes.new('SvExEvalCurveNode')
                apply_default_preset(eval_node)
                offset_node_location(existing_node, eval_node, offset)
                frame_adjust(existing_node, eval_node)
                offset_node_location(eval_node, new_node, offset)
                frame_adjust(eval_node, new_node)
                links.new(outputs[output_map['curve']], eval_node.inputs[0])
                links.new(eval_node.outputs[0], inputs[0])
                links.new(eval_node.outputs[1], inputs[1])

            elif 'surface' in output_map:
                eval_node = nodes.new('SvExEvalSurfaceNode')
                apply_default_preset(eval_node)
                offset_node_location(existing_node, eval_node, offset)
                frame_adjust(existing_node, eval_node)
                offset_node_location(eval_node, new_node, offset)
                frame_adjust(eval_node, new_node)
                links.new(outputs[output_map['surface']], eval_node.inputs[0])
                links.new(eval_node.outputs[0], inputs[0])
                links.new(eval_node.outputs[1], inputs[1])
                links.new(eval_node.outputs[2], inputs[2])
            elif 'solid' in output_map:
                tree.nodes.remove(new_node)
                new_node = nodes.new('SvSolidViewerNode')
                apply_default_preset(new_node)
                offset_node_location(existing_node, new_node, offset)
                frame_adjust(existing_node, new_node)
                links.new(outputs[output_map['solid']], new_node.inputs[0])
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
            conect_to_3d_viewer(tree)

        elif self.fn == 'vdmk2 + idxv':
            add_connection(tree, bl_idname_new_node=["SvViewerDrawMk4", "SvIDXViewer28"], offset=[180, 0])
        elif self.fn == '+idxv':
            add_connection(tree, bl_idname_new_node="SvIDXViewer28", offset=[180, 0])
        elif self.fn == 'stethoscope':
            add_connection(tree, bl_idname_new_node="SvStethoscopeNodeMK2", offset=[60, 0])

        return {'FINISHED'}

class SvNodeviewRClickMenu(bpy.types.Menu):
    bl_label = "Right click menu for Sverchok"
    bl_idname = "NODEVIEW_MT_sv_rclick_menu"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        return tree_type in {'SverchCustomTreeType', }

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
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
            if len(node.outputs):
                layout.menu('SV_MT_AllSocketsOptionsMenu', text='Outputs post-process')
                layout.separator()
            if node.bl_idname in {'SvViewerDrawMk4', 'SvBmeshViewerNodeMK2'}:
                layout.operator("node.sv_deligate_operator", text="Connect IDXViewer").fn = "+idxv"
            else:
                if has_outputs(node):
                    layout.operator("node.sv_deligate_operator", text="Connect ViewerDraw").fn = "vdmk2"
            if len(node.outputs):
                layout.operator("node.sv_deligate_operator", text="Connect stethoscope").fn = "stethoscope"


            layout.separator()

        if node_supports_presets(node):
            layout.menu('SV_MT_LoadPresetMenu', text="Node Presets")

        if node and node.bl_idname == 'NodeFrame':
            # give options for Frame nodes..
            col = layout.column(align=True)
            col.prop(node, 'label', text='', icon='NODE')
            col.prop(node, 'use_custom_color')
            if node.use_custom_color:
                col.prop(node, 'color', text='')
            col.prop(node, 'label_size', slider=True)
            col.prop(node, 'shrink')

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
