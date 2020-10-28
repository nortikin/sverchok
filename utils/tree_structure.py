# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from collections import Mapping
from typing import List, Iterable

import bpy

import sverchok.utils.tree_walk as tw


class Tree(tw.Tree):
    """
    Structure similar to blender node groups but is more efficient in searching neighbours
    Each time when nodes or links collections are changed the instance of the tree should be recreated
    so it is immutable data structure
    """
    def __init__(self, bl_tree: bpy.types.NodeTree):
        self._nodes = NodesCollection(bl_tree)
        self._links = LinksCollection(bl_tree, self)

    @property
    def nodes(self) -> NodesCollection:
        return self._nodes

    @property
    def links(self) -> LinksCollection:
        return self._links


class TreeCollections(Mapping):
    """
    The idea of this collection is to have access to its elements by their identifier
    and meantime to have access to their indexes of true blender collections
    so to get fast mapping between python and blender collections
    downside is that this collection is immutable
    because it impossible to predict order of Blender collection after changing of their content
    """
    def __init__(self):
        self._dict = dict()

    def __getitem__(self, item):
        return self._dict[item]

    def __iter__(self):
        return iter(self._dict.values())

    def __len__(self):
        return len(self._dict)

    def __contains__(self, item):
        return item in self._dict


class NodesCollection(TreeCollections):
    def __init__(self, bl_tree: bpy.types.NodeTree):
        super().__init__()
        for i, bl_node in enumerate(bl_tree.nodes):
            self._dict[bl_node.name] = Node.from_bl_node(bl_node, i)


class LinksCollection(TreeCollections):
    def __init__(self, bl_tree: bpy.types.NodeTree, tree: Tree):
        super().__init__()
        for i, bl_link in enumerate(bl_tree.links):
            from_node = tree.nodes[bl_link.from_node.name]
            from_socket = from_node.get_output_socket(bl_link.from_socket.identifier)
            to_node = tree.nodes[bl_link.to_node.name]
            to_socket = to_node.get_input_socket(bl_link.to_socket.identifier)

            self._dict[(bl_link.from_node.name, bl_link.from_socket.identifier,
                        bl_link.to_node.name, bl_link.to_socket.identifier)] = Link(from_socket, to_socket, i)


class Node(tw.Node):
    def __init__(self, name: str, index: int):
        self.name = name
        self.select = False  # todo consider to remove
        self._inputs = []
        self._outputs = []
        self._index = index

    @property
    def index(self):
        """Index of node location in Blender collection from which it was copied"""
        return self._index

    @property
    def inputs(self) -> list:
        return self._inputs

    @property
    def outputs(self) -> list:
        return self._outputs

    @property
    def next_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node output sockets"""
        return {other_s.node for s in self.outputs for other_s in s.linked_sockets}

    @property
    def last_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node input sockets"""
        return {other_s.node for s in self.inputs for other_s in s.linked_sockets}

    def get_bl_node(self, tree: bpy.types.NodeTree, by_name=True) -> bpy.types.Node:
        """
        Will return the node from given tree with the same name
        if by_name is False it will use node index instead what will be faster
        """
        return tree.nodes[self.name if by_name else self.index]

    def get_input_socket(self, identifier: str) -> Socket:
        """Search input socket by its identifier"""
        for socket in self._inputs:
            if socket.identifier == identifier:
                return socket
        raise LookupError(f'Socket "{identifier}" was not found in node"{self.name}" inputs{self._inputs}')

    def get_output_socket(self, identifier: str) -> Socket:
        """Search output socket by its identifier"""
        for socket in self._outputs:
            if socket.identifier == identifier:
                return socket
        raise LookupError(f'Socket "{identifier}" was not found in Node "{self.name}" outputs{self._outputs}')

    @classmethod
    def from_bl_node(cls, bl_node: bpy.types.Node, index: int) -> Node:
        """Generate node and its sockets from Blender node instance"""
        node = cls(bl_node.name, index)
        node.select = bl_node.select
        for in_socket in bl_node.inputs:
            node.inputs.append(Socket.from_bl_socket(node, in_socket))
        for out_socket in bl_node.outputs:
            node.outputs.append(Socket.from_bl_socket(node, out_socket))
        return node

    def __repr__(self):
        return f'Node:"{self.name}"'


class Socket:
    def __init__(self, node: Node, is_output: bool, identifier: str):
        self.is_output = is_output
        self.identifier = identifier
        self._node = node
        self._links = []

    @property
    def index(self) -> int:
        """Index of the node in inputs or outputs collection"""
        return getattr(self.node, 'outputs' if self.is_output else 'inputs').index(self)

    @property
    def node(self) -> Node:
        return self._node

    @property
    def links(self) -> list:
        return self._links

    def get_bl_socket(self, bl_tree: bpy.types.NodeTree) -> bpy.types.NodeSocket:
        """Search socket in given tree by its identifier"""
        bl_node = self.node.get_bl_node(bl_tree)
        for bl_socket in bl_node.outputs if self.is_output else bl_node.inputs:
            if bl_socket.identifier == self.identifier:
                return bl_socket
        raise LookupError(f'Socket "{self.identifier}" was not found in Node "{bl_node.name}"'
                          f'in {"outputs" if self.is_output else "inputs"} sockets:'
                          f'"{[s.identefier for s in (bl_node.outputs if self.is_output else bl_node.inputs)]}"')

    @property
    def linked_sockets(self) -> List[Socket]:
        """All sockets which share the same links"""
        return [link.to_socket if self.is_output else link.from_socket for link in self.links]

    @classmethod
    def from_bl_socket(cls, node: Node, bl_socket: bpy.types.NodeSocket) -> Socket:
        """Generate socket from Blender socket instance"""
        return cls(node, bl_socket.is_output, bl_socket.identifier)

    def __repr__(self):
        return f'Socket "{self.identifier}"'


class Link:
    def __init__(self, from_socket: Socket, to_socket: Socket, index: int):
        self.from_socket = from_socket
        self.to_socket = to_socket
        from_socket.links.append(self)
        to_socket.links.append(self)

        self._index = index

    @property
    def index(self):
        """Index of the link location in Blender collection from which it was copied"""
        return self._index

    @property
    def from_node(self) -> Node:
        return self.from_socket.node

    @property
    def to_node(self) -> Node:
        return self.to_socket.node

    def __repr__(self):
        return f'FROM "{self.from_node.name}.{self.from_socket.identifier}" ' \
               f'TO "{self.to_node.name}.{self.to_socket.identifier}"'
