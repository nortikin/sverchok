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
from typing import Union, List, TYPE_CHECKING

from bpy.types import Node

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTreeNode, SverchCustomTree as SvTree
    SvNode = Union[SverchCustomTreeNode, SvGroupTreeNode, Node]


class TreeEvent:
    """Keeps information about what was changed during the even"""
    # task should be run via timer only https://developer.blender.org/T82318#1053877
    tree: SvTree

    def __init__(self, tree):
        self.tree = tree

    def __repr__(self):
        return f"<{type(self).__name__} {self.tree.name=}>"


class ForceEvent(TreeEvent):
    pass


class AnimationEvent(TreeEvent):
    is_frame_changed: bool
    is_animation_playing: bool

    def __init__(self, tree, is_frame_change, is_animation_laying):
        super().__init__(tree)
        self.is_frame_changed = is_frame_change
        self.is_animation_playing = is_animation_laying


class SceneEvent(TreeEvent):
    pass


class PropertyEvent(TreeEvent):
    updated_nodes: Iterable[SvNode]

    def __init__(self, tree, updated_nodes):
        super().__init__(tree)
        self.updated_nodes = updated_nodes


class FileEvent:
    pass


class _TreeEvent:  # todo to remove
    TREE_UPDATE = 'tree_update'  # some changed in a tree topology
    NODES_UPDATE = 'nodes_update'  # changes in node properties, update animated nodes
    FORCE_UPDATE = 'force_update'  # rebuild tree and reevaluate every node
    FRAME_CHANGE = 'frame_change'  # unlike other updates this one should be un-cancellable
    SCENE_UPDATE = 'scene_update'  # something was changed in the scene
    FILE_RELOADED = 'file_reloaded'  # New files was opened

    def __init__(self,
                 event_type: str,
                 tree: SvTree,
                 updated_nodes: Iterable[SvNode] = None,
                 cancel=True,
                 is_frame_changed: bool = True,
                 is_animation_playing: bool = False):
        self.type = event_type
        self.tree = tree
        self.updated_nodes = updated_nodes
        self.cancel = cancel
        self.is_frame_changed = is_frame_changed
        self.is_animation_playing = is_animation_playing

    def __repr__(self):
        return f"<TreeEvent type={self.type}>"


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
