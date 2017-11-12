import bpy

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}


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

        if not got_verts and 'vert' in socket_name:
            output_map['verts'] = socket.name
            got_verts = True

        if not got_edges and 'edg' in socket_name:
            output_map['edges'] = socket.name
            got_edges = True

        if not got_faces and 'face' in socket_name or 'poly' in socket_name:
            output_map['faces'] = socket.name
            got_faces = True

    return output_map

def offset_node_location(existing_node, new_node, offset):
    new_node.location = existing_node.location.x + offset[0], existing_node.location.y  + offset[1]

def add_connection(tree, bl_idname_new_node, offset):

    nodes = tree.nodes
    links = tree.links

    output_map = get_verts_edge_poly_output_sockets(nodes.active)

    existing_node = nodes.active

    if isinstance(bl_idname_new_node, str):
        # single new node..

        new_node = nodes.new(bl_idname_new_node)
        offset_node_location(existing_node, new_node, offset)
        
        if bl_idname_new_node == 'ViewerNode2':
            outputs = existing_node.outputs
            inputs = new_node.inputs

            if 'verts' in output_map:
                if 'faces' in output_map:
                    links.new(outputs[output_map['verts']], inputs[0])
                    links.new(outputs[output_map['faces']], inputs[1])
                elif 'edges' in output_map:
                    links.new(outputs[output_map['verts']], inputs[0])
                    links.new(outputs[output_map['edges']], inputs[1])

        else:
            ...
    elif isinstance(bl_idname_new_node, list):
        # maybe vdmk2 + indexviewer
        ...



class SvGenericDeligationOperator(bpy.types.Operator):

    bl_idname = "node.sv_deligate_operator"
    bl_label = "Execute generic code"

    fn = bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = context.space_data.edit_tree

        if self.fn == 'vdmk2':
            add_connection(tree, bl_idname_new_node="ViewerNode2", offset=[180, 0])
        elif self.fn == 'vdmk2 + idxv':
            add_connection(tree, bl_idname_new_node=["ViewerNode2", "IndexViewer"], offset=[180, 0])

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
        nodes = tree.nodes

        node = valid_active_node(nodes)
        if has_outputs(node):
            layout.operator("node.sv_deligate_operator", text="Connect ViewerDraw").fn="vdmk2"
            # layout.operator("node.sv_deligate_operator", text="Connect ViewerDraw + IDX").fn="vdmk2 + idxv"
        
        else:
            layout.menu("NODEVIEW_MT_Dynamic_Menu", text='node menu')


def register():
    bpy.utils.register_class(SvGenericDeligationOperator)
    bpy.utils.register_class(SvNodeviewRClickMenu)


def unregister():
    bpy.utils.unregister_class(SvNodeviewRClickMenu)
    bpy.utils.unregister_class(SvGenericDeligationOperator)
