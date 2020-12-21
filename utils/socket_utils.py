# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

# this functions are used in core.sockets

def format_bpy_property(prop):
    if isinstance(prop, (str, int, float)):
        return [[prop]]
    if hasattr(prop, '__len__'):
        # it looks like as some BLender property array - convert to tuple
        return [[prop[:]]]

    return [prop]

def setup_new_node_location(new_node, old_node):
    links_number = len([s for s in old_node.inputs if s.is_linked])
    new_node.location = (old_node.location[0] - 200, old_node.location[1] - 100 * links_number)
    if old_node.parent:
        new_node.parent = old_node.parent
        new_node.location = new_node.absolute_location
