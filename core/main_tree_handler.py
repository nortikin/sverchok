# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

import gc
from contextlib import contextmanager
from functools import partial
from time import time
from typing import Dict, Generator, Optional, Iterator, Tuple, NewType, List, TYPE_CHECKING, Callable

import bpy
from sverchok.core.sv_custom_exceptions import SvNoDataError, CancelError
from sverchok.core.socket_conversions import ConversionPolicies
from sverchok.data_structure import post_load_call
from sverchok.core.events import TreeEvent
from sverchok.utils.logging import debug, catch_log_error, log_error
from sverchok.utils.tree_structure import Tree, Node
from sverchok.utils.handle_blender_data import BlTrees, BlNode
from sverchok.utils.profile import profile
import sverchok.core.simple_update_system as sus

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTreeNode as SvNode


Path = NewType('Path', str)  # concatenation of group node ids


class TreeHandler:

    @staticmethod
    def send(event: TreeEvent):
        """Control center"""
        # debug(event.type)
        current_task = Task.get()

        # this should be first other wise other instructions can spoil the node statistic to redraw
        if current_task and current_task.is_running():
            if event.cancel:
                current_task.cancel()
            else:
                return  # ignore the event

        # something changed in scene and it duplicates some tree events which should be ignored
        elif event.type == TreeEvent.SCENE_UPDATE:
            # Either the scene handler was triggered by changes in the tree or tree is still in progress
            if current_task:
                return  # ignore the event
            # this event was caused my update system itself and should be ignored
            elif 'SKIP_UPDATE' in event.tree:
                del event.tree['SKIP_UPDATE']
                return

        # force update
        elif event.type == TreeEvent.FORCE_UPDATE:
            event.tree['FORCE_UPDATE'] = True

        # Add update tusk for the tree
        if handler := sus.control_center(event):
            Task.add(event, handler)

    @staticmethod
    def get_error_nodes(bl_tree) -> Iterator[Optional[Exception]]:
        """Return map of bool values to group tree nodes where node has error if value is True"""
        tree = ContextTrees.get(bl_tree, rebuild=False)
        for node in bl_tree.nodes:
            if node.bl_idname in {'NodeReroute', 'NodeFrame'}:
                yield None
                continue
            with tree.set_exec_context():  # tests shows good performance frequent use of the context manager
                error = tree.nodes[node.name].error
            # exit context manager before yielding otherwise it will block reading context dependent properties
            yield error

    @staticmethod
    def get_update_time(bl_tree) -> Iterator[Optional[float]]:
        tree = ContextTrees.get(bl_tree, rebuild=False)
        for node in bl_tree.nodes:
            if node.bl_idname in {'NodeReroute', 'NodeFrame'}:
                yield None
                continue
            with tree.set_exec_context():
                upd_time = tree.nodes[node.name].update_time
            yield upd_time

    @staticmethod
    def get_cum_time(bl_tree) -> Iterator[Optional[float]]:
        cum_time_nodes = ContextTrees.calc_cam_update_time(bl_tree)
        for node in bl_tree.nodes:
            yield cum_time_nodes.get(node)


def control_center(event: TreeEvent) -> bool:
    add_tusk = True

    # something changed in scene and it duplicates some tree events which should be ignored
    if event.type == TreeEvent.SCENE_UPDATE:
        ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

    # frame update
    # This event can't be handled via NodesUpdater during animation rendering because new frame change event
    # can arrive before timer finishes its tusk. Or timer can start working before frame change is handled.
    elif event.type == TreeEvent.FRAME_CHANGE:
        ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)
        profile(section="UPDATE")(lambda: list(global_updater(event.type)))()
        add_tusk = False

    # mark given nodes as outdated
    elif event.type == TreeEvent.NODES_UPDATE:
        ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

    # it will find changes in tree topology and mark related nodes as outdated
    elif event.type == TreeEvent.TREE_UPDATE:
        ContextTrees.mark_tree_outdated(event.tree)

    # force update
    elif event.type == TreeEvent.FORCE_UPDATE:
        ContextTrees.reset_data(event.tree)

    # new file opened
    elif event.type == TreeEvent.FILE_RELOADED:
        ContextTrees.reset_data()

    # Unknown event
    else:
        raise TypeError(f'Detected unknown event - {event}')

    return add_tusk


