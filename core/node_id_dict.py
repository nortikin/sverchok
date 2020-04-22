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
    sv_node_dict_cache = {}

    def to_node_name(self, node_tree, affected_nodes):
        tree_id = node_tree.tree_id
        return [self.sv_node_dict_cache[tree_id][node_id] for node_id in affected_nodes if node_id in self.sv_node_dict_cache[tree_id]]

    def load_node(self, node):

        n_id = node.node_id
        tree_id = node.id_data.tree_id

        if tree_id not in self.sv_node_dict_cache:
            self.sv_node_dict_cache[tree_id] = {}
        self.sv_node_dict_cache[tree_id][n_id] = node

    def forget_node(self, node):
        n_id = node.node_id
        tree_id = node.id_data.tree_id
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
