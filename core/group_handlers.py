# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

import traceback
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Generator, ContextManager, Dict, TYPE_CHECKING, Union, List

from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree
from sverchok.utils.logging import debug

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTree
    SvTree = Union[SvGroupTree, SverchCustomTree]


class MainHandler:
    def __init__(self):
        self.handlers = group_node_update(group_tree_update(nodes_update()))

    def send(self, event: GroupEvent):

        # handler should override this if if output node was changed indeed
        # but not when update call was created by paren tree
        event.output_was_changed = False

        self.handlers.send(event)
        if event.output_was_changed:
            pass_running(event.bl_tree)


class NodesStatus:
    _trees: Dict[str, Tree] = dict()

    @classmethod
    @contextmanager
    def update_tree_nodes(cls, bl_tree: SvGroupTree) -> ContextManager[Tree]:
        """
        It will create Python copy of the tree and tag already updated nodes
        User should update nodes via node.update method in appropriate order
        After all updated tree will be catch in memory
        """
        new_tree = Tree(bl_tree)
        if bl_tree.tree_id in cls._trees:
            # copy nodes status from previous tree
            old_tree = cls._trees[bl_tree.tree_id]
            [setattr(new_tree.nodes[on.name], 'is_updated', on.is_updated)
             for on in old_tree.nodes if on in new_tree.nodes]

            new_links = new_tree.links - old_tree.links
            for link in new_links:
                link.from_node.is_updated = False
                link.to_node.is_updated = False

            removed_links = old_tree.links - new_tree.links
            for link in removed_links:
                if link.from_node in new_tree.nodes:
                    new_tree.nodes[link.from_node.name].is_updated = False
                if link.to_node in new_tree.nodes:
                    new_tree.nodes[link.to_node.name].is_updated = False
        try:
            yield new_tree
        finally:
            if new_tree is not None:
                cls._trees[bl_tree.tree_id] = new_tree


def coroutine(f):  # todo find appropriate module
    @wraps(f)
    def wrap(*args, **kwargs):
        cr = f(*args, **kwargs)
        cr.send(None)
        return cr
    return wrap


@coroutine
def group_node_update(next_handler=None) -> Generator[None, GroupEvent, None]:
    """
    This node is working when group tree was called to update outside
    But it also assuming that kept status of nodes can be outdated
    """
    while True:
        event: GroupEvent
        event = yield  # this variable can't have annotations here - syntax error
        if event.type == GroupEvent.GROUP_NODE_UPDATE:

            with print_errors():
                debug(event)
                with NodesStatus.update_tree_nodes(event.bl_tree) as tree:
                    if tree.nodes.active_input:
                        tree.nodes.active_input.is_updated = False
                    for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                        if not node.is_updated:
                            node.update(event.call_paths[0])
                            [setattr(n, 'is_updated', False) for n in node.next_nodes]

        else:
            if next_handler:
                next_handler.send(event)


@coroutine
def group_tree_update(next_handler=None):
    """
    Update tree if collection of links or nodes was changed
    update should be done carefully only of outdated nodes
    after tree update running should be passed to parent group nodes
    """
    while True:
        event: GroupEvent
        event = yield
        if event.type == GroupEvent.GROUP_TREE_UPDATE:

            with print_errors():
                debug(event)
                with NodesStatus.update_tree_nodes(event.bl_tree) as tree:
                    from_input_nodes = {n for n in tree.bfs_walk(
                        [n for n in tree.nodes if n.bl_tween.bl_idname == 'NodeGroupInput'])}
                    for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                        if not node.is_updated:
                            if node.is_output:
                                event.output_was_changed = True
                            if node in from_input_nodes:
                                # this nodes should be updated several times for each group node separately
                                for path in event.call_paths:
                                    node.update(path)
                            else:
                                # otherwise one update will be enough
                                node.update()
                            [setattr(n, 'is_updated', False) for n in node.next_nodes]

        else:
            if next_handler:
                next_handler.send(event)


@coroutine
def nodes_update(next_handler=None):
    """
    It will update given via event object nodes
    """
    while True:
        event: GroupEvent
        event = yield
        if event.type == GroupEvent.NODES_UPDATE:

            with print_errors():
                debug(event)
                with NodesStatus.update_tree_nodes(event.bl_tree) as tree:
                    outdated_nodes = set(event.updated_nodes)
                    from_input_nodes = {n for n in tree.bfs_walk(
                        [n for n in tree.nodes if n.bl_tween.bl_idname == 'NodeGroupInput'])}
                    for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                        if not node.is_updated or node.name in outdated_nodes:
                            if node.is_output:
                                event.output_was_changed = True
                            if node in from_input_nodes:
                                # this nodes should be updated several times for each group node separately
                                for path in event.call_paths:
                                    node.update(path)
                            else:
                                # otherwise one update will be enough
                                node.update()
                            [setattr(n, 'is_updated', False) for n in node.next_nodes]

        else:
            if next_handler:
                next_handler.send(event)


def pass_running(from_tree: SvGroupTree):
    """
    It asks update group nodes of upper trees
    there could be several group nodes in one tree and group nodes can be in multiple trees as well
    thous nodes also should be update only if output data was changed

    this function can't be called from generator chain otherwise if in parent tree there is another group node
    it will raise "ValueError: generator already executing"
    """
    trees_to_nodes: Dict[SvTree, List[SvGroupTreeNode]] = defaultdict(list)
    for node in from_tree.parent_nodes():
        trees_to_nodes[node.id_data].append(node)

    for sv_tree, nodes in trees_to_nodes.items():
        try:
            [n.toggle_active(False) for n in nodes]
            sv_tree.update_nodes(nodes)
        except Exception as e:
            print(e)
        finally:
            [n.toggle_active(True, to_update=False) for n in nodes]


@contextmanager
def print_errors():
    try:
        yield None
    except Exception:
        traceback.print_exc()