def tree_event_loop(delay):
    """Sverchok event handler"""
    with catch_log_error():
        if task := Task.get():
            if not task.is_running():
                task.start()
            task.run()  # task should be run via timer only https://developer.blender.org/T82318#1053877
    return delay


tree_event_loop = partial(tree_event_loop, 0.01)


class Task:
    _task: Optional['Task'] = None  # for now running only one task is supported

    __slots__ = ('_event',
                 '_handler_func',
                 '_handler',
                 '_node_tree_area',
                 '_start_time',
                 '_last_node',
                 )

    @classmethod
    def add(cls, event: TreeEvent, handler: Callable) -> 'Task':
        if cls._task and cls._task.is_running():
            raise RuntimeError(f"Can't update tree: {event.tree.name},"
                               f" already updating tree: {cls._task._event.tree.name}")
        cls._task = cls(event, handler)
        return cls._task

    @classmethod
    def get(cls) -> Optional['Task']:
        return cls._task

    def __init__(self, event, handler):
        self._event: TreeEvent = event
        self._handler_func: Callable[[TreeEvent], Generator] = handler
        self._handler: Optional[Generator[SvNode, None, None]] = None
        self._node_tree_area: Optional[bpy.types.Area] = None
        self._start_time: Optional[float] = None
        self._last_node: Optional[SvNode] = None

    def start(self):
        changed_tree = self._event.tree
        if self.is_running():
            raise RuntimeError(f'Tree "{changed_tree.name}" already is being updated')
        self._handler = self._handler_func(self._event)

        # searching appropriate area index for reporting update progress
        for area in bpy.context.screen.areas:
            if area.ui_type == 'SverchCustomTreeType':
                path = area.spaces[0].path
                if path and path[-1].node_tree.name == changed_tree.name:
                    self._node_tree_area = area
                    break
        gc.disable()

        self._start_time = time()

    @profile(section="UPDATE")
    def run(self):
        try:
            if self._last_node:
                self._last_node.set_temp_color()

            start_time = time()
            while (time() - start_time) < 0.15:  # 0.15 is max timer frequency
                node = next(self._handler)

            self._last_node = node
            node.set_temp_color((0.7, 1.000000, 0.7))
            self._report_progress(f'Pres "ESC" to abort, updating node "{node.name}"')

        except StopIteration:
            self.finish_task()

    def cancel(self):
        try:
            self._handler.throw(CancelError)
        except (StopIteration, RuntimeError):
            pass
        finally:  # protection from the task to be stack forever
            self.finish_task()

    def finish_task(self):
        try:
            gc.enable()
            debug(f'Global update - {int((time() - self._start_time) * 1000)}ms')
            self._report_progress()
        finally:
            Task._task = None

    def is_running(self) -> bool:
        return self._handler is not None

    def _report_progress(self, text: str = None):
        if self._node_tree_area:
            self._node_tree_area.header_text_set(text)


