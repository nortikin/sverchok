# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Purpose of this module is centralization of update events.

For now it can be used in debug mode for understanding which event method are triggered by Blender
during evaluation of Python code.

Details: https://github.com/nortikin/sverchok/issues/3077
"""

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum, auto
from typing import Union, List, TYPE_CHECKING

from bpy.types import Node

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTreeNode, SverchCustomTree
    SvNode = Union[SverchCustomTreeNode, SvGroupTreeNode, Node]


class TreeEvent:
    TREE_UPDATE = 'tree_update'  # some changed in a tree topology
    NODES_UPDATE = 'nodes_update'  # changes in node properties, update animated nodes
    FORCE_UPDATE = 'force_update'  # rebuild tree and reevaluate every node
    FRAME_CHANGE = 'frame_change'  # unlike other updates this one should be un-cancellable

    def __init__(self, event_type: str, tree: SverchCustomTree, updated_nodes: Iterable[SvNode] = None, cancel=True):
        self.type = event_type
        self.tree = tree
        self.updated_nodes = updated_nodes
        self.cancel = cancel


class GroupEvent:
    GROUP_NODE_UPDATE = 'group_node_update'
    GROUP_TREE_UPDATE = 'group_tree_update'
    NODES_UPDATE = 'nodes_update'
    EDIT_GROUP_NODE = 'edit_group_node'  # upon pressing edit button or Tab

    def __init__(self,
                 event_type: str,
                 group_nodes_path: List[SvGroupTreeNode],
                 updated_nodes: List[SvNode] = None):
        self.type = event_type
        self.group_node = group_nodes_path[-1]
        self.group_nodes_path = group_nodes_path
        self.updated_nodes = updated_nodes
        self.to_update = group_nodes_path[-1].is_active

    @property
    def tree(self) -> SvGroupTree:
        return self.group_node.node_tree

    def __repr__(self):
        return f'{self.type.upper()} event, GROUP_NODE={self.group_node.name}, TREE={self.tree.name}' \
               + (f', NODES={self.updated_nodes}' if self.updated_nodes else '')


class BlenderEventsTypes(Enum):
    tree_update = auto()  # this updates is calling last with exception of creating new node
    node_update = auto()  # it can be called last during creation new node event
    add_node = auto()   # it is called first in update wave
    copy_node = auto()  # it is called first in update wave
    free_node = auto()  # it is called first in update wave
    add_link_to_node = auto()  # it can detects only manually created links
    node_property_update = auto()  # can be in correct in current implementation
    undo = auto()  # changes in tree does not call any other update events
    frame_change = auto()

    def print(self, updated_element=None):
        event_name = f"EVENT: {self.name: <30}"
        if updated_element is not None:
            element_data = f"IN: {updated_element.bl_idname: <25} INSTANCE: {updated_element.name: <25}"
        else:
            element_data = ""
        print(event_name + element_data)
