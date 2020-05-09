# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Union, List, KeysView, Iterable
from operator import getitem

import bpy
from bpy.types import NodeLink

if TYPE_CHECKING:
    # https://stackoverflow.com/questions/39740632/python-type-hinting-without-cyclic-imports
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode

    Node = Union[bpy.types.Node, SverchCustomTreeNode]
    NodeTree = Union[bpy.types.NodeTree, SverchCustomTreeNode]


""" 
This module keeps node and links instances of bpy.types.NodeTree objects
They are available by their IDs
It used for converting nodes of Reconstruction tree to Blender nodes
But also can be used for any other purposes when collection of node_tree.links and node_tree.nodes are unchanged
It is known that keeping such links can lead to Blender crash
So all this data is refreshing if collection of nodes or links was changed
This module can be adopted to getting links of a socket for constant time

Warning: don't use `from` statement for import the module
"""


class HashedBlenderData:
    # keeping data fresh is CurrentEvents class responsibility
    tree_data: Dict[str, HashedTreeData] = dict()

    @classmethod
    def get_node(cls, tree_id: str, node_id: str) -> Node:
        hashed_tree = cls.get_tree(tree_id)
        return hashed_tree.nodes[node_id]

    @classmethod
    def get_link(cls, tree_id: str, link_id: str) -> NodeLink:
        hashed_tree = cls.get_tree(tree_id)
        return hashed_tree.links[link_id]

    @classmethod
    def get_tree(cls, tree_id: str) -> HashedTreeData:
        if tree_id not in cls.tree_data:
            cls.tree_data[tree_id] = HashedTreeData(tree_id)
        return cls.tree_data[tree_id]

    @classmethod
    def reset_data(cls, tree_id: str = None, reset_nodes=True, reset_links=True):
        if tree_id is None:
            cls.tree_data.clear()
        if tree_id in cls.tree_data:
            if reset_nodes:
                cls.tree_data[tree_id].reset_nodes()
            if reset_links:
                cls.tree_data[tree_id].reset_links()


class HashedTreeData:
    def __init__(self, tree_id: str):
        self.tree_id = tree_id

        self.nodes: HashedNodes = HashedNodes(self)
        self.links: HashedLinks = HashedLinks(self)

    def reset_nodes(self):
        self.nodes = HashedNodes(self)

    def reset_links(self):
        self.links = HashedLinks(self)

    def __repr__(self):
        return f"Nodes: {repr(self.nodes)} \n Links: {repr(self.links)}"


class HashedNodes:
    def __init__(self, tree: HashedTreeData):
        self._tree: HashedTreeData = tree
        self._nodes: Dict[str, Node] = dict()

    def __getitem__(self, item: str) -> Node:
        self._memorize_nodes()
        return self._nodes[item]

    def __setitem__(self, key, value):
        self._nodes[key] = value

    def __len__(self):
        return len(get_blender_tree(self._tree.tree_id).nodes)

    def __sub__(self, other) -> List[Node]:
        if hasattr(other, '_nodes'):
            self._memorize_nodes()
            new_nodes_keys = self._nodes.keys() - other._nodes.keys()
            return [getitem(self._nodes, key) for key in new_nodes_keys]
        else:
            return NotImplemented

    def __iter__(self) -> Iterable[Node]:
        return iter(self._nodes.values())

    def __repr__(self):
        return repr(self._nodes)

    def _memorize_nodes(self):
        if not self._nodes:
            tree = get_blender_tree(self._tree.tree_id)
            self._nodes.update({node.node_id: node for node in tree.nodes})


class HashedLinks:
    def __init__(self, tree: HashedTreeData):
        self._tree: HashedTreeData = tree
        self._links: Dict[str, NodeLink] = dict()

    def keys(self) -> KeysView:
        return self._links.keys()

    def __getitem__(self, item: str) -> NodeLink:
        self._memorize_links()
        return self._links[item]

    def __len__(self):
        return len(get_blender_tree(self._tree.tree_id).links)

    def __sub__(self, other) -> List[NodeLink]:
        self._memorize_links()
        if hasattr(other, '_links'):
            new_links_keys = self._links.keys() - other._links.keys()
            return [getitem(self._links, key) for key in new_links_keys]
        elif isinstance(other, set):
            new_links_keys = self._links.keys() - other
            return [getitem(self._links, key) for key in new_links_keys]
        else:
            return NotImplemented

    def __repr__(self):
        return repr(self._links)

    def _memorize_links(self):
        if not self._links:
            tree = get_blender_tree(self._tree.tree_id)
            self._links.update({link.link_id: link for link in tree.links})


def get_blender_tree(tree_id: str) -> NodeTree:
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            ng: SverchCustomTree
            if ng.tree_id == tree_id:
                return ng
    raise LookupError(f"Looks like some node tree has disappeared, or its ID has changed")