def global_updater(event_type: str) -> Generator[Node, None, None]:
    """Find all Sverchok main trees and run their handlers and update their UI if necessary
    update_ui of group trees will be called only if they opened in one of tree editors
    update_ui of main trees will be called if they are opened or was changed during the update event"""

    # grab trees from active node group editors
    trees_ui_to_update = set()
    if bpy.context.screen:  # during animation rendering can be None
        for area in bpy.context.screen.areas:
            if area.ui_type == BlTrees.MAIN_TREE_ID:
                if area.spaces[0].path:  # filter editors without active tree
                    trees_ui_to_update.add(area.spaces[0].path[-1].node_tree)

    for bl_tree in BlTrees().sv_main_trees:
        was_changed = False
        # update only trees which should be animated (for performance improvement in case of many trees)
        if event_type == TreeEvent.FRAME_CHANGE:
            if bl_tree.sv_animate:
                was_changed = yield from tree_updater(bl_tree, trees_ui_to_update)

        # tree should be updated any way
        elif event_type == TreeEvent.FORCE_UPDATE and 'FORCE_UPDATE' in bl_tree:
            del bl_tree['FORCE_UPDATE']
            was_changed = yield from tree_updater(bl_tree, trees_ui_to_update)

        # this seems the event upon some changes in the tree, skip tree if the property is switched off
        else:
            if bl_tree.sv_process:
                was_changed = yield from tree_updater(bl_tree, trees_ui_to_update)

        # it has sense to call this here if you press update all button or creating group tree from selected
        if was_changed:
            # if "DEBUG":
            #     yield None
            update_ui(bl_tree)  # this only will update UI of main trees
            trees_ui_to_update.discard(bl_tree)  # protection from double updating

            # this only need to trigger scene changes handler again
            bl_tree.nodes[-1].use_custom_color = not bl_tree.nodes[-1].use_custom_color
            bl_tree.nodes[-1].use_custom_color = not bl_tree.nodes[-1].use_custom_color
            # this indicates that process of the tree is finished and next scene event can be skipped
            bl_tree['SKIP_UPDATE'] = True

    # this will update all opened trees (in group editors)
    # regardless whether the trees was changed or not, including group nodes
    for bl_tree in trees_ui_to_update:
        update_ui(bl_tree)
        # args = [bl_tree.get_update_path()] if BlTree(bl_tree).is_group_tree else []
        # bl_tree.update_ui(*args)


def update_ui(tree):
    nodes_errors = TreeHandler.get_error_nodes(tree)
    update_time = (TreeHandler.get_cum_time(tree) if tree.show_time_mode == "Cumulative"
                   else TreeHandler.get_update_time(tree))
    tree.update_ui(nodes_errors, update_time)


def tree_updater(bl_tree, trees_ui_to_update: set) -> Generator[Node, None, bool]:
    tree = ContextTrees.get(bl_tree)
    tree_output_changed = False

    with tree.set_exec_context():
        for node in tree.sorted_walk(tree.output_nodes):
            can_be_updated = all(n.is_updated for n in node.last_nodes)
            if not can_be_updated:
                # here different logic can be implemented but for this we have to know if is there any output of the node
                # we could leave the node as updated and don't broke work of the rest forward nodes
                # but if the node does not have any output all next nodes will gen NoDataError what is horrible
                node.is_updated = False
                node.is_output_changed = False
                continue

            if hasattr(node.bl_tween, 'updater'):
                updater = group_node_updater(node, trees_ui_to_update)
            elif hasattr(node.bl_tween, 'process'):
                updater = node_updater(node)
            else:
                updater = empty_updater(node, error=None)

            # update node with sub update system, catch statistic
            start_time = time()
            node_error = yield from updater
            update_time = (time() - start_time)

            if node.is_output_changed or node_error:
                node.error = node_error
                node.update_time = None if node_error else update_time
                tree_output_changed = True

    return tree_output_changed


