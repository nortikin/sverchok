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

class SvNodesDict:
    '''
    Class to store a dictionary to find nodes by node_id
    '''
    sv_node_dict_cache = {}

    def to_node_name(self, node_tree, nodes_id):
        tree_id = node_tree.tree_id
        if not node_tree.tree_id in self.sv_node_dict_cache:
            self.load_nodes(node_tree)
        node_dict = self.sv_node_dict_cache[tree_id]
        nodes_name = []
        for node_id in nodes_id:
            if node_id in node_dict:
                nodes_name.append(node_dict[node_id])
        return nodes_name

    def load_node(self, node):

        n_id = node.node_id
        tree_id = node.id_data.tree_id

        if tree_id not in self.sv_node_dict_cache:
            self.sv_node_dict_cache[tree_id] = {}
        self.sv_node_dict_cache[tree_id][n_id] = node

    def forget_node(self, node):
        n_id = node.node_id
        node_tree = node.id_data
        tree_id = node_tree.tree_id
        if not tree_id in self.sv_node_dict_cache:
            self.load_nodes(node_tree)

        if n_id in self.sv_node_dict_cache[tree_id]:
            del self.sv_node_dict_cache[tree_id][n_id]

    def load_nodes(self, node_tree):
        tree_id = node_tree.tree_id
        self.sv_node_dict_cache[tree_id] = {}
        for node in node_tree.nodes:
            try:
                self.sv_node_dict_cache[tree_id][node.node_id] = node
            except AttributeError:
                # it is a NodeReroute
                pass

    def get(self, node_tree):
        if not node_tree.tree_id in self.sv_node_dict_cache:
            self.load_nodes(node_tree)
        return self.sv_node_dict_cache[node_tree.tree_id]
