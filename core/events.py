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
from typing import Union, TYPE_CHECKING

from bpy.types import Node

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree as GrTree, \
        SvGroupTreeNode as GrNode
    from sverchok.node_tree import SverchCustomTreeNode, SverchCustomTree as SvTree
    SvNode = Union[SverchCustomTreeNode, GrNode, Node]


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


class GroupTreeEvent(TreeEvent):
    tree: GrTree
    update_path: list[GrNode]

    def __init__(self, tree, update_path):
        super().__init__(tree)
        self.update_path = update_path


class GroupPropertyEvent(GroupTreeEvent):
    updated_nodes: Iterable[SvNode]

    def __init__(self, tree, update_path, update_nodes):
        super().__init__(tree, update_path)
        self.updated_nodes = update_nodes


class FileEvent:
    pass


class TreesGraphEvent:
    pass