class ContextTrees:
    """It keeps trees with their states"""
    _trees: Dict[str, Tree] = dict()

    @classmethod
    def get(cls, bl_tree, rebuild=True):
        """Return caught tree. If rebuild is true it will try generate new tree if it was not build yet or changed"""
        tree = cls._trees.get(bl_tree.tree_id)

        # new tree, all nodes are outdated
        if tree is None:
            if rebuild:
                tree = Tree(bl_tree)
                cls._trees[bl_tree.tree_id] = tree
            else:
                raise RuntimeError(f"Tree={bl_tree} was never executed yet")

        # topology of the tree was changed and should be updated
        # Two reasons why always new tree is generated - it's simpler and new tree keeps fresh references to the nodes
        elif not tree.is_updated:
            if rebuild:
                tree = Tree(bl_tree)
                cls._update_topology_status(tree)
                cls._trees[bl_tree.tree_id] = tree
            else:
                raise RuntimeError(f"Tree={tree} is outdated")

        return tree

    @classmethod
    def mark_tree_outdated(cls, bl_tree):
        """Whenever topology of a tree is changed this method should be called."""
        tree = cls._trees.get(bl_tree.tree_id)
        if tree:
            tree.is_updated = False

    @classmethod
    def mark_nodes_outdated(cls, bl_tree, bl_nodes, context=''):
        """It will try to mark given nodes as to be recalculated.
        If node won't be found status of the tree will be changed to outdated"""
        if bl_tree.tree_id not in cls._trees:
            return  # all nodes will be outdated either way when the tree will be recreated (nothing to do)

        tree = cls._trees[bl_tree.tree_id]
        for bl_node in bl_nodes:
            try:
                if context:
                    with tree.set_exec_context(context):
                        tree.nodes[bl_node.name].is_updated = False
                else:
                    del tree.nodes[bl_node.name].is_updated

            # it means that generated tree does no have given node and should be recreated by next request
            except KeyError:
                tree.is_updated = False

    @classmethod
    def reset_data(cls, bl_tree=None):
        """
        Should be called upon loading new file, other wise it can lead to errors and even crash
        Also according the fact that trees have links to real blender nodes
        it is also important to call this method upon undo method otherwise errors and crashes
        Also single tree can be added, in this case only it will be deleted
        (it's going to be used in force update)
        """
        if bl_tree and bl_tree.tree_id in cls._trees:
            cls._trees[bl_tree.tree_id].delete()
            del cls._trees[bl_tree.tree_id]
        else:
            for tree in cls._trees.values():
                tree.delete()
            cls._trees.clear()

    @classmethod
    def calc_cam_update_time(cls, bl_tree, context='') -> dict:
        cum_time_nodes = dict()
        if bl_tree.tree_id not in cls._trees:
            return cum_time_nodes

        tree = cls._trees[bl_tree.tree_id]
        with tree.set_exec_context(context):
            for node in tree.sorted_walk(tree.output_nodes):
                if node.update_time is None:  # error node?
                    cum_time_nodes[node.bl_tween] = None
                    continue
                if len(node.last_nodes) > 1:
                    cum_time = sum(n.update_time for n in tree.sorted_walk([node]) if n.update_time is not None)
                else:
                    cum_time = sum(cum_time_nodes.get(n.bl_tween, 0) for n in node.last_nodes) + node.update_time
                cum_time_nodes[node.bl_tween] = cum_time
        return cum_time_nodes

    @classmethod
    def calc_cam_update_time_group(cls, bl_tree, group_nodes: List[SvNode]) -> dict:
        cum_time_nodes = dict()
        if bl_tree.tree_id not in cls._trees:
            return cum_time_nodes

        tree = cls._trees[bl_tree.tree_id]
        out_nodes = [n for n in tree.nodes if BlNode(n.bl_tween).is_debug_node]
        out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
        for node in tree.sorted_walk(out_nodes):
            path = PathManager.generate_path(group_nodes)
            with tree.set_exec_context(path):
                if node.update_time is None:  # error node?
                    cum_time_nodes[node.bl_tween] = None
                    continue
                if len(node.last_nodes) > 1:
                    cum_time = sum(n.update_time for n in tree.sorted_walk([node]) if n.update_time is not None)
                else:
                    cum_time = sum(cum_time_nodes.get(n.bl_tween, 0) for n in node.last_nodes) + node.update_time
                cum_time_nodes[node.bl_tween] = cum_time
        return cum_time_nodes

    @classmethod
    def _update_topology_status(cls, new_tree: Tree):
        """Copy link node status by comparing with previous tree and save current"""
        if new_tree.id in cls._trees:
            old_tree = cls._trees[new_tree.id]

            new_links = new_tree.links - old_tree.links
            for link in new_links:
                if link.from_node.name in old_tree.nodes:
                    from_old_node = old_tree.nodes[link.from_node.name]
                    from_old_socket = from_old_node.get_output_socket(link.from_socket.identifier)
                    has_old_from_socket_links = from_old_socket.links if from_old_socket is not None else False
                else:
                    has_old_from_socket_links = False

                # this is only because some nodes calculated data only if certain output socket is connected
                # ideally we would not like to make previous node outdated, but it requires changes in many nodes
                if not has_old_from_socket_links:
                    del link.from_node.is_input_changed
                else:
                    del link.to_node.is_input_changed

            removed_links = old_tree.links - new_tree.links
            for link in removed_links:
                if link.to_node in new_tree.nodes:
                    del new_tree.nodes[link.to_node.name].is_input_changed


