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


class DataGetter:

    def __init__(self, socket):
        self.socket = socket

    def get(self):
        return socket.data

class SvDataTree:
    def __init__(self, socket):
        self.data = []
        self.children =[]
        self.socket = socket

    @property
    def is_leaf(self):
        return bool(self.data)

    def parse(self, node_func):
        if self.is_leaf:
            node_func
        for child in children:
            res = child.execute(node_func)

    def __iter__(self):
        return self

    def __next__(self):
        if self.is_leaf:
            yield data
        else:
            for child in children:
                yield child.__next__()

    def set_level(self, level=0):
        self.level = level
        for child in children:
            child.set_level(level + 1)






def compile_node(node):
    def f(*args):
        for idx, arg in enumerate(args):
            socket = node.inputs[idx]
            if socket.is_linked:
                socket.other.sv_set([[arg]])
            else:
                setattr(node, socket.prop_name, arg)
        node.process()
        data = []
        for socket in node.outputs:
            if socket.is_linked:
                data.append(socket.other.sv_get()[0])
            else:
                data.append(None)
        return tuple(data)
    return f
