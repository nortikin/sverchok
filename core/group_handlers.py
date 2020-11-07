# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Purpose of this module is calling `process` methods of nodes in appropriate order according their relations in a tree
and keeping `updating` statistics.
"""

from __future__ import annotations

import traceback
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple

from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree, Node
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


class NodeStatistic(NamedTuple):
    """
    Statistic should be kept separately for each node
    because each node can have 10 or even 100 of different statistic profiles according number of group nodes using it
    """
    is_update: bool = False
    # has_error: bool = False
    # update_time: int  # ns


class ContextTree(Tree):
    """
    The same tree but nodes has statistic dependently on context evaluation
    For example node can has is_updated=True for tree evaluated from one group node and False for another
    """
    _trees: Dict[str, Tree] = dict()
    _nodes_statistic: Dict[str, NodeStatistic] = defaultdict(NodeStatistic)  # str - node_id

    def __init__(self, bl_tree: SvGroupTree, group_node: SvGroupTreeNode):
        """
        It will create Python copy of the tree and tag already updated nodes


        User should update nodes via node.update method in appropriate order
        """
        self.group_node = group_node

        super().__init__(bl_tree)
        self._trees[bl_tree.tree_id] = self
        self._replace_nodes_id()
        [setattr(n, atr, val) for n in self.nodes
         for atr, val in zip(NodeStatistic.__annotations__, self._nodes_statistic[n.bl_tween.node_id])]
        self._update_topology_status()

    def update_node(self, node: Node):
        bl_node = node.bl_tween
        was_updated = False
        has_error = False
        try:
            if bl_node.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
                bl_node.process(self.group_node)
            elif hasattr(bl_node, 'process'):
                bl_node.process()
            was_updated = True
        except Exception:
            has_error = True
            traceback.print_exc()
        finally:
            self._nodes_statistic[bl_node.node_id] = NodeStatistic(was_updated)

    def _update_topology_status(self):
        """Copy nodes status from previous tree"""
        if self.bl_tween.tree_id in self._trees:
            old_tree = self._trees[self.bl_tween.tree_id]

            new_links = self.links - old_tree.links
            for link in new_links:
                link.from_node.is_updated = False
                link.to_node.is_updated = False

            removed_links = old_tree.links - self.links
            for link in removed_links:
                if link.from_node in self.nodes:
                    self.nodes[link.from_node.name].is_updated = False
                if link.to_node in self.nodes:
                    self.nodes[link.to_node.name].is_updated = False

    def _replace_nodes_id(self):
        """
        The idea is to replace nodes ID before evaluating the tree
        in this case sockets will get unique identifiers relative to base group node
        format of new nodes ID -> "group_node_id.node_id" ("group_node_id." is replaceable part unlike "node_id")
        but nodes which is not connected with input should not change their ID
        because the result of their process method will be constant between different group nodes
        """
        from_input_nodes = {n for n in self.bfs_walk(
            [n for n in self.nodes if n.bl_tween.bl_idname == 'NodeGroupInput'])}
        for node in self.nodes:
            parsed_id = node.bl_tween.node_id.split('.')
            if len(parsed_id) > 2:
                raise TypeError(f'Wrong format of node_di "{node.bl_tween.node_id}" expecting "tree_id.group_node_id" '
                                f'in NODE "{node.name}" of TREE "{node.bl_tween.id_data.name}"')
            constant_id = parsed_id[-1]
            if node in from_input_nodes:
                node.bl_tween.n_id = self.group_node.n_id + '.' + constant_id
            else:
                node.bl_tween.n_id = constant_id


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
                tree = ContextTree(event.bl_tree, event.group_node)
                if tree.nodes.active_input:
                    tree.nodes.active_input.is_updated = False
                for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                    if not node.is_updated:
                        tree.update_node(node)
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
                tree = ContextTree(event.bl_tree, event.group_node)
                for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                    if not node.is_updated:
                        if node.is_output:
                            event.output_was_changed = True
                        tree.update_node(node)
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
                tree = ContextTree(event.bl_tree, event.group_node)
                outdated_nodes = set(event.updated_nodes)
                for node in tree.sorted_walk([tree.nodes.active_output] if tree.nodes.active_output else []):
                    if not node.is_updated or node.name in outdated_nodes:
                        if node.is_output:
                            event.output_was_changed = True
                        tree.update_node(node)
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
