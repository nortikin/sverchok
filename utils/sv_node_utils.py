# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


def recursive_framed_location_finder(node, loc_xy):
    locx, locy = loc_xy
    if node.parent:
        locx += node.parent.location.x
        locy += node.parent.location.y
        return recursive_framed_location_finder(node.parent, (locx, locy))
    else:
        return locx, locy


def frame_adjust(caller_node, new_node):
    if caller_node.parent:
        new_node.parent = caller_node.parent
        loc_xy = new_node.location[:]
        locx, locy = recursive_framed_location_finder(new_node, loc_xy)
        new_node.location = locx, locy


def nodes_bounding_box(selected_nodes):
    """
    usage:
    minx, maxx, miny, maxy = nodes_bounding_box(selected_nodes)
    """
    minx = +1e10
    maxx = -1e10
    miny = +1e10
    maxy = -1e10
    for node in selected_nodes:
        minx = min(minx, node.location.x)
        maxx = max(maxx, node.location.x + node.width)
        miny = min(miny, node.location.y - node.height)
        maxy = max(maxy, node.location.y)

    return minx, maxx, miny, maxy

def framed_nodes_bounding_box(selected_nodes):
    """
    usage:
    minx, maxx, miny, maxy = nodes_bounding_box(selected_nodes)
    warning: don't call this on ReRoute or Frame nodes.
    """
    minx = +1e10
    maxx = -1e10
    miny = +1e10
    maxy = -1e10
    for node in selected_nodes:
        
        node_loc_x, node_loc_y = node.absolute_location

        minx = min(minx, node_loc_x)
        maxx = max(maxx, node_loc_x + node.width)
        miny = min(miny, node_loc_y - node.height)
        maxy = max(maxy, node_loc_y)

    return minx, maxx, miny, maxy

def are_nodes_in_same_frame(nodes):
    """
    input: a list of nodes (expects no Reroute or Frame nodes)
    returns: 
       - < False > if the set is not length one.
       - < None > if no nodes are frames
       - < FrameNode > if all nodes have the same parent
    """
    parents = set([node.parent for node in nodes])
    if len(parents) == 1:
        return list(parents)[0]


def sync_pointer_and_stored_name(node, pointer_prop_name, prop_name):
    # in the event that the text datablock is renamed elsewhere, this will automatically
    # resync the stored name of the datablock. updates to datablock names do not 
    # automatically call the pointer updatefunction. hence this nonsense
    if hasattr(node, pointer_prop_name):
        pointer = getattr(node, pointer_prop_name)
        if not pointer:
            return
        if pointer.name != getattr(node, prop_name):
            setattr(node, prop_name, pointer.name)
            node.info(f"synchronized name of {node} from datablock name change")