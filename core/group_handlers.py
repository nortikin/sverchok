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
from functools import partial
from time import time
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple, Optional, Iterator, NewType

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
            if event.to_update:  # todo cancel existing task?
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
        """Return map of bool values to group tree nodes where node has error if value is True"""
        path = NodeIdManager.generate_path(group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield NodesStatuses.get(node, path).error


@post_load_call
def register_loop():

    # this function won't be reload on script.reload event (F8)
    def group_event_loop(delay):
        if NodesUpdater.is_running():
            NodesUpdater.run_task()
        elif NodesUpdater.has_task():
            NodesUpdater.start_task()
            NodesUpdater.run_task()
        return delay

    bpy.app.timers.register(partial(group_event_loop, 0.01))


class NodesUpdater:
    """It can update only one tree at a time"""
    _group_nodes_path: Optional[List[SvGroupTreeNode]] = None  # todo path instead?
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
            while (time() - start_time) < 0.1:
                node = next(cls._handler)

            cls._last_node = node
            node.bl_tween.use_custom_color = True
            node.bl_tween.color = (0.7, 1.000000, 0.7)
            cls._report_progress(f'Pres "ESC" to abort, updating node "{node.name}"')

        except StopIteration:
            cls.finish_task()

    @classmethod
    def cancel_task(cls):
        # todo add cancel error to all nodes which should be processed next
        cls._handler.close()
        cls.finish_task()

    @classmethod
    def finish_task(cls):
        debug(f'Global update - {int((time() - cls._start_time) * 1000)}ms')
        cls._report_progress()
        group_node = cls._group_nodes_path[-1]
        path = NodeIdManager.generate_path(cls._group_nodes_path)
        group_node.node_tree.color_nodes(NodesStatuses.get(n, path).error for n in group_node.node_tree.nodes)

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
    # update_time: int  # ms


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
        for node in tree.nodes:
            node_id = cls.extract_node_id(node.bl_tween)

            if node.bl_tween.bl_idname not in OUT_ID_NAMES and node.is_input_linked:
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


class ContextTree(Tree):
    """
    The same tree but nodes has statistic dependently on context evaluation
    For example node can has is_updated=True for tree evaluated from one group node and False for another
    For using this class nodes of blender tree should have proper node_ids
    """
    _trees: Dict[str, Tree] = dict()

    def __init__(self, group_node: SvGroupTreeNode, path: Path):
        """
        It will create Python copy of the tree and tag already updated nodes
        User should update nodes via node.update method in appropriate order
        """
        self.group_node = group_node
        self.path = path

        super().__init__(group_node.node_tree)
        self._update_topology_status()
        for node in self.nodes:
            node.is_updated = NodesStatuses.get(node.bl_tween, path).is_updated

    def update_node(self, node: Node):
        """
        Group tree should have proper node_ids before calling this method
        Also this method will mark next nodes as outdated for current context
        """
        bl_node = node.bl_tween
        node.error = None
        try:
            if bl_node.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
                bl_node.process(self.group_node)
            elif hasattr(bl_node, 'process'):
                bl_node.process()

        except Exception as e:
            node.error = e
            traceback.print_exc()
        finally:
            NodesStatuses.set(bl_node, self.path, NodeStatistic(node.is_updated, node.error))

    def _update_topology_status(self):
        """Copy link node status by comparing with previous tree and save current"""
        if self.bl_tween.tree_id in self._trees:
            old_tree = self._trees[self.bl_tween.tree_id]

            new_links = self.links - old_tree.links
            for link in new_links:
                link.from_node.link_changed = True  # todo check if socket was already linked
                # link.to_node.is_updated = False  # it will be updated if "from_node" will updated without errors

            removed_links = old_tree.links - self.links
            for link in removed_links:
                if link.from_node in self.nodes:
                    self.nodes[link.from_node.name].link_changed = True  # todo should we?
                if link.to_node in self.nodes:
                    self.nodes[link.to_node.name].link_changed = True

        self._trees[self.bl_tween.tree_id] = self


# also IDs for this nodes are unchanged for now
OUT_ID_NAMES = {'SvDebugPrintNode', 'SvStethoscopeNodeMK2'}  # todo replace by checking of OutNode mixin class


def group_tree_handler(group_nodes_path: List[SvGroupTreeNode]) -> Generator[Node, None, bool]:
    group_node = group_nodes_path[-1]
    path = NodeIdManager.generate_path(group_nodes_path)
    tree = ContextTree(group_node, path)
    NodeIdManager.replace_nodes_id(tree, path)

    out_nodes = [n for n in tree.nodes if n.bl_tween.bl_idname in OUT_ID_NAMES]
    out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
    output_was_changed = False
    for node in tree.sorted_walk(out_nodes):
        should_be_updated = (not node.is_updated) or node.link_changed

        if hasattr(node.bl_tween, 'updater'):
            sup_updater = node.bl_tween.updater(group_nodes_path=group_nodes_path, is_input_changed=should_be_updated)
            # todo handling errors?
            try:
                while True:
                    yield next(sup_updater)
            except StopIteration as stop_error:
                node_was_updated = stop_error.value
            except GeneratorExit:  # todo aborting update
                return output_was_changed

        elif should_be_updated:
            yield node
            tree.update_node(node)
            node_was_updated = node.error is None
            if node.bl_tween.bl_idname == 'NodeGroupOutput':
                output_was_changed = True

        if node_was_updated:
            if not node.is_input_linked:
                for next_node in node.next_nodes:
                    if next_node.is_input_linked:
                        # this should cause arising all next node statistic because input was changed by global node
                        NodesStatuses.set(next_node.bl_tween, Path(''), NodeStatistic(False))
            for next_node in node.next_nodes:  # it will mark nodes as outdated according evaluation context
                next_node.is_updated = False

    return output_was_changed


def group_global_handler() -> Generator[Node]:
    """
    It should find changes and update group nodes
    After that update system of main trees should update themselves
    meanwhile group nodes should be switched off because they already was updated
    """
    for bl_tree in (t for t in bpy.data.node_groups if t.bl_idname == 'SverchCustomTreeType'):
        outdated_group_nodes = set()
        tree = Tree(bl_tree)
        for node in tree.sorted_walk(tree.output_nodes):
            if hasattr(node.bl_tween, 'updater'):

                group_updater = node.bl_tween.updater(is_input_changed=False)  # just searching inner changes
                try:
                    # it should return only nodes which should be updated
                    while True:
                        yield next(group_updater)
                except GeneratorExit:
                    group_updater.close()
                    return
                except StopIteration as stop_error:
                    sub_tree_changed = stop_error.value
                    if sub_tree_changed:
                        outdated_group_nodes.add(node.bl_tween)

        # passing running to update system of main tree
        if outdated_group_nodes:
            outdated_group_nodes = list(outdated_group_nodes)
            active_states = [n.is_active for n in outdated_group_nodes]
            try:
                [n.toggle_active(False) for n in outdated_group_nodes]
                bl_tree.update_nodes(list(outdated_group_nodes))
            except Exception:
                traceback.print_exc()
            finally:
                [n.toggle_active(s, to_update=False) for s, n in zip(active_states, outdated_group_nodes)]


class PressingEscape(bpy.types.Operator):
    bl_idname = 'node.sv_abort_nodes_updating'
    bl_label = 'Abort nodes updating'

    def execute(self, context):
        if NodesUpdater.is_running():
            NodesUpdater.cancel_task()
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type in {'SverchCustomTreeType'}  # todo can work only when group tree in path


register, unregister = bpy.utils.register_classes_factory([PressingEscape])
