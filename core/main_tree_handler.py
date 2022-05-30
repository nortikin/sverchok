# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from typing import Dict, NewType, List, TYPE_CHECKING

import sverchok.core.events as ev
from sverchok.utils.tree_structure import Tree
from sverchok.utils.handle_blender_data import BlNode
import sverchok.core.update_system as us
import sverchok.core.group_update_system as gus

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTreeNode as SvNode


Path = NewType('Path', str)  # concatenation of group node ids

update_systems = [us.control_center, gus.control_center]


class TreeHandler:

    @staticmethod
    def send(event):
        """Main control center
        1. preprocess the event
        2. Pass the event to update system(s)"""
        print(f"{event=}")

        # something changed in scene and it duplicates some tree events which should be ignored
        if isinstance(event, ev.SceneEvent):
            # this event was caused by update system itself and should be ignored
            if 'SKIP_UPDATE' in event.tree:
                del event.tree['SKIP_UPDATE']
                return

        was_handled = dict()
        # Add update tusk for the tree
        for handler in update_systems:
            res = handler(event)
            was_handled[handler] = res

        if (results := sum(was_handled.values())) > 1:
            duplicates = [f.__module__ for f, r in was_handled if r == 1]
            raise RuntimeError(f"{event=} was executed more than one time, {duplicates=}")
        elif results == 0:
            raise RuntimeError(f"{event} was not handled")


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
