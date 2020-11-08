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
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple, Optional, Iterator

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

    @staticmethod
    def get_error_nodes(group_node: SvGroupTreeNode) -> Iterator[Optional[Exception]]:
        """Return map of bool values to group tree nodes where node has error if value is True"""
        for stat in ContextTree.get_statistic(group_node.node_tree, group_node):
            yield stat.error


class NodeStatistic(NamedTuple):
    """
    Statistic should be kept separately for each node
    because each node can have 10 or even 100 of different statistic profiles according number of group nodes using it
    """
    is_updated: bool = False
    error: Exception = None
    # update_time: int  # ns


class ContextTree(Tree):
    """
    The same tree but nodes has statistic dependently on context evaluation
    For example node can has is_updated=True for tree evaluated from one group node and False for another
    """
    _trees: Dict[str, Tree] = dict()
    _nodes_statistic: Dict[str, NodeStatistic] = defaultdict(NodeStatistic)  # str - sub_node_id

    def __init__(self, bl_tree: SvGroupTree, group_node: SvGroupTreeNode):
        """
        It will create Python copy of the tree and tag already updated nodes


        User should update nodes via node.update method in appropriate order
        """
        self.group_node = group_node

        super().__init__(bl_tree)
        self._replace_nodes_id()  # this should be before copying context node status and nodes updates
        [setattr(n, atr, val) for n in self.nodes
         for atr, val in zip(NodeStatistic.__annotations__, self._nodes_statistic[n.bl_tween.node_id])]
        self._update_topology_status()  # this should be after copying context nodes status
        self._trees[bl_tree.tree_id] = self  # this should be after topology changes chek

    def update_node(self, node: Node):
        bl_node = node.bl_tween
        node.error = None
        try:
            if bl_node.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
                bl_node.process(self.group_node)
            elif hasattr(bl_node, 'process'):
                bl_node.process()
            node.is_updated = True
        except Exception as e:
            node.error = e
            traceback.print_exc()
        finally:
            self._nodes_statistic[bl_node.node_id] = NodeStatistic(node.is_updated, node.error)

    @classmethod
    def get_statistic(cls, bl_tree: SvGroupTree, group_node: SvGroupTreeNode) -> Iterator[NodeStatistic]:
        tree = cls._trees.get(bl_tree.tree_id)
        if tree is None:
            return
        for bl_n in bl_tree.nodes:
            yield cls._nodes_statistic[cls._generate_sub_node_id(tree.nodes[bl_n.name], group_node)]

    def _update_topology_status(self):
        """Copy nodes status from previous tree"""
        if self.bl_tween.tree_id in self._trees:
            old_tree = self._trees[self.bl_tween.tree_id]

            new_links = self.links - old_tree.links
            for link in new_links:
                link.from_node.is_updated = False
                # link.to_node.is_updated = False  # it will be updated if "from_node" will updated without errors

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
        """
        for node in self.nodes:
            node.bl_tween.n_id = self._generate_sub_node_id(node, self.group_node)

    @staticmethod
    def _generate_sub_node_id(node: Node, group_node: SvGroupTreeNode) -> str:
        """
        format of new nodes ID -> "group_node_id.node_id" ("group_node_id." is replaceable part unlike "node_id")
        but nodes which is not connected with input should not change their ID
        because the result of their process method will be constant between different group nodes
        """
        parsed_id = node.bl_tween.node_id.split('.')
        if len(parsed_id) > 2:
            raise TypeError(
                f'Node has wrong format of node_di "{node.bl_tween.node_id}" expecting "tree_id.group_node_id" '
                f'in NODE "{node.bl_tween.name}" of TREE "{node.bl_tween.id_data.name}" '
                f'of GROUP NODE "{group_node.name}"')
        constant_id = parsed_id[-1]
        if node.bl_tween.bl_idname not in OUT_ID_NAMES and node.is_input_linked:
            return group_node.node_id + '.' + constant_id
        else:
            return constant_id


def coroutine(f):  # todo find appropriate module
    @wraps(f)
    def wrap(*args, **kwargs):
        cr = f(*args, **kwargs)
        cr.send(None)
        return cr
    return wrap


# also IDs for this nodes are unchanged for now
OUT_ID_NAMES = {'SvDebugPrintNode', 'SvStethoscopeNodeMK2'}  # todo replace by checking of OutNode mixin class


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
                        if node.error is None:
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
                out_nodes = [n for n in tree.nodes if n.bl_tween.bl_idname in OUT_ID_NAMES]
                out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
                for node in tree.sorted_walk(out_nodes):
                    if not node.is_updated:
                        if node is tree.nodes.active_output:
                            event.output_was_changed = True
                        tree.update_node(node)
                        if node.error is None:
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
                out_nodes = [n for n in tree.nodes if n.bl_tween.bl_idname in OUT_ID_NAMES]
                out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
                for node in tree.sorted_walk(out_nodes):
                    if not node.is_updated or node.name in outdated_nodes:
                        if node is tree.nodes.active_output:
                            event.output_was_changed = True
                        tree.update_node(node)
                        if node.error is None:
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
