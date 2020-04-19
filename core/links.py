# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Declaring namedtuple()
import collections
from sverchok.core.update_system import (
    build_update_list,
    process_from_nodes,
    )
from sverchok.core.node_id_dict import dict_of_node_tree, translate_node_id_to_node_name
SvLink = collections.namedtuple('SvLink', ['from_node_id', 'to_node_id', 'from_socket_id', 'to_socket_id'])

sv_links_cache = {}
sv_linked_output_sockets_cache = {}
sv_linked_input_sockets_cache = {}
sv_linked_inputted_nodes_cache = {}

def empty_links_cache():
    global sv_links_cache
    sv_links_cache = {}


def link_cache_is_ready(node_tree):
    return node_tree.tree_id in sv_links_cache


def get_output_socket_id(socket):
    if socket.node.bl_idname == 'NodeReroute':
        if socket.node.inputs[0].is_linked:
            return get_output_socket_id(socket.node.inputs[0].links[0].from_socket)
        else:
            return None, None
    else:
        return socket.socket_id, socket.node.node_id


def get_new_linked_nodes(new_sv_links, before_sv_links, before_output_sockets):
    affected_nodes = []
    for link in new_sv_links:
        if not link in before_sv_links:
            if not link.from_socket_id in before_output_sockets:
                if not link.from_node_id in affected_nodes:
                    affected_nodes.append(link.from_node_id)
            if not link.to_node_id in affected_nodes:
                affected_nodes.append(link.to_node_id)
    return affected_nodes


def get_new_unlinked_nodes(before_inputted_nodes, before_input_sockets, input_sockets, nodes_dict):
    affected_nodes = []

    for node_id, socket in zip(before_inputted_nodes, before_input_sockets):
        if not socket in input_sockets:
            #if the node has been deleted it is not affected
            if node_id in nodes_dict:
                affected_nodes.append(node_id)

    return affected_nodes


def split_new_links_data(new_sv_links):
    inputted_nodes = []
    input_sockets = []
    output_sockets = []
    for link in new_sv_links:
        inputted_nodes.append(link.to_node_id)
        input_sockets.append(link.to_socket_id)
        output_sockets.append(link.from_socket_id)

    return  inputted_nodes, input_sockets, output_sockets


def bl_links_to_sv_links(node_tree):

    new_sv_links = []
    for link in node_tree.links:
        if not link.to_socket.node.bl_idname == 'NodeReroute':
            #recursive function to override reroutes
            output_socket, output_node = get_output_socket_id(link.from_socket)
            if output_socket:
                sv_link = SvLink(
                    from_node_id=output_node,
                    to_node_id=link.to_socket.node.node_id,
                    from_socket_id=output_socket,
                    to_socket_id=link.to_socket.socket_id )
                new_sv_links.append(sv_link)

    return new_sv_links


def fill_links_memory(node_tree):
    tree_id = node_tree.tree_id
    new_sv_links = bl_links_to_sv_links(node_tree)

    inputted_nodes, input_sockets, output_sockets = split_new_links_data(new_sv_links)

    sv_links_cache[tree_id] = new_sv_links
    sv_linked_output_sockets_cache[tree_id] = output_sockets
    sv_linked_input_sockets_cache[tree_id] = input_sockets
    sv_linked_inputted_nodes_cache[tree_id] = inputted_nodes


def get_affected_groups(node_tree):
    affected_groups = []
    for node in node_tree.nodes:
        if 'SvGroupNode' in node.bl_idname:
            subtree = node.monad
            tree_id = subtree.tree_id
            fill_memory_is_ready = tree_id in sv_links_cache
            if fill_memory_is_ready:
                has_been_updated = use_link_memory(subtree)
            else:
                fill_links_memory(subtree)
                subtree.has_changed = True
                node.process()
                has_been_updated = True

            if has_been_updated:
                affected_groups.append(node)
    return affected_groups


def use_link_memory(node_tree):
    if node_tree.configuring_new_node or node_tree.is_frozen() or not node_tree.sv_process:
        return False

    tree_id = node_tree.tree_id
    new_sv_links = bl_links_to_sv_links(node_tree)
    before_sv_links = sv_links_cache[tree_id]
    links_has_changed = before_sv_links != new_sv_links

    if links_has_changed:

        affected_nodes = []

        new_inputted_nodes, new_input_sockets, new_output_sockets = split_new_links_data(new_sv_links)
        before_input_sockets = sv_linked_input_sockets_cache[tree_id]
        before_inputted_nodes = sv_linked_inputted_nodes_cache[tree_id]
        before_output_sockets = sv_linked_output_sockets_cache[tree_id]

        new_linked_nodes = get_new_linked_nodes(
            new_sv_links,
            before_sv_links,
            before_output_sockets)

        new_unlinked_linked_nodes = get_new_unlinked_nodes(
            before_inputted_nodes,
            before_input_sockets,
            new_input_sockets,
            dict_of_node_tree(node_tree)
            )
        affected_nodes = new_linked_nodes + new_unlinked_linked_nodes

        sv_links_cache[tree_id] = new_sv_links
        sv_linked_inputted_nodes_cache[tree_id] = new_inputted_nodes
        sv_linked_output_sockets_cache[tree_id] = new_output_sockets
        sv_linked_input_sockets_cache[tree_id] = new_input_sockets

        build_update_list(node_tree)

        if affected_nodes:
            node_list = translate_node_id_to_node_name(node_tree, affected_nodes)
            process_from_nodes(node_list)
            return True
        else:
            return False
    else:

        affected_groups = get_affected_groups(node_tree)
        if affected_groups:
            process_from_nodes(affected_groups)
            return True
        else:
            return False