class PathManager:
    @staticmethod
    def generate_path(group_nodes: List[SvNode]) -> Path:
        """path is ordered collection group node ids
        max length of path should be no more then number of base trees of most nested group node + 1"""
        return Path('.'.join(n.node_id for n in group_nodes))


def node_updater(node: Node) -> Generator[Node, None, Optional[Exception]]:
    """The node should has process method, all previous nodes should be updated"""
    node_error = None

    previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
    should_be_updated = not node.is_updated or node.is_input_changed or previous_nodes_are_changed

    node.is_output_changed = False  # it should always False unless the process method was called
    node.is_input_changed = False  # if node wont be able to handle new input it will be seen in its update status
    if should_be_updated:
        try:
            yield node
            with handle_node_data(node):
                node.bl_tween.process()
                node.is_updated = True
                node.is_output_changed = True
        except CancelError as e:
            node.is_updated = False
            node_error = e
        except Exception as e:
            node.is_updated = False
            log_error(e)
            node_error = e
    return node_error


def group_node_updater(node: Node, trees_ui_to_update: set) -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    """The node should have updater attribute"""
    previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
    should_be_updated = (not node.is_updated or node.is_input_changed or previous_nodes_are_changed)
    updater = node.bl_tween.updater(is_input_changed=should_be_updated, trees_ui_to_update=trees_ui_to_update)
    with handle_node_data(node):  # it's is redundant if the node group has no changes
        is_output_changed, out_error = yield from updater
        if is_output_changed or out_error:
            yield node  # yield groups node so it be colored by node Updater if necessary
    node.is_input_changed = False
    node.is_updated = not out_error
    node.is_output_changed = is_output_changed
    return out_error


def empty_updater(node: Node = None, **kwargs):  # todo to remove there is no reroute nodes in trees anymore
    """Reroutes, frame nodes, empty updaters which do nothing, set node in correct state
     returns given kwargs (only their values) like error=None, is_updated=True"""
    if node:  # ideally we would like always get first argument as node but group updater does not posses it
        previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
        should_be_updated = not node.is_updated or node.is_input_changed or previous_nodes_are_changed
        node.is_input_changed = False  # if node wont be able to handle new input it will be seen in its update status
        node.is_updated = True
        node.is_output_changed = True if should_be_updated else False
    return tuple(kwargs.values()) if len(kwargs) > 1 else next(iter(kwargs.values()))
    yield


@contextmanager
def handle_node_data(node: Node):
    """Any node should be executed inside this context manager. It supply node with data and save output node data
    Also it makes data conversion if it is needed"""

    # before execution the data should be put into input sockets
    # the storage of the data is in output sockets and is dependent on context
    # context should be set before the function execution
    for in_sock in node.inputs:
        for out_sock in in_sock.linked_sockets:
            data = out_sock.data

            # cast data from one socket type to another
            if out_sock.bl_tween.bl_idname != in_sock.bl_tween.bl_idname:
                implicit_conversions = ConversionPolicies.get_conversion(in_sock.bl_tween.default_conversion_name)
                data = implicit_conversions.convert(in_sock.bl_tween, out_sock.bl_tween, data)

            # save data to input socket
            in_sock.bl_tween.sv_set(data)  # data should be saved without context to be able to read by node

    # pass flow for node execution
    yield None

    # after node was executed the data should be reputed into appropriate place according to execution context
    # this redundant step in main trees and have only sense inside node groups
    for out_sock in node.outputs:
        try:
            if hasattr(out_sock.bl_tween, 'sv_get'):  # in case the node is group input one
                out_sock.data = out_sock.bl_tween.sv_get()
        except SvNoDataError:
            pass


@post_load_call
def post_load_register():
    # when new file is loaded all timers are unregistered
    # to make them persistent the post load handler should be used
    # but it's also is possible that the timer was registered during registration of the add-on
    if not bpy.app.timers.is_registered(tree_event_loop):
        bpy.app.timers.register(tree_event_loop)


def register():
    """Registration of Sverchok event handler"""
    # it appeared that the timers can be registered during the add-on initialization
    # The timer should be registered here because post_load_register won't be called when an add-on is enabled by user
    bpy.app.timers.register(tree_event_loop)


def unregister():
    bpy.app.timers.unregister(tree_event_loop)
