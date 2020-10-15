# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from collections import deque
from itertools import count
from typing import Dict, Tuple, List, Iterable, Generator

import bpy


class Tree:
    """Structure similar to blender node groups but is more efficient in searching neighbours"""
    def __init__(self):
        self._nodes: Dict[str, Node] = {}
        self._links: Dict[Tuple[str, str]: Link] = {}  # Tuple[node_name, identifier]

    @property
    def nodes(self) -> Dict[str, Node]:
        return self._nodes

    @property
    def links(self) -> Dict[Tuple[str, int]: Link]:
        return self._links

    @classmethod
    def from_bl_tree(cls, bl_tree: bpy.types.NodeTree) -> Tree:
        tree = cls()
        for bl_node in bl_tree.nodes:
            tree.nodes[bl_node.name] = Node.from_bl_node(bl_node)
        for bl_link in bl_tree.links:
            from_node = tree.nodes[bl_link.from_node.name]
            from_socket = from_node.get_output_socket(bl_link.from_socket.identifier)
            to_node = tree.nodes[bl_link.to_node.name]
            to_socket = to_node.get_input_socket(bl_link.to_socket.identifier)
            tree.links[(bl_link.to_node.name, bl_link.to_socket.identifier)] = Link(from_socket, to_socket)
        return tree


class Node:
    def __init__(self, name: str):
        self.name = name
        self.select = False
        self._inputs = []
        self._outputs = []

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

    def bfs_walk(self) -> Generator[Node]:
        """Forward walk from the current node, it will visit all next nodes"""
        # https://en.wikipedia.org/wiki/Tree_traversal#Breadth-first_search
        waiting_nodes = deque([self])
        safe_counter = count()
        max_node_number = 2000
        while waiting_nodes:
            node = waiting_nodes.popleft()
            waiting_nodes.extend(node.next_nodes)
            yield node

            if next(safe_counter) > max_node_number:
                raise RecursionError(f'The tree has either more then={max_node_number} nodes '
                                     f'or most likely it is circular')

    def get_bl_node(self, tree: bpy.types.NodeTree) -> bpy.types.Node:
        """
        Will return the node from given tree with the same name
        In future it can be improved and should use index instead of name
        """
        return tree.nodes[self.name]

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
    def from_bl_node(cls, bl_node: bpy.types.Node) -> Node:
        """Generate node and its sockets from Blender node instance"""
        node = cls(bl_node.name)
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
    def __init__(self, from_socket: Socket, to_socket: Socket):
        self.from_socket = from_socket
        self.to_socket = to_socket
        from_socket.links.append(self)
        to_socket.links.append(self)

    @property
    def from_node(self) -> Node:
        return self.from_socket.node

    @property
    def to_node(self) -> Node:
        return self.to_socket.node

    def __repr__(self):
        return f'FROM "{self.from_node.name}.{self.from_socket.identifier}" ' \
               f'TO "{self.to_node.name}.{self.to_socket.identifier}"'
