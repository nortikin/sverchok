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

from collections import defaultdict
from time import time
from typing import Generator, Dict, TYPE_CHECKING, Union, List, NamedTuple, Optional, Iterator, NewType, Tuple

from sverchok.core.events import GroupEvent
from sverchok.core.main_tree_handler import empty_updater, NodesUpdater, CancelError, ContextTrees
from sverchok.utils.tree_structure import Tree, Node
from sverchok.utils.logging import log_error
from sverchok.utils.handle_blender_data import BlNode

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
        # just replace nodes IDs and return (should be first, does not call cancel or add task) todo should it be here?
        if event.type == GroupEvent.EDIT_GROUP_NODE:
            path = NodeIdManager.generate_path(event.group_nodes_path)
            NodeIdManager.replace_nodes_id(event.tree, path)
            return  # there is no need in updating anything

        # this should be first other wise other instructions can spoil the node statistic to redraw
        if NodesUpdater.is_running():
            NodesUpdater.cancel_task()

        # mark given nodes as outdated
        if event.type == GroupEvent.NODES_UPDATE:
            [NodesStatuses.mark_outdated(n) for n in event.updated_nodes]

        # it will find (before the tree evaluation) changes in tree topology and mark related nodes as outdated
        elif event.type == GroupEvent.GROUP_TREE_UPDATE:
            GroupContextTrees.mark_tree_outdated(event.tree)

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
        path = NodeIdManager.generate_path(group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield NodesStatuses.get(node, path).error

    @staticmethod
    def get_nodes_update_time(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[float]]:
        """Returns duration of a node being executed in milliseconds or None if there was an error"""
        path = NodeIdManager.generate_path(group_nodes_path)
        for node in group_nodes_path[-1].node_tree.nodes:
            yield NodesStatuses.get(node, path).update_time

    @staticmethod
    def get_cum_time(group_nodes_path: List[SvGroupTreeNode]) -> Iterator[Optional[float]]:
        path = NodeIdManager.generate_path(group_nodes_path)
        bl_tree = group_nodes_path[-1].node_tree
        cum_time_nodes = GroupContextTrees.calc_cam_update_time(bl_tree, path)
        for node in bl_tree.nodes:
            yield cum_time_nodes.get(node)


# it is now inconsistent with the main tree handler module because is_updates can't be removed from here right now
# it is used by the NodeStatuses class to keep update status of nodes
class NodeStatistic(NamedTuple):
    """
    Statistic should be kept separately for each node
    because each node can have 10 or even 100 of different statistic profiles according number of group nodes using it
    """
    is_updated: bool = False
    error: Exception = None
    update_time: float = None  # sec


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

            if not BlNode(node.bl_tween).is_debug_node and node in input_linked_nodes:
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


class GroupContextTrees(ContextTrees):
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

        # new tree, all nodes are outdated
        if tree is None:
            tree = Tree(bl_tree)
            cls._trees[bl_tree.tree_id] = tree

        # topology of the tree was changed and should be updated
        elif not tree.is_updated:
            tree = cls._update_tree(bl_tree)
            cls._trees[bl_tree.tree_id] = tree

        # we have to always update is_updated status because the tree does not keep them properly
        for node in tree.nodes:
            node.is_updated = NodesStatuses.get(node.bl_tween, path).is_updated  # fill in actual is_updated state

        return tree

    @classmethod
    def calc_cam_update_time(cls, bl_tree, path: Path) -> dict:
        cum_time_nodes = dict()
        if bl_tree.tree_id not in cls._trees:
            return cum_time_nodes

        tree = cls._trees[bl_tree.tree_id]
        out_nodes = [n for n in tree.nodes if BlNode(n.bl_tween).is_debug_node]
        out_nodes.extend([tree.nodes.active_output] if tree.nodes.active_output else [])
        for node in tree.sorted_walk(out_nodes):
            update_time = NodesStatuses.get(node.bl_tween, path).update_time
            if update_time is None:  # error node?
                cum_time_nodes[node.bl_tween] = None
                continue
            if len(node.last_nodes) > 1:
                cum_time = sum(NodesStatuses.get(n.bl_tween, path).update_time for n in tree.sorted_walk([node])
                               if NodesStatuses.get(n.bl_tween, path).update_time is not None)
            else:
                cum_time = sum(cum_time_nodes.get(n.bl_tween, 0) for n in node.last_nodes) + update_time
            cum_time_nodes[node.bl_tween] = cum_time
        return cum_time_nodes

    @classmethod
    def _update_tree(cls, bl_tree: SvTree):
        """
        This method will generate new tree and update 'is_input_changed' node attribute
        according topological changes relatively previous call
        """
        new_tree = Tree(bl_tree)

        # update is_input_changed attribute
        cls._update_topology_status(new_tree)

        return new_tree

    @classmethod
    def mark_nodes_outdated(cls, bl_tree, bl_nodes):
        raise RuntimeError("Use the NodeStatuses classes instead")


def group_tree_handler(group_nodes_path: List[SvGroupTreeNode])\
        -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    # The function is growing bigger and bigger. I wish I knew how to simplify it.
    group_node = group_nodes_path[-1]
    path = NodeIdManager.generate_path(group_nodes_path)
    tree = GroupContextTrees.get(group_node.node_tree, path)
    NodeIdManager.replace_nodes_id(tree, path)

    out_nodes = [n for n in tree.nodes if BlNode(n.bl_tween).is_debug_node]
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
            sub_updater = group_node_updater(node, group_nodes_path)
        # regular nodes
        elif hasattr(node.bl_tween, 'process'):
            sub_updater = node_updater(node, group_node)
        # reroutes
        else:
            node.is_updated = True
            sub_updater = empty_updater(it_output_changed=True, node_error=None)

        start_time = time()
        is_output_changed, node_error = yield from sub_updater
        update_time = time() - start_time

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


def group_node_updater(node: Node, group_nodes_path=None) -> Generator[Node, None, Tuple[bool, Optional[Exception]]]:
    """The node should have updater attribute"""
    previous_nodes_are_changed = any(n.is_output_changed for n in node.last_nodes)
    should_be_updated = (not node.is_updated or node.is_input_changed or previous_nodes_are_changed)
    yield node  # yield groups node so it be colored by node Updater if necessary
    updater = node.bl_tween.updater(group_nodes_path=group_nodes_path, is_input_changed=should_be_updated)
    is_output_changed, out_error = yield from updater
    node.is_input_changed = False
    node.is_updated = not out_error
    node.is_output_changed = is_output_changed
    return is_output_changed, out_error


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
        log_error(e)
    return not node_error, node_error
