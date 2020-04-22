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

sv_node_dict_cache = {}

def translate_node_id_to_node_name(node_tree, affected_nodes):
    tree_id = node_tree.tree_id
    return [sv_node_dict_cache[tree_id][node_id] for node_id in affected_nodes if node_id in sv_node_dict_cache[tree_id]]

def load_in_node_dict(node):

    n_id = node.node_id
    tree = node.id_data
    tree_id = node.id_data.tree_id

    if tree_id not in sv_node_dict_cache:
        sv_node_dict_cache[tree_id] = {}
    sv_node_dict_cache[tree_id][n_id] = node

def delete_from_node_dict(node):
    n_id = node.node_id
    tree_id = node.id_data.tree_id
    del sv_node_dict_cache[tree_id][n_id]

def load_nodes_in_node_dict(node_tree):
    print('loading_nodes_in_nodetree', node_tree.tree_id)
    tree_id = node_tree.tree_id
    # if tree_id in sv_node_dict_cache:
    sv_node_dict_cache[tree_id] = {}
    for node in node_tree.nodes:
        try:
            sv_node_dict_cache[tree_id][node.node_id] = node
        except AttributeError:
            # it is a NodeReroute
            pass


def dict_of_node_tree(node_tree):
    print(node_tree.tree_id in sv_node_dict_cache)
    if not node_tree.tree_id in sv_node_dict_cache:
        load_nodes_in_node_dict(node_tree)
    return sv_node_dict_cache[node_tree.tree_id]
