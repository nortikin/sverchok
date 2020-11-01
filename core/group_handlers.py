# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from itertools import chain
from typing import Generator, ContextManager, Dict, TYPE_CHECKING

from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree


class MainHandler:
    def __init__(self):
        self.handlers = group_node_update(group_tree_update())

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
        new_tree = None
        try:
            new_tree = Tree(bl_tree)
            if bl_tree.tree_id in cls._trees:
                # copy nodes status from previous tree
                old_tree = cls._trees[bl_tree.tree_id]
                old_nodes = old_tree.nodes - new_tree.nodes
                [setattr(new_tree.nodes[on.name], 'is_updated', on.is_updated) for on in old_nodes]

                new_links = new_tree.links - old_tree.links
                removed_links = old_tree.links - new_tree.links
                for link in chain(new_links, removed_links):
                    link.from_node.is_updated = False
                    link.to_node.is_updated = False

            yield new_tree
        except Exception as e:
            print(e)
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

            with NodesStatus.update_tree_nodes(event.bl_tree) as tree:
                [setattr(n, 'is_updated', False) for n in tree.nodes if n.bl_tween.bl_idname == 'NodeGroupInput']
                for node in tree.sorted_walk(
                        [n for n in tree.output_nodes if n.bl_tween.bl_idname == 'NodeGroupOutput']):
                    if not node.is_updated:
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
    """
    while True:
        event: GroupEvent
        event = yield  # this variable can't have annotations here - syntax error
        if event.type == GroupEvent.GROUP_TREE_UPDATE:

            pass

        else:
            if next_handler:
                next_handler.send(event)
