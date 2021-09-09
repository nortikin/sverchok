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

from time import time
from typing import Generator, TYPE_CHECKING, Union, List, Optional, Iterator, Tuple

from sverchok.core.events import GroupEvent
from sverchok.core.main_tree_handler import empty_updater, NodesUpdater, ContextTrees, handle_node_data, PathManager
from sverchok.core.sv_custom_exceptions import CancelError
from sverchok.utils.tree_structure import Node
from sverchok.utils.logging import log_error
from sverchok.utils.handle_blender_data import BlNode

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree, SvGroupTreeNode
    from sverchok.node_tree import SverchCustomTree, SverchCustomTreeNode
    SvTree = Union[SvGroupTree, SverchCustomTree]
    SvNode = Union[SverchCustomTreeNode, SvGroupTreeNode]


class MainHandler:
    @classmethod
    def update(cls, event: GroupEvent, trees_ui_to_update: set) -> Iterator[Node]:
        """
        This method should be called by group nodes for updating their tree
        Also it means that input data was changed
        """
        ContextTrees.mark_nodes_outdated(
            event.tree, event.updated_nodes, PathManager.generate_path(event.group_nodes_path))
        return group_tree_handler(event.group_nodes_path, trees_ui_to_update)

    @classmethod
    def send(cls, event: GroupEvent):
        # this should be first other wise other instructions can spoil the node statistic to redraw
        if NodesUpdater.is_running():
            NodesUpdater.cancel_task()

        # mark given nodes as outdated
        if event.type == GroupEvent.NODES_UPDATE:
            ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

        # it will find (before the tree evaluation) changes in tree topology and mark related nodes as outdated
        elif event.type == GroupEvent.GROUP_TREE_UPDATE:
            ContextTrees.mark_tree_outdated(event.tree)

        # trigger just to evaluate debug nodes and update tree ui
        elif event.type == GroupEvent.EDIT_GROUP_NODE:
            ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

        elif event.type == GroupEvent.GROUP_NODE_UPDATE:
            raise TypeError(f'"Group node update" event should use update method instead of send')

        # Unknown event
        else:
            raise TypeError(f'Detected unknown event - {event}')

        # Add update tusk for the tree
        if event.to_update:
            NodesUpdater.add_task(event)

    @staticmethod
    def get_error_nodes(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[Exception]]:
        """Returns error if a node has error during execution or None"""
        path = PathManager.generate_path(group_nodes_path)
        tree = ContextTrees.get(group_nodes_path[-1].node_tree, rebuild=False)
        for node in group_nodes_path[-1].node_tree.nodes:
            if node.bl_idname in {'NodeReroute', 'NodeFrame'}:
                yield None
                continue
            with tree.set_exec_context(path):
                error = tree.nodes[node.name].error
            yield error

    @staticmethod
    def get_nodes_update_time(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[float]]:
        """Returns duration of a node being executed in milliseconds or None if there was an error"""
        path = PathManager.generate_path(group_nodes_path)
        tree = ContextTrees.get(group_nodes_path[-1].node_tree, rebuild=False)
        for node in group_nodes_path[-1].node_tree.nodes:
            if node.bl_idname in {'NodeReroute', 'NodeFrame'}:
                yield None
                continue
            with tree.set_exec_context(path):
                upd_time = tree.nodes[node.name].update_time
            yield upd_time

    @staticmethod
    def get_cum_time(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[float]]:
        bl_tree = group_nodes_path[-1].node_tree
        cum_time_nodes = ContextTrees.calc_cam_update_time_group(bl_tree, group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield cum_time_nodes.get(node)


def group_tree_handler(group_nodes_path: List[SvGroupTreeNode], trees_ui_to_update: set)\
        -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    group_node = group_nodes_path[-1]
    path = PathManager.generate_path(group_nodes_path)
    tree = ContextTrees.get(group_node.node_tree, path)
    is_debug_to_update = group_node.node_tree in trees_ui_to_update \
                         and group_node.node_tree.group_node_name == group_node.name

    out_nodes = [n for n in tree.nodes if BlNode(n.bl_tween).is_debug_node]
    out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])

    # output
    output_was_changed = False
    node_error = None

    with tree.set_exec_context(path):
        for node in tree.sorted_walk(out_nodes):
            can_be_updated = all(n.is_updated for n in node.last_nodes)
            if not can_be_updated:
                # here different logic can be implemented but for this we have to know if is there any output of the node
                # we could leave the node as updated and don't broke work of the rest forward nodes
                # but if the node does not have any output all next nodes will gen NoDataError what is horrible
                node.is_updated = False
                node.is_output_changed = False
                continue

            # update node with sub update system
            if hasattr(node.bl_tween, 'updater'):
                sub_updater = group_node_updater(node, group_nodes_path)
            # regular nodes
            elif hasattr(node.bl_tween, 'process'):
                sub_updater = node_updater(node, group_node, is_debug_to_update)
            # reroutes
            else:
                node.is_updated = True
                sub_updater = empty_updater(it_output_changed=True, node_error=None)

            start_time = time()
            node_error = yield from sub_updater
            update_time = time() - start_time

            if node.is_output_changed or node_error:
                node.error = node_error
                node.update_time = None if node_error else update_time

            if node.is_output_changed and node.bl_tween.bl_idname == 'NodeGroupOutput':
                output_was_changed = True

    return output_was_changed, node_error


def group_node_updater(node: Node, group_nodes_path=None) -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    """The node should have updater attribute"""
    previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
    should_be_updated = (not node.is_updated or node.is_input_changed or previous_nodes_are_changed)
    yield node  # yield groups node so it be colored by node Updater if necessary
    updater = node.bl_tween.updater(group_nodes_path=group_nodes_path, is_input_changed=should_be_updated)
    with handle_node_data(node):
        is_output_changed, out_error = yield from updater
    node.is_input_changed = False
    node.is_updated = not out_error
    node.is_output_changed = is_output_changed
    return out_error


def node_updater(node: Node, group_node: SvGroupTreeNode, is_debug_to_update: bool):
    """
    Group tree should have proper node_ids before calling this method
    Also this method will mark next nodes as outdated for current context
    """
    if BlNode(node.bl_tween).is_debug_node and not is_debug_to_update:
        return None, None  # Early exit otherwise it will spoil node statuses

    node_error = None

    previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
    should_be_updated = not node.is_updated or node.is_input_changed or previous_nodes_are_changed

    node.is_output_changed = False  # it should always False unless the process method was called
    node.is_input_changed = False  # if node wont be able to handle new input it will be seen in its update status
    if should_be_updated:
        try:
            with handle_node_data(node):
                if node.bl_tween.bl_idname in {'NodeGroupInput', 'NodeGroupOutput'}:
                    node.bl_tween.process(group_node)
                else:
                    yield node  # yield only normal nodes
                    node.bl_tween.process()
                node.is_updated = True
                node.is_output_changed = True

                # is_output_changed of a node without context is not reliable
                # if the tree presented multiple times attribute will be true only in first execution
                # so this should let to know next nodes that they also should be updated
                if not node.is_input_linked:
                    for next_n in node.next_nodes:
                        if next_n.is_input_linked or BlNode(next_n.bl_tween).is_debug_node:
                            del next_n.is_input_changed

        except CancelError as e:
            node.is_updated = False
            node_error = e
        except Exception as e:
            node.is_updated = False
            node_error = e
            log_error(e)
    return node_error
