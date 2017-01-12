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
from update_system import make_update_list

class SvDataTree:
    def __init__(self, socket):
        self.data = None
        self.children = []
        self.socket = socket

    def add_child(tree):
        self.children.append(tree)


class SvTreeDB:
    def __init__(self):
        self.data_trees = {}

    def get(socket):
        ng_id = socket.id_data.name
        s_id = socket.socket_id
        if ng_id not in self.data_trees:
            self.data_trees[ng_id] = {}
        ng_trees = self.data_trees[ng_id]
        if s_id not in ng_trees:
            ng_trees[s_id] = SvDataTree(socket)
        return ng_trees[s_id]

    def clean(ng):
        ng_id = socket.id_data.name
        self.data_trees[ng_id] = {}


def DAG(node_group):
    yield from make_update_list(node_group):
    
# sketch of execution mechanism
# DAG gives nodes in correct eval order
# data_trees is and interface for storing socket data
# recurse_tree matches data and executes function, while building tree
def exec_node_group(node_group):
    for node in DAG(node_group):
        for socket in node.outputs:
            if socket.is_linked:
                out_trees = data_trees.get(socket)
        func = compile_node(node)
        trees = []
        for socket in node.inputs:
            if socket.is_linked:
                tree = data_trees.get(socket.other)
                trees.append(tree)
        recurse_trees(func, in_trees, out_trees)

def recurse_trees(func, trees):
    if func.is_generator:
        pass
    elif func.is_reducer:
        pass
    elif func.is_output:
        pass
    else:
        pass


def compile_node(node):
    def f(*args):
        for idx, arg in enumerate(args):
            socket = node.inputs[idx]
            if socket.is_linked:
                socket.other.sv_set([[arg]])
            else:
                pass
                #setattr(node, socket.prop_name, arg)
        node.process()
        data = {}
        for socket in node.outputs:
            if socket.is_linked:
                data[socket.name] = socket.other.sv_get()[0]
            else:
                data[socket.name] = None
        return data
    return f
