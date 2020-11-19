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
from functools import wraps, partial
from time import time
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple, Optional, Iterator, Set

import bpy

from sverchok.data_structure import post_load_call
from sverchok.core.events import GroupEvent
from sverchok.utils.tree_structure import Tree, Node
from sverchok.utils.logging import debug

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SvTree = Union[SvGroupTree, SverchCustomTree]
    SvNode = Union[SverchCustomTreeNode, SvGroupTreeNode]


class MainHandler:
    @classmethod
    def update(cls, event: GroupEvent) -> Generator:
        """
        This method should be called by group nodes for updating their tree
        Also in means that input data was changed
        """

        # this will update node_id(s) of group tree todo it se redundant
        tree = ContextTree(event.group_node)
        if tree.nodes.active_input:
            ContextTree.mark_outdated_nodes([tree.nodes.active_input.bl_tween])
        return group_tree_update_handler(event.group_node)

    @classmethod
    def send(cls, event: GroupEvent):
        if event.type == GroupEvent.GROUP_NODE_UPDATE:
            if event.group_node.bl_idname != 'SvGroupTree':
                group_node_update().send(event)
            else:
                raise TypeError(f'SvGroupTree should use update method instead of send')

        elif event.type in {GroupEvent.NODES_UPDATE, GroupEvent.GROUP_TREE_UPDATE}:
            if event.updated_nodes:
                ContextTree.mark_outdated_nodes(event.updated_nodes)

            # Add events which should be updated via timer (changes in node tree)
            if event.to_update:
                NodesUpdater.add_task(event.group_node)

        elif event.type == GroupEvent.EDIT_GROUP_NODE:
            ContextTree(event.group_node)  # this will update node_ids of grout tree

    @staticmethod
    def get_error_nodes(group_node: SvGroupTreeNode) -> Iterator[Optional[Exception]]:
        """Return map of bool values to group tree nodes where node has error if value is True"""
        for stat in ContextTree.get_statistic(group_node.node_tree, group_node):
            yield stat.error


@post_load_call
def register_loop():

    # this function won't be reload on script.reload event (F8)
    def group_event_loop(delay):
        # if NodesUpdater.has_task() and not NodesUpdater.is_running():
        #     bpy.ops.node.updating_group_nodes('INVOKE_DEFAULT')
        if NodesUpdater.is_running():
            NodesUpdater.run_task()
        elif NodesUpdater.has_task():
            NodesUpdater.start_task()
        return delay

    bpy.app.timers.register(partial(group_event_loop, 0.01))


