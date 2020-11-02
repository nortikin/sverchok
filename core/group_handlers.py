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

import bpy
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
        self.handlers.send(event)


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
                    [setattr(n, 'is_updated', False) for n in tree.nodes if n.bl_tween.bl_idname == 'NodeGroupInput']
                    for node in tree.sorted_walk(
                            [n for n in tree.output_nodes if n.bl_tween.bl_idname == 'NodeGroupOutput']):
                        if not node.is_updated:
                            if node.bl_tween.bl_idname == 'NodeGroupInput':  # already updated by triggered group node
                                node.is_updated = True
                            else:
                                node.update()
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
                    output_was_changed = False  # optimisation
                    for node in tree.sorted_walk(
                            [n for n in tree.output_nodes if n.bl_tween.bl_idname == 'NodeGroupOutput']):
                        if not node.is_updated:
                            if node.is_output:
                                output_was_changed = True
                            node.update()
                            [setattr(n, 'is_updated', False) for n in node.next_nodes]

                    # pass running to base trees
                    if output_was_changed:
                        pass_running(event.bl_tree)

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
                    output_was_changed = False  # optimisation
                    outdated_nodes = set(event.updated_nodes)
                    for node in tree.sorted_walk(
                            [n for n in tree.output_nodes if n.bl_tween.bl_idname == 'NodeGroupOutput']):
                        if not node.is_updated or node.name in outdated_nodes:
                            if node.is_output:
                                output_was_changed = True
                            node.update()
                            [setattr(n, 'is_updated', False) for n in node.next_nodes]

                    if output_was_changed:
                        pass_running(event.bl_tree)

        else:
            if next_handler:
                next_handler.send(event)


def pass_running(from_tree: SvGroupTree):
    """
    It asks update group nodes of upper trees
    there could be several group nodes in one tree and group nodes can be in multiple trees as well
    thous nodes also should be update only if output data was changed
    """
    trees_to_nodes: Dict[SvTree, List[SvGroupTreeNode]] = defaultdict(list)
    for node in from_tree.parent_nodes():
        trees_to_nodes[node.id_data].append(node)

    group_node_class: SvGroupTreeNode = bpy.types.Node.bl_rna_get_subclass_py('SvGroupTreeNode')
    process_method = group_node_class.process
    del group_node_class.process  # this method should not be called
    try:
        for sv_tree, nodes in trees_to_nodes.items():
            sv_tree.update_nodes(nodes)
    except Exception as e:
        print(e)
    finally:
        group_node_class.process = process_method


@contextmanager
def print_errors():
    try:
        yield None
    except Exception:
        traceback.print_exc()
