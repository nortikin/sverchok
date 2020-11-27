# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from __future__ import annotations

from collections import Mapping
from typing import List, Iterable, TypeVar, TYPE_CHECKING, Dict, Any, Generic, Optional, Union

import bpy

import sverchok.utils.tree_walk as tw

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree
    from sverchok.node_tree import SverchCustomTreeNode
    SvNode = Union[SverchCustomTreeNode, bpy.types.Node]


class Node(tw.Node):
    def __init__(self, name: str, index: int, tree: Tree):
        self.name = name
        self.is_input_linked = False  # True if node has straight connection or via other nodes to one of input nodes

        self._inputs: List[Socket] = []
        self._outputs: List[Socket] = []
        self._index = index
        self._tree = tree

        # statistics
        self.is_updated = False
        self.link_changed = False
        self.error = None

    @property
    def bl_tween(self) -> SvNode:
        return self._tree.bl_tween.nodes[self._index]

    @property
    def index(self):
        """Index of node location in Blender collection from which it was copied"""
        return self._index

    @property
    def inputs(self) -> List[Socket]:
        return self._inputs

    @property
    def outputs(self) -> List[Socket]:
        return self._outputs

    @property
    def next_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node output sockets"""
        return {other_s.node for s in self.outputs for other_s in s.linked_sockets}

    @property
    def last_nodes(self) -> Iterable[Node]:
        """Returns all nodes which are linked wia the node input sockets"""
        return {other_s.node for s in self.inputs for other_s in s.linked_sockets}

    def get_bl_node(self, tree: SvGroupTree) -> bpy.types.Node:
        """
        Will return the node from given tree with the same name
        It is slower then `bl_tween` attribute but can return node from another given tree
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
    def from_bl_node(cls, bl_node: bpy.types.Node, index: int, tree: Tree) -> Node:
        """Generate node and its sockets from Blender node instance"""
        node = cls(bl_node.name, index, tree)
        for in_socket in bl_node.inputs:
            node.inputs.append(Socket.from_bl_socket(node, in_socket))
        for out_socket in bl_node.outputs:
            node.outputs.append(Socket.from_bl_socket(node, out_socket))
        return node

    def __repr__(self):
        return f'Node:"{self.name}"'


NodeType = TypeVar('NodeType', bound=Node)


class Tree(tw.Tree[NodeType]):
    """
    Structure similar to blender node groups but is more efficient in searching neighbours
    Each time when nodes or links collections are changed the instance of the tree should be recreated
    so it is immutable (topologically) data structure
    """
    def __init__(self, bl_tree: SvGroupTree):
        self._tree_id = bl_tree.tree_id
        self._nodes = NodesCollection(bl_tree, self)
        self._links = LinksCollection(bl_tree, self)

        for i, tree in enumerate(bpy.data.node_groups):
            if tree.name == bl_tree.name:
                self._index = i
                break

        # topology analyze
        [setattr(n, 'is_input_linked', True) for n in self.bfs_walk(
            [n for n in self.nodes if n.bl_tween.bl_idname == 'NodeGroupInput'])]

    @property
    def id(self) -> str:
        return self._tree_id

    @property
    def bl_tween(self) -> SvGroupTree:
        return bpy.data.node_groups[self._index]

    @property
    def nodes(self) -> NodesCollection:
        return self._nodes

    @property
    def links(self) -> LinksCollection:
        return self._links


Element = TypeVar('Element')


class TreeCollections(Mapping, Generic[Element]):
    """
    The idea of this collection is to have access to its elements by their identifier
    and meantime to have access to their indexes of true blender collections
    so to get fast mapping between python and blender collections
    downside is that this collection is immutable
    because it impossible to predict order of Blender collection after changing of their content
    """
    def __init__(self):
        self._dict: Dict[Any, Element] = dict()

    def __getitem__(self, item) -> Element:
        return self._dict[item]

    def __iter__(self) -> Iterable[Element]:
        return iter(self._dict.values())

    def __len__(self):
        return len(self._dict)

    def __contains__(self, item):
        try:
            return item.name in self._dict
        except AttributeError:
            return item in self._dict

    def __sub__(self, other) -> List[Element]:
        if isinstance(other, TreeCollections):
            return [self._dict[k] for k in (self._dict.keys() - other._dict.keys())]
        else:
            return NotImplemented


class NodesCollection(TreeCollections[NodeType]):
    def __init__(self, bl_tree: SvGroupTree, tree: Tree):
        super().__init__()
        self._active_input: Optional[Node] = None
        self._active_output: Optional[Node] = None
        for i, bl_node in enumerate(bl_tree.nodes):
            node = Node.from_bl_node(bl_node, i, tree)
            self._dict[bl_node.name] = node

            # https://developer.blender.org/T82350
            if bl_node.bl_idname == 'NodeGroupInput':
                self._active_input = node
            if bl_node.bl_idname == 'NodeGroupOutput':
                self._active_output = node

    @property
    def active_input(self) -> Optional[Node]:
        return self._active_input

    @property
    def active_output(self) -> Optional[Node]:
        return self._active_output


class LinksCollection(TreeCollections):
    def __init__(self, bl_tree: SvGroupTree, tree: Tree):
        super().__init__()
        for i, bl_link in enumerate(bl_tree.links):
            from_node = tree.nodes[bl_link.from_node.name]
            from_socket = from_node.get_output_socket(bl_link.from_socket.identifier)
            to_node = tree.nodes[bl_link.to_node.name]
            to_socket = to_node.get_input_socket(bl_link.to_socket.identifier)

            self._dict[(bl_link.from_node.name, bl_link.from_socket.identifier,
                        bl_link.to_node.name, bl_link.to_socket.identifier)] = Link(from_socket, to_socket, i)

    def __iter__(self) -> Iterable[Link]: return super().__iter__()


class Socket:
    def __init__(self, node: Node, is_output: bool, identifier: str):
        self.is_output = is_output
        self.identifier = identifier
        self._node = node
        self._links = []

    @property
    def bl_tween(self) -> bpy.types.NodeSocket:
        return getattr(self._node.bl_tween, 'outputs' if self.is_output else 'inputs')[self.index]

    @property
    def index(self) -> int:
        """Index of the node in inputs or outputs collection"""
        return getattr(self.node, 'outputs' if self.is_output else 'inputs').index(self)

    @property
    def node(self) -> Node:
        return self._node

    @property
    def links(self) -> List[Link]:
        return self._links

    def get_bl_socket(self, bl_tree: SvGroupTree) -> bpy.types.NodeSocket:
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
