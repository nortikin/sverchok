# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.utils.logging import debug, info, warning, error, exception


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


def find_enumerators(node):
    ignored_enums = ['bl_icon', 'bl_static_type', 'type']
    node_props = node.bl_rna.properties[:]
    f = filter(lambda p: isinstance(p, bpy.types.EnumProperty), node_props)
    return [p.identifier for p in f if not p.identifier in ignored_enums]


def compile_socket(link):

    try:
        link_data = (link.from_node.name, link.from_socket.index, link.to_node.name, link.to_socket.index)
    except Exception as err:
        if "'NodeSocketColor' object has no attribute 'index'" in repr(err):
            debug('adding node reroute using socketname instead if index')
        else:
            error(repr(err))
        link_data = (link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name)

    return link_data


def collect_custom_socket_properties(node, node_dict):
    # print("** PROCESSING custom properties for node: ", node.bl_idname)
    input_socket_storage = {}
    for socket in node.inputs:

        # print("Socket %d of %d" % (socket.index + 1, len(node.inputs)))

        storable = {}
        tracked_props = 'use_expander', 'use_quicklink', 'expanded', 'use_prop'

        for tracked_prop_name in tracked_props:
            if not hasattr(socket, tracked_prop_name):
                continue

            value = getattr(socket, tracked_prop_name)
            defaultValue = socket.bl_rna.properties[tracked_prop_name].default
            # property value same as default ? => don't store it
            if value == defaultValue:
                continue

            # print("Processing custom property: ", tracked_prop_name, " value = ", value)
            storable[tracked_prop_name] = value

            if tracked_prop_name == 'use_prop' and value:
                # print("prop type:", type(socket.prop))
                storable['prop'] = socket.prop[:]

        if storable:
            input_socket_storage[socket.index] = storable

    if input_socket_storage:
        node_dict['custom_socket_props'] = input_socket_storage
    # print("**\n")