class NodesUpdater:
    """It can update only one tree at a time"""
    _group_node: Optional[SvGroupTreeNode] = None
    _handler: Optional[Generator] = None

    _node_tree_area: Optional[bpy.types.Area] = None
    _last_node: Optional[Node] = None

    @classmethod
    def add_task(cls, group_node: SvGroupTreeNode):
        """It can handle ony one tree at a time, several task will override each other"""
        cls._group_node = group_node

    @classmethod
    def start_task(cls):
        if cls.is_running():
            raise RuntimeError(f'Tree "{cls._group_node.node_tree.name}" already is being updated')
        cls._handler = group_tree_update_handler(cls._group_node)

        # searching appropriate area index for reporting update progress
        for area in bpy.context.screen.areas:
            if area.ui_type == 'SverchCustomTreeType':
                if area.spaces[0].path[-1].node_tree.name == cls._group_node.node_tree.name:
                    cls._node_tree_area = area
                    break

    @classmethod
    def run_task(cls, event: str = 'TIMER') -> Set[str]:
        if event != 'ESC':
            try:
                if cls._last_node:
                    cls._last_node.bl_tween.use_custom_color = False
                    cls._last_node.bl_tween.set_color()

                start_time = time()
                while (time() - start_time) < 0.1:
                    node = next(cls._handler)

                cls._last_node = node
                node.bl_tween.use_custom_color = True
                node.bl_tween.color = (0.7, 1.000000, 0.7)
                cls._report_progress(f'Pres "ESC" to abort, updating node "{node.name}"')

                return {'PASS_THROUGH'}
            except StopIteration:
                cls._report_progress()
                cls.finish_task()
                return {'FINISHED'}
        else:
            cls._handler.close()
            cls._report_progress()
            cls.finish_task()
            return {'CANCELED'}

    @classmethod
    def finish_task(cls):
        group_node = cls._group_node
        cls._group_node, cls._handler, cls._node_tree_area, cls._last_node = [None] * 4
        pass_running(group_node.node_tree)  # todo only if necessary

    @classmethod
    def has_task(cls) -> bool:
        return bool(cls._group_node)

    @classmethod
    def is_running(cls) -> bool:
        return bool(cls._handler)

    @classmethod
    def _report_progress(cls, text: str = None):
        if cls._node_tree_area:
            cls._node_tree_area.header_text_set(text)


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

    def __init__(self, group_node: SvGroupTreeNode):
        """
        It will create Python copy of the tree and tag already updated nodes


        User should update nodes via node.update method in appropriate order
        """
        self.group_node = group_node

        super().__init__(group_node.node_tree)
        self._replace_nodes_id()  # this should be before copying context node status and nodes updates
        [setattr(n, atr, val) for n in self.nodes
         for atr, val in zip(NodeStatistic.__annotations__, self._nodes_statistic[n.bl_tween.node_id])]
        self._update_topology_status()  # this should be after copying context nodes status
        self._trees[group_node.node_tree.tree_id] = self  # this should be after topology changes chek

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
        # saved tree can't be used here because it can contain outdated nodes (especially node.index attribute)
        # so called tree should be recreated, it should be done because node_id is dependent on tree topology
        tree = Tree(bl_tree)
        if tree is None:
            return
        for bl_n in bl_tree.nodes:
            yield cls._nodes_statistic[cls._generate_sub_node_id(tree.nodes[bl_n.name], group_node)]

    @classmethod
    def mark_outdated_nodes(cls, bl_nodes: List[SvNode]):
        """
        Try find given nodes in statistic and if find mark them as outdated
        it assumes that given nodes have correct node_id(s)
        """
        for bl_node in bl_nodes:
            stats = cls._nodes_statistic.get(bl_node.node_id)
            if stats is not None:
                cls._nodes_statistic[bl_node.node_id] = NodeStatistic(False, stats.error)

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

        group_node_id also can consist several paths -> "base_group_id.current_group_id"
        in case when the group is inside another group
        max length of path should be no more then number of base trees of most nested group node + 1
        """
        *previous_group_node_id, node_id = node.bl_tween.node_id.rsplit('.', 1)
        if node.bl_tween.bl_idname not in OUT_ID_NAMES and node.is_input_linked:
            return group_node.node_id + '.' + node_id
        else:
            return node_id


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
                tree = ContextTree(event.group_node)
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


def group_tree_update_handler(group_node: SvGroupTreeNode) -> Generator[Node]:
    tree = ContextTree(group_node)
    out_nodes = [n for n in tree.nodes if n.bl_tween.bl_idname in OUT_ID_NAMES]
    out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
    try:
        for node in tree.sorted_walk(out_nodes):
            if not node.is_updated:
                if hasattr(node.bl_tween, 'updater'):
                    yield from node.bl_tween.updater()  # todo handling errors?
                else:
                    yield node
                    tree.update_node(node)

                # if node is tree.nodes.active_output:  # todo move upper over call stuck
                #     event.output_was_changed = True

                if node.error is None:
                    [setattr(n, 'is_updated', False) for n in node.next_nodes]
    except GeneratorExit:
        pass  # todo aborting update


def pass_running(from_tree: SvGroupTree):
    """
    It asks update group nodes of upper trees
    there could be several group nodes in one tree and group nodes can be in multiple trees as well
    thous nodes also should be update only if output data was changed

    this function can't be called from generator chain otherwise if in parent tree there is another group node
    it will raise "ValueError: generator already executing" <- outdated, now it possible to call
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


class PressingEscape(bpy.types.Operator):
    bl_idname = 'node.sv_abort_nodes_updating'
    bl_label = 'Abort nodes updating'

    def execute(self, context):
        if NodesUpdater.is_running():
            NodesUpdater.run_task('ESC')
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type in {'SverchCustomTreeType'}  # todo can work only when group tree in path


register, unregister = bpy.utils.register_classes_factory([PressingEscape])
