
# hotswap_macros.py

def swap_vd_mv(context, operator, term, nodes, links):
    """ hotswap viewerdraw <---> meshview ///"""
    active_node = context.active_node
    if active_node and active_node.bl_idname == 'SvViewerDrawMk4':
        loc = active_node.location[:]
        tree = context.space_data.edit_tree
        nodes, links = tree.nodes, tree.links
        mv = tree.nodes.new('SvMeshViewer')

        frame = active_node.parent
        if frame:
            mv.location = active_node.absolute_location
            mv.parent = frame
        else: 
            mv.location = loc

        a_inputs = active_node.inputs
        link_matches = [[0, 0], [1, 1], [2, 2], [3, 4]]
        for idx_a, idx_b in link_matches:
        	if a_inputs[idx_a].is_linked:
        	    links.new(a_inputs[idx_a].links[0].from_socket, mv.inputs[idx_b])

        nodes.remove(active_node)