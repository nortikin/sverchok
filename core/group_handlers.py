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

import logging
import traceback
from collections import defaultdict
from functools import partial
from time import time
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple, Optional, Iterator, NewType, Tuple

import bpy

from sverchok.data_structure import post_load_call
from sverchok.core.events import GroupEvent
from sverchok.core.main_tree_handler import global_updater, empty_updater
from sverchok.utils.tree_structure import Tree, Node
from sverchok.utils.logging import debug, error, getLogger
from sverchok.utils.handle_blender_data import BlNode, BlTrees

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SvTree = Union[SvGroupTree, SverchCustomTree]
    SvNode = Union[SverchCustomTreeNode, SvGroupTreeNode]

NodeId = NewType('NodeId', str)
Path = NewType('Path', str)


class MainHandler:
    @classmethod
    def update(cls, event: GroupEvent) -> Iterator[Node]:
        """
        This method should be called by group nodes for updating their tree
        Also it means that input data was changed
        """
        path = NodeIdManager.generate_path(event.group_nodes_path)
        [NodesStatuses.mark_outdated(n, path) for n in event.updated_nodes]
        return group_tree_handler(event.group_nodes_path)

    @classmethod
    def send(cls, event: GroupEvent):
        if event.type in {GroupEvent.NODES_UPDATE, GroupEvent.GROUP_TREE_UPDATE}:
            if event.updated_nodes:
                [NodesStatuses.mark_outdated(n) for n in event.updated_nodes]  # global updating

            # Add events which should be updated via timer (changes in node tree)
            if event.to_update:
                if NodesUpdater.is_running():
                    NodesUpdater.cancel_task()

                NodesUpdater.add_task(event.group_nodes_path)

        elif event.type == GroupEvent.EDIT_GROUP_NODE:
            path = NodeIdManager.generate_path(event.group_nodes_path)
            NodeIdManager.replace_nodes_id(event.group_tree, path)

        elif event.type == GroupEvent.GROUP_NODE_UPDATE:
            raise TypeError(f'"Group node update" event should use update method instead of send')

        else:
            debug(f'Detected unknown event - {event}')

    @staticmethod
    def get_error_nodes(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[Exception]]:
        """Returns error if a node has error during execution or None"""
        path = NodeIdManager.generate_path(group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield NodesStatuses.get(node, path).error

    @staticmethod
    def get_nodes_update_time(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[int]]:
        """Returns duration of a node being executed in milliseconds or None if there was an error"""
        path = NodeIdManager.generate_path(group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield NodesStatuses.get(node, path).update_time


@post_load_call
def register_loop():

    # this function won't be reload on script.reload event (F8)
    def group_event_loop(delay):
        if NodesUpdater.is_running():
            NodesUpdater.run_task()
        elif NodesUpdater.has_task():  # task should be run via timer only https://developer.blender.org/T82318#1053877
            NodesUpdater.start_task()
            NodesUpdater.run_task()
        return delay

    bpy.app.timers.register(partial(group_event_loop, 0.01))


class NodesUpdater:
    """It can update only one tree at a time"""
    _group_nodes_path: Optional[List[SvGroupTreeNode]] = None
    _handler: Optional[Generator] = None

    _node_tree_area: Optional[bpy.types.Area] = None
    _last_node: Optional[Node] = None

    _start_time: float = None

    @classmethod
    def add_task(cls, group_nodes_path: List[SvGroupTreeNode]):
        """It can handle ony one tree at a time"""
        if not cls.is_running():  # ignoring for now
            cls._group_nodes_path = group_nodes_path

    @classmethod
    def start_task(cls):
        changed_tree = cls._group_nodes_path[-1].node_tree
        if cls.is_running():
            raise RuntimeError(f'Tree "{changed_tree.name}" already is being updated')
        cls._handler = group_global_handler()

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
    def debug_run_task(cls):
        """Color updated nodes for a few second after all"""
        try:
            start_time = time()
            while (time() - start_time) < 0.15:  # 0.15 is max timer frequency
                node = next(cls._handler)
                node.bl_tween.use_custom_color = True
                node.bl_tween.color = (0.7, 1.000000, 0.7)

            cls._last_node = node
            cls._report_progress(f'Pres "ESC" to abort, updating node "{node.name}"')

        except StopIteration:
            if 'node' in vars():
                return
            from time import sleep
            sleep(1)
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
        group_node = cls._group_nodes_path[-1]
        group_node.node_tree.update_ui(cls._group_nodes_path)

        cls._group_nodes_path, cls._handler, cls._node_tree_area, cls._last_node, cls._start_time = [None] * 5

    @classmethod
    def has_task(cls) -> bool:
        return cls._group_nodes_path is not None

    @classmethod
    def is_running(cls) -> bool:
        return cls._handler is not None

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
    update_time: int = None  # ms


class NodesStatuses:
    """
    It keeps node attributes which can be sensitive to context evaluation (path)
    """
    _statuses: Dict[NodeId, Union[NodeStatistic, Dict[Path, NodeStatistic]]] = defaultdict(dict)

    @classmethod
    def mark_outdated(cls, bl_node: SvNode, path: Optional[Path] = None):
        """
        Try find given nodes in statistic and if find mark them as outdated
        if path is not given it will mark as outdated for all node contexts
        """
        node_id = NodeIdManager.extract_node_id(bl_node)
        if node_id in cls._statuses:
            if isinstance(cls._statuses[node_id], dict):
                if path is not None:
                    if path in cls._statuses[node_id]:
                        del cls._statuses[node_id][path]
                else:
                    del cls._statuses[node_id]
            else:
                del cls._statuses[node_id]

    @classmethod
    def get(cls, bl_node: SvNode, path: Path) -> NodeStatistic:
        # saved tree can't be used here because it can contain outdated nodes (especially node.index attribute)
        # so called tree should be recreated, it should be done because node_id is dependent on tree topology
        node_id = NodeIdManager.extract_node_id(bl_node)
        if isinstance(cls._statuses[node_id], NodeStatistic):
            return cls._statuses[node_id]
        elif path in cls._statuses[node_id]:
            return cls._statuses[node_id][path]
        else:
            return NodeStatistic()

    @classmethod
    def set(cls, bl_node: SvNode, path: Path, stat: NodeStatistic):
        """
        path should be empty ("") for all nodes which are not connected to input group nodes
        it will protect useless node recalculation (such nodes should be calculated only once)
        """
        node_id = NodeIdManager.extract_node_id(bl_node)
        empty_path = Path('')
        if path == empty_path:
            cls._statuses[node_id] = stat
        else:
            if not isinstance(cls._statuses[node_id], dict):
                cls._statuses[node_id] = {path: stat}
            else:
                cls._statuses[node_id][path] = stat

    @classmethod
    def reset_data(cls):
        """This method should be called before opening new file to free all statistic data"""
        cls._statuses.clear()


class NodeIdManager:
    """Responsible for handling node_ids, should be deleted in future refactorings"""
    @classmethod
    def replace_nodes_id(cls, tree: Union[SvGroupTree, Tree], path: Path = ''):
        """
        The idea is to replace nodes ID before evaluating the tree
        in this case sockets will get unique identifiers relative to base group node

        format of new nodes ID -> "group_node_id.node_id" ("group_node_id." is replaceable part unlike "node_id")
        but nodes which is not connected with input should not change their ID
        because the result of their process method will be constant between different group nodes

        group_node_id also can consist several paths -> "base_group_id.current_group_id"
        in case when the group is inside another group
        max length of path should be no more then number of base trees of most nested group node + 1
        """
        if hasattr(tree, 'bl_idname'):  # it's Blender tree
            tree = Tree(tree)

        # todo should be cashed for optimization?
        input_linked_nodes = {n for n in tree.bfs_walk([tree.nodes.active_input] if tree.nodes.active_output else [])}

        for node in tree.nodes:
            node_id = cls.extract_node_id(node.bl_tween)

            if cut_mk_suffix(node.bl_tween.bl_idname) not in DEBUGGER_NODES and node in input_linked_nodes:
                node.bl_tween.n_id = path + '.' + node_id
            else:
                node.bl_tween.n_id = node_id

    @classmethod
    def generate_path(cls, group_nodes: List[SvGroupTreeNode]) -> Path:
        return Path('.'.join(cls.extract_node_id(n) for n in group_nodes))

    @staticmethod
    def extract_node_id(bl_node: SvNode) -> NodeId:
        *previous_group_node_id, node_id = bl_node.node_id.rsplit('.', 1)
        return node_id


class ContextTrees:
    """
    The same tree but nodes has statistic dependently on context evaluation
    For example node can has is_updated=True for tree evaluated from one group node and False for another
    For using this class nodes of blender tree should have proper node_ids
    """
    _trees: Dict[str, Tree] = dict()

    @classmethod
    def get(cls, bl_tree: SvTree, path: Path):
        """Return caught tree with filled `is_updated` attribute according last statistic"""
        tree = cls._trees.get(bl_tree.tree_id)
        if tree is None:
            tree = Tree(bl_tree)
            cls._trees[bl_tree.tree_id] = tree
        for node in tree.nodes:
            node.is_updated = NodesStatuses.get(node.bl_tween, path).is_updated  # good place to do this?
        return tree

    @classmethod
    def update_tree(cls, bl_tree: SvTree):
        """
        This method will generate new tree and update 'is_input_changed' node attribute
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
                    link.from_node.is_input_changed = True
                else:
                    link.to_node.is_input_changed = True

            removed_links = old_tree.links - new_tree.links
            for link in removed_links:
                if link.to_node in new_tree.nodes:
                    new_tree.nodes[link.to_node.name].is_input_changed = True

        cls._trees[new_tree.bl_tween.tree_id] = new_tree


# also node IDs for this nodes are unchanged for now
# todo replace by checking of OutNode mixin class
DEBUGGER_NODES = {'SvDebugPrintNode', 'SvStethoscopeNode'}  # those nodes should not have any outputs
# todo add list of unsupported nodes


def group_tree_handler(group_nodes_path: List[SvGroupTreeNode])\
        -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    # The function is growing bigger and bigger. I wish I knew how to simplify it.
    group_node = group_nodes_path[-1]
    path = NodeIdManager.generate_path(group_nodes_path)
    tree = ContextTrees.get(group_node.node_tree, path)
    NodeIdManager.replace_nodes_id(tree, path)

    out_nodes = [n for n in tree.nodes if cut_mk_suffix(n.bl_tween.bl_idname) in DEBUGGER_NODES]
    out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])

    input_linked_nodes = {n for n in tree.bfs_walk([tree.nodes.active_input] if tree.nodes.active_output else [])}
    output_linked_nodes = {n for n in tree.bfs_walk(out_nodes, direction='DOWNWARD')}

    # output
    output_was_changed = False
    node_error = None
    for node in tree.sorted_walk(out_nodes):
        if BlNode(node.bl_tween).is_debug_node:
            continue  # debug nodes will be updated after all by NodesUpdater only if necessary

        can_be_updated = all(n.is_updated for n in node.last_nodes)
        should_be_updated = can_be_updated and ((not node.is_updated) or node.is_input_changed)

        # reset current statistic
        if should_be_updated:
            node.is_updated = False
        else:
            continue

        # update node with sub update system
        if hasattr(node.bl_tween, 'updater'):
            sub_updater = node.bl_tween.updater(group_nodes_path=group_nodes_path, is_input_changed=should_be_updated)
        # regular nodes
        elif hasattr(node.bl_tween, 'process'):
            sub_updater = node_updater(node, group_node)
        # reroutes
        else:
            node.is_updated = True
            sub_updater = empty_updater(it_output_changed=True, node_error=None)

        start_time = time()
        is_output_changed, node_error = yield from sub_updater
        update_time = int((time() - start_time) * 1000)

        # update current node statistic if there was any updates
        node_path = Path('') if node not in input_linked_nodes else path
        stat = NodeStatistic(node.is_updated, node_error, update_time if not node_error else None)
        NodesStatuses.set(node.bl_tween, node_path, stat)

        # if update was successful
        if is_output_changed:

            # reset next nodes statistics (only for context nodes connected to global nodes)
            if node not in input_linked_nodes:
                for next_node in node.next_nodes:
                    if next_node in input_linked_nodes:
                        # this should cause arising all next node statistic because input was changed by global node
                        NodesStatuses.set(next_node.bl_tween, Path(''), NodeStatistic(False))

            # next nodes should be update too then
            for next_node in node.next_nodes:
                next_node.is_updated = False
                # statistic of below nodes should be set directly into NodesStatuses
                # because they won't be updated with current task
                if next_node not in output_linked_nodes:
                    NodesStatuses.set(next_node.bl_tween, Path(''), NodeStatistic(False))

            # output of group tree was changed
            if node.bl_tween.bl_idname == 'NodeGroupOutput':
                output_was_changed = True

    return output_was_changed, node_error


def group_global_handler() -> Generator[Node]:
    """
    It should find changes and update group nodes
    After that update system of main trees should update themselves
    meanwhile group nodes should be switched off because they already was updated
    """
    for bl_tree in BlTrees().sv_group_trees:
        # for now it always update all trees todo should be optimized later (keep in mind, trees can become outdated)
        ContextTrees.update_tree(bl_tree)

    yield from global_updater()


class CancelError(Exception):
    """Aborting tree evaluation by user"""


def cut_mk_suffix(name: str) -> str:
    """SvStethoscopeNodeMK2 -> SvStethoscopeNode"""
    id_name, _, version = name.partition('MK')
    try:
        int(version)
    except ValueError:
        return name
    return id_name


def node_updater(node: Node, group_node: SvGroupTreeNode):
    """
    Group tree should have proper node_ids before calling this method
    Also this method will mark next nodes as outdated for current context
    """
    bl_node = node.bl_tween
    node_error = None
    try:
        if bl_node.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
            bl_node.process(group_node)
        elif hasattr(bl_node, 'process'):
            yield node  # yield only normal nodes
            bl_node.process()
        node.is_updated = True
    except CancelError as e:
        node_error = e
    except Exception as e:
        node_error = e
        error(e)
        logger = getLogger()
        if logger.isEnabledFor(logging.DEBUG):
            traceback.print_exc()
    return not node_error, node_error
