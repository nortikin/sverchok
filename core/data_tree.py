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
import time
from itertools import chain, filterfalse
import collections

from sverchok.core.update_system import make_update_list

# from itertools, should be somewhere else...
def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element


def recurse_generator(f, trees, out_trees, level=0):
    if all(tree.is_leaf for tree in trees):
        args = [tree.data for tree in trees]
        res = f(args)
        if len(out_trees) > 1:
            for out_tree, r in zip(out_trees, res):
                out_tree.data = r
        elif len(out_trees) == 1:
            for r in res[0]:
                sdt = SvDataTree()
                sdt.data = r
                out_trees[0].children.append(sdt)
        else:  # no output
            pass
    else:
        inner_trees = [[tree] if tree.is_leaf else tree.children for tree in trees]
        for i in range(max(map(len, inner_trees))):
            index = [i if i < len(tree) else len(tree) - 1 for tree in inner_trees]
            args = [inner_trees[j][idx] for j, idx in enumerate(index)]
            for out_tree in out_trees:
                out_tree.children.append(SvDataTree())
            recurse_generator(f, args, [out_tree.children[-1] for out_tree in out_trees], level=(level + 1))


def recurse_level(f, trees, out_trees, level=0):
    if all(tree.is_leaf for tree in trees):
        args = [tree.data for tree in trees]
        res = f(args)
        if len(out_trees) > 1:
            for out_tree, r in zip(out_trees, res):
                out_tree.data = r
        elif len(out_trees) == 1:
            out_trees[0] = res[0]
        else:  # no output
            pass
    else:
        inner_trees = [[tree] if tree.is_leaf else tree.children for tree in trees]
        for i in range(max(map(len, inner_trees))):
            index = [i if i < len(tree) else len(tree) - 1 for tree in inner_trees]
            args = [inner_trees[j][idx] for j, idx in enumerate(index)]
            for out_tree in out_trees:
                out_tree.children.append(SvDataTree())
            recurse_generator(f, args, [out_tree.children[-1] for out_tree in out_trees], level=(level + 1))

def recurse_reduce(f, trees, out_trees, level=0):
    if all(not tree.is_leaf and tree.children[0].is_leaf for tree in trees):
        args = [list(tree) for tree in trees]
        res = f(args)
        if len(out_trees) > 1:
            for out_tree, r in zip(out_trees, res):
                out_tree.data = r
        elif len(out_trees) == 1:
            out_trees[0] = res[0]
        else:  # no output
            pass
    else:
        inner_trees = [[tree] if tree.is_leaf else tree.children for tree in trees]
        for i in range(max(map(len, inner_trees))):
            index = [i if i < len(tree) else len(tree) - 1 for tree in inner_trees]
            args = [inner_trees[j][idx] for j, idx in enumerate(index)]
            for out_tree in out_trees:
                out_tree.children.append(SvDataTree())
            recurse_generator(f, args, [out_tree.children[-1] for out_tree in out_trees], level=(level + 1))



def recurse_stateful(f, in_trees, out_trees, level=0):
    args = [list(in_tree) for in_tree in in_trees]
    res = f(args)
    for r, out_tree in zip(res, out_trees):
        out_tree.data = r

timings = []

def compile_node(node):
    def f(args):
        for idx, arg in enumerate(args):
            socket = node.inputs[idx]
            if socket.is_linked:
                #print(node.name, "arg inside exec node", arg)
                socket.other.sv_set([arg])
            else:
                pass
                """
                not needed inside of Sverchok context
                setattr(node, socket.prop_name, arg)
                """
        start = time.perf_counter()
        node.process()
        stop = time.perf_counter()
        timings.append((node.bl_idname, node.name, stop - start))
        data = []
        for socket in node.outputs:
            if socket.is_linked:
                d = socket.other.sv_get()
                #print(node.name, "result", socket.name, d)
                data.append(d)

        #print(node.name, "total result", data)
        return data
    return f, node_database.get(node.bl_idname, recurse_generator)

class SvDataTree:
    def __init__(self, socket=None):
        self.data = None
        self.children = []
        if socket:
            self.name = socket.node.name + ": " + socket.name
        else:
            self.name = None

    @property
    def is_leaf(self):
        return self.data is not None

    def __repr__(self):
        if self.is_leaf:
            return "SvDataTree<{}>".format(self.data)
        else:
            return "SvDataTree<children={}>".format(len(self.children))

    def print(self, level=0):
        if self.name:
            print(self.name)
        if self.is_leaf:
            print(level * "    ", self.data)
        else:
            for child in self.children:
                child.print(level + 1)

    def __iter__(self):
        if self.is_leaf:
            yield self.data
        else:
            for v in chain(map(iter, self.children)):
                yield from v

    def set_level(self, level=0):
        self.level = level
        if self.is_leaf:
            return level
        else:
            for child in self.children:
                child.set_level(level + 1)

    def get_level(self):
        if self.is_leaf:
            return 1
        else:
            return 1 + self.children[0].get_level()


class SvDummyTree:
    is_leaf = True
    data = None

    def __iter__(self):
        yield None

    children = []

class SvTreeDB:
    def __init__(self):
        self.data_trees = {}

    def print(self, ng):
        for link in ng.links:
            self.get(link.from_socket).print()

    def get(self, socket):
        ng_id = socket.id_data.name
        s_id = socket.socket_id
        if ng_id not in self.data_trees:
            self.data_trees[ng_id] = {}
        ng_trees = self.data_trees[ng_id]
        if s_id not in ng_trees:
            ng_trees[s_id] = SvDataTree(socket)
        return ng_trees[s_id]

    def clean(self, ng):
        ng_id = ng.name
        self.data_trees[ng_id] = {}

data_trees = SvTreeDB()


def DAG(node_group):
    print(make_update_list(node_group))
    for name in make_update_list(node_group):
        yield node_group.nodes[name]

#  sketch of execution mechanism
#  DAG gives nodes in correct eval order
#  data_trees is and interface for storing socket data
#  recurse_tree matches data and executes function, while building tree


def exec_node_group(node_group):
    print("exec tree")
    data_trees.clean(node_group)
    timings.clear()
    for node in DAG(node_group):
        print("exec node", node.name)
        func, recurse = compile_node(node)
        out_trees = []
        in_trees = []
        for socket in node.inputs:
            if socket.is_linked:
                tree = data_trees.get(socket.other)
                in_trees.append(tree)
            else:
                in_trees.append(SvDummyTree())
        for socket in node.outputs:
            if socket.is_linked:
                out_trees.append(data_trees.get(socket))

        recurse(func, in_trees, out_trees)
        for ot in out_trees:
            ot.set_level()
            print(ot.name, ot.get_level())

    def f():
        return [0, 0]

    times = collections.defaultdict(lambda : [0, 0])
    for _, name, t in timings:
        times[name][1] += t
        times[name][0] += 1

    for name in unique_everseen(name for _, name, t in timings):
        print(name, "called {} times in {:.3}".format(*times[name]))

# this needs something more clever
node_database = {
    "SvCircleNode": recurse_reduce,
    "GenListRangeIntNode": recurse_generator,
    "LineConnectNodeMK2": recurse_reduce,
    "ViewerNode2": recurse_stateful,
    "GenVectorsNode": recurse_level,
}
