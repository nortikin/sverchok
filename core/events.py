# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Events keep information about which Blender trigger was executed and with which
context
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Union, TYPE_CHECKING

from bpy.types import Node

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree as GrTree, \
        SvGroupTreeNode as GrNode
    from sverchok.node_tree import SverchCustomTreeNode, SverchCustomTree as SvTree
    SvNode = Union[SverchCustomTreeNode, GrNode, Node]


class TreeEvent:
    """Adding removing nodes or links but not necessarily"""
    # the event should be run via timer only https://developer.blender.org/T82318#1053877
    tree: SvTree

    def __init__(self, tree):
        self.tree = tree

    def __repr__(self):
        return f"<{type(self).__name__} {self.tree.name=}>"


class ForceEvent(TreeEvent):
    """Indicates the whole tree should be recalculated"""
    pass


class AnimationEvent(TreeEvent):
    """Frame was changed. Last event can be with the same frame"""
    is_frame_changed: bool
    is_animation_playing: bool

    def __init__(self, tree, is_frame_change, is_animation_laying):
        super().__init__(tree)
        self.is_frame_changed = is_frame_change
        self.is_animation_playing = is_animation_laying


class SceneEvent(TreeEvent):
    """Something was changed in the scene"""
    pass


class PropertyEvent(TreeEvent):
    """Property of the node(s) was changed"""
    updated_nodes: Iterable[SvNode]

    def __init__(self, tree, updated_nodes):
        super().__init__(tree)
        self.updated_nodes = updated_nodes


class GroupTreeEvent(TreeEvent):
    """The same as Tree event but inside a group tree"""
    tree: GrTree
    update_path: list[GrNode]

    def __init__(self, tree, update_path):
        super().__init__(tree)
        self.update_path = update_path


class NewGroupTreeEvent(GroupTreeEvent):
    """It should be called when to update newly created group tree
    because when it was created parent tree also was changed
    and should be refreshed"""
    parent_tree: Union[SvTree, GrTree]

    def __init__(self, tree, update_path, parent_tree):
        super().__init__(tree, update_path)
        self.parent_tree = parent_tree


class GroupPropertyEvent(GroupTreeEvent):
    """Property of a node(s) inside a group tree was changed"""
    updated_nodes: Iterable[SvNode]

    def __init__(self, tree, update_path, update_nodes):
        super().__init__(tree, update_path)
        self.updated_nodes = update_nodes


class FileEvent:
    """It indicates that new file was loaded"""
    pass


class UndoEvent:
    """Undo handler was executed"""


class TreesGraphEvent:
    """It indicates that something was changed in trees relations defined via
    group nodes"""
    pass
