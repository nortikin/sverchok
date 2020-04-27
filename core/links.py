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


import collections
from typing import NamedTuple


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


class SvLink(NamedTuple):
    from_node_id: str
    to_node_id: str
    from_socket_id: str
    to_socket_id: str

    @classmethod
    def init_from_link(cls, link):
        output_socket, output_node = get_output_socket_id(link.from_socket)
        sv_link = cls(
            from_node_id=output_node,
            to_node_id=link.to_socket.node.node_id,
            from_socket_id=output_socket,
            to_socket_id=link.to_socket.socket_id )
        return sv_link

    @classmethod
    def init_from_links(cls, links):
        new_sv_links = []
        for link in links:
            if not link.to_socket.node.bl_idname == 'NodeReroute':
                #recursive function to override reroutes
                output_socket, output_node = get_output_socket_id(link.from_socket)
                if output_socket:
                    sv_link = cls(
                        from_node_id=output_node,
                        to_node_id=link.to_socket.node.node_id,
                        from_socket_id=output_socket,
                        to_socket_id=link.to_socket.socket_id )
                    new_sv_links.append(sv_link)

        return new_sv_links

class SvLinks:
    sv_links_new = {}
    sv_links_cache = {}
    output_sockets_cache = {}
    input_sockets_cache = {}
    inputted_nodes_cache = {}
    output_sockets_new = dict()
    input_sockets_new = dict()
    inputted_nodes_new = dict()

    def start_dictionaries(self, tree_id):
        self.sv_links_new[tree_id] = dict()
        self.sv_links_cache[tree_id] = dict()
        self.output_sockets_new[tree_id] = dict()
        self.input_sockets_new[tree_id] = dict()
        self.inputted_nodes_new[tree_id] = dict()
        self.output_sockets_cache[tree_id] = dict()
        self.input_sockets_cache[tree_id] = dict()
        self.inputted_nodes_cache[tree_id] = dict()


    def create_new_links(self, node_tree):
        tree_id = node_tree.tree_id
        if not node_tree.tree_id in self.sv_links_new:
            self.start_dictionaries(node_tree.tree_id)

        new_sv_links = SvLink.init_from_links(node_tree.links)
        self.sv_links_new[tree_id] = new_sv_links
        new_inputted_nodes, new_input_sockets, new_output_sockets = split_new_links_data(new_sv_links)
        self.output_sockets_new[tree_id] = new_output_sockets
        self.input_sockets_new[tree_id] = new_input_sockets
        self.inputted_nodes_new[tree_id] = new_inputted_nodes


    def links_have_changed(self, node_tree):
        return self.sv_links_new[node_tree.tree_id] != self.sv_links_cache[node_tree.tree_id]

    def store_links_cache(self, node_tree):
        tree_id = node_tree.tree_id
        self.sv_links_cache[node_tree.tree_id] = self.sv_links_new[node_tree.tree_id]
        self.output_sockets_cache[tree_id] = self.output_sockets_new[tree_id]
        self.input_sockets_cache[tree_id] = self.input_sockets_new[tree_id]
        self.inputted_nodes_cache[tree_id] = self.inputted_nodes_new[tree_id]

    def get_nodes(self, node_tree):
        tree_id = node_tree.tree_id
        new_sv_links = self.sv_links_new[tree_id]
        before_sv_links = self.sv_links_cache[tree_id]

        if not self.sv_links_cache[tree_id]:
            return node_tree.nodes

        affected_nodes = []

        new_linked_nodes = get_new_linked_nodes(
            new_sv_links,
            before_sv_links,
            self.output_sockets_cache[tree_id])

        new_unlinked_linked_nodes = get_new_unlinked_nodes(
            self.inputted_nodes_cache[tree_id],
            self.input_sockets_cache[tree_id],
            self.input_sockets_new[tree_id],
            node_tree.nodes_dict.get(node_tree)
            )
        affected_nodes = new_linked_nodes + new_unlinked_linked_nodes
        node_list = node_tree.nodes_dict.to_node_name(node_tree, affected_nodes)

        return node_list
