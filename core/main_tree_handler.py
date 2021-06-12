# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
import logging
import traceback
from collections import defaultdict
from functools import partial
from time import time
from typing import Dict, NamedTuple, Generator, Optional, Iterator

import bpy
from sverchok.data_structure import post_load_call
from sverchok.core.events import TreeEvent
from sverchok.utils.logging import debug, catch_log_error, error, getLogger
from sverchok.utils.tree_structure import Tree, Node


# todo wifi nodes
# todo reroutes
# todo remove heat map
# todo animation
# todo update all
# todo print timings ?? it's available in the tree now
# todo debug to a file?
# todo add tree profiling tool


class TreeHandler:

    @classmethod
    def send(cls, event: TreeEvent):

        # this should be first other wise other instructions can spoil the node statistic to redraw
        if NodesUpdater.is_running():
            NodesUpdater.cancel_task()

        # mark given nodes as outdated
        if event.type == TreeEvent.NODES_UPDATE:
            [NodesStatuses.mark_outdated(n) for n in event.updated_nodes]

        # it will find changes in tree topology and mark related nodes as outdated
        elif event.type == TreeEvent.TREE_UPDATE:
            ContextTrees.update_tree(event.tree)

        # Unknown event
        else:
            raise TypeError(f'Detected unknown event - {event}')

        # Add update tusk for the tree
        if event.to_update:
            NodesUpdater.add_task(event.tree)

    @staticmethod
    def get_error_nodes(bl_tree) -> Iterator[Optional[Exception]]:
        """Return map of bool values to group tree nodes where node has error if value is True"""
        for node in bl_tree.nodes:
            yield NodesStatuses.get(node).error

    @staticmethod
    def get_update_time(bl_tree) -> Iterator[Optional[int]]:
        for node in bl_tree.nodes:
            yield NodesStatuses.get(node).update_time


@post_load_call
def register_loop():

    # this function won't be reload on script.reload event (F8)
    def tree_event_loop(delay):
        with catch_log_error():
            if NodesUpdater.is_running():
                NodesUpdater.run_task()
            elif NodesUpdater.has_task():  # task should be run via timer only https://developer.blender.org/T82318#1053877
                NodesUpdater.start_task()
                NodesUpdater.run_task()
        return delay

    bpy.app.timers.register(partial(tree_event_loop, 0.01))


class NodesUpdater:
    """It can update only one tree at a time"""
    _bl_tree = None
    _handler: Optional[Generator] = None

    _node_tree_area: Optional[bpy.types.Area] = None
    _last_node: Optional[Node] = None

    _start_time: float = None

    @classmethod
    def add_task(cls, bl_tree):
        """It can handle ony one tree at a time"""
        if cls.is_running():
            raise RuntimeError(f"Can't update tree: {bl_tree.name}, already updating tree: {cls._bl_tree.name}")
        cls._bl_tree = bl_tree

    @classmethod
    def start_task(cls):
        changed_tree = cls._bl_tree
        if cls.is_running():
            raise RuntimeError(f'Tree "{changed_tree.name}" already is being updated')
        cls._handler = tree_handler(changed_tree)

        # searching appropriate area index for reporting update progress
        for area in bpy.context.screen.areas:
            if area.ui_type == 'SverchCustomTreeType':
                path = area.spaces[0].path
                if path and path[-1].node_tree.name == changed_tree.name:
                    cls._node_tree_area = area
                    break

        cls._start_time = time()

    @classmethod
    def run_task(cls):
        try:
            if cls._last_node:
                cls._last_node.bl_tween.use_custom_color = False
                cls._last_node.bl_tween.set_color()

            start_time = time()
            while (time() - start_time) < 0.15:  # 0.15 is max timer frequency
                node = next(cls._handler)

            cls._last_node = node
            node.bl_tween.use_custom_color = True
            node.bl_tween.color = (0.7, 1.000000, 0.7)
            cls._report_progress(f'Pres "ESC" to abort, updating node "{node.name}"')

        except StopIteration:
            cls.finish_task()

    @classmethod
    def cancel_task(cls):
        try:
            cls._handler.throw(CancelError)
        except (StopIteration, RuntimeError):
            pass
        cls.finish_task()

    @classmethod
    def finish_task(cls):
        debug(f'Global update - {int((time() - cls._start_time) * 1000)}ms')
        cls._report_progress()
        cls._bl_tree.update_ui()
        cls._bl_tree, cls._handler, cls._node_tree_area, cls._last_node, cls._start_time = [None] * 5

    @classmethod
    def has_task(cls) -> bool:
        return cls._bl_tree is not None

    @classmethod
    def is_running(cls) -> bool:
        return cls._handler is not None

    @classmethod
    def _report_progress(cls, text: str = None):
        if cls._node_tree_area:
            cls._node_tree_area.header_text_set(text)


def tree_handler(bl_tree) -> Generator[Node, None, Optional[Exception]]:
    # The function is growing bigger and bigger. I wish I knew how to simplify it.
    tree = ContextTrees.get(bl_tree)
    out_nodes = [n for n in tree.nodes if not n.next_nodes]  # todo optimization

    # input
    cancel_updating = False

    # output
    error = None

    for node in tree.sorted_walk(out_nodes):
        can_be_updated = all(n.is_updated for n in node.last_nodes)
        should_be_updated = can_be_updated and ((not node.is_updated) or node.link_changed)
        is_output_changed = False

        # reset current statistic
        if should_be_updated:
            node.is_updated, node.error = False, None

        # update node with sub update system
        if hasattr(node.bl_tween, 'updater'):
            sub_updater = node.bl_tween.updater(is_input_changed=should_be_updated)
            try:
                while True:
                    yield next(sub_updater)
            except StopIteration as stop_error:
                is_output_changed, node.error = stop_error.value
                node.is_updated = not node.error
            except CancelError:
                sub_updater.throw(CancelError)

        # update regular node
        elif should_be_updated:
            if not cancel_updating:
                try:
                    yield node
                    ContextTrees.update_node(node)
                except CancelError:
                    cancel_updating = True
                    node.error = CancelError()
            else:
                node.error = CancelError()

            is_output_changed = node.error is None

        # update current node statistic if there was any updates
        if should_be_updated:
            NodesStatuses.set(node.bl_tween, NodeStatistic(node.is_updated, node.error, node.update_time))
            error = node.error or error

        # if update was successful
        if is_output_changed:

            # next nodes should be update too then
            for next_node in node.next_nodes:
                next_node.is_updated = False
                next_node.update_time = None

    return error


class ContextTrees:
    """
    The same tree but nodes has statistic dependently on context evaluation
    For example node can has is_updated=True for tree evaluated from one group node and False for another
    For using this class nodes of blender tree should have proper node_ids
    """
    _trees: Dict[str, Tree] = dict()

    @classmethod
    def get(cls, bl_tree):
        """Return caught tree with filled `is_updated` attribute according last statistic"""
        tree = cls._trees.get(bl_tree.tree_id)
        if tree is None:
            tree = Tree(bl_tree)
            cls._trees[bl_tree.tree_id] = tree
        for node in tree.nodes:
            node.is_updated = NodesStatuses.get(node.bl_tween).is_updated  # good place to do this?
        return tree

    @staticmethod
    def update_node(node: Node):
        """
        Group tree should have proper node_ids before calling this method
        Also this method will mark next nodes as outdated for current context
        """
        bl_node = node.bl_tween
        try:
            if hasattr(bl_node, 'process'):
                start_time = time()
                bl_node.process()
                node.update_time = int((time() - start_time) * 1000)
            node.is_updated = True

        except Exception as e:
            node.error = e
            error(e)
            logger = getLogger()
            if logger.isEnabledFor(logging.DEBUG):
                traceback.print_exc()

    @classmethod
    def update_tree(cls, bl_tree):
        """
        This method will generate new tree and update 'link_changed' node attribute
        according topological changes relatively previous call
        """
        cls._update_topology_status(Tree(bl_tree))

    @classmethod
    def reset_data(cls):
        """
        Should be called upon loading new file, other wise it can lead to errors and even crash
        Also according the fact that trees have links to real blender nodes
        it is also important to call this method upon undo method otherwise errors and crashes
        """
        cls._trees.clear()

    @classmethod
    def _update_topology_status(cls, new_tree: Tree):
        """Copy link node status by comparing with previous tree and save current"""
        if new_tree.bl_tween.tree_id in cls._trees:
            old_tree = cls._trees[new_tree.bl_tween.tree_id]

            new_links = new_tree.links - old_tree.links
            for link in new_links:
                if link.from_node.name in old_tree.nodes:
                    from_old_node = old_tree.nodes[link.from_node.name]
                    from_old_socket = from_old_node.get_output_socket(link.from_socket.identifier)
                    update_last_node = not from_old_socket.links if from_old_socket is not None else True
                else:
                    update_last_node = True

                if update_last_node:
                    link.from_node.link_changed = True
                else:
                    link.to_node.link_changed = True

            removed_links = old_tree.links - new_tree.links
            for link in removed_links:
                if link.to_node in new_tree.nodes:
                    new_tree.nodes[link.to_node.name].link_changed = True

        cls._trees[new_tree.bl_tween.tree_id] = new_tree


class NodeStatistic(NamedTuple):
    """
    Statistic should be kept separately for each node
    because each node can have 10 or even 100 of different statistic profiles according number of group nodes using it
    """
    is_updated: bool = False
    error: Exception = None
    update_time: int = None  # ms


class NodesStatuses:
    """
    It keeps node attributes which can be sensitive to context evaluation (path)
    """
    NodeId = str
    _statuses: Dict[NodeId, NodeStatistic] = defaultdict(NodeStatistic)

    @classmethod
    def mark_outdated(cls, bl_node):
        """
        Try find given nodes in statistic and if find mark them as outdated
        if path is not given it will mark as outdated for all node contexts
        """
        node_id = bl_node.node_id
        if node_id in cls._statuses:
            del cls._statuses[node_id]

    @classmethod
    def get(cls, bl_node) -> NodeStatistic:
        # saved tree can't be used here because it can contain outdated nodes (especially node.index attribute)
        # so called tree should be recreated, it should be done because node_id is dependent on tree topology
        return cls._statuses[bl_node.node_id]

    @classmethod
    def set(cls, bl_node, stat: NodeStatistic):
        node_id = bl_node.node_id
        cls._statuses[node_id] = stat

    @classmethod
    def reset_data(cls):
        """This method should be called before opening new file to free all statistic data"""
        cls._statuses.clear()


class CancelError(Exception):
    """Aborting tree evaluation by user"""
