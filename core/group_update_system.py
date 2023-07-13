import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Iterator, Callable, Optional

from bpy.types import NodeTree, Node, NodeSocket
import sverchok.core.update_system as us
import sverchok.core.events as ev
import sverchok.core.tasks as ts
from sverchok.utils.handle_blender_data import BlTrees
from sverchok.utils.tree_walk import recursion_dfs_walk

if TYPE_CHECKING:
    from sverchok.node_tree import (SverchCustomTreeNode as SvNode,
                                    SverchCustomTree as SvTree)
    from sverchok.core.node_group import SvGroupTree as GrTree, \
        SvGroupTreeNode as GrNode


sv_logger = logging.getLogger('sverchok')


def control_center(event):
    """
    1. Update tree model lazily
    2. Check whether the event should be processed
    3. Process event or create task to process via timer"""
    was_executed = True

    # property of some node of a group tree was changed
    if type(event) is ev.GroupPropertyEvent:
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.add_outdated(event.updated_nodes)
        GroupUpdateTree.set_update_path(event.update_path)
        GroupUpdateTree.mark_outdated_groups(event.tree)

    # topology of a group tree was changed
    elif type(event) is ev.GroupTreeEvent:
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.is_updated = False
        GroupUpdateTree.set_update_path(event.update_path)  # in case it was called by pressing tab
        GroupUpdateTree.mark_outdated_groups(event.tree)

    # when group was created by pressing Ctrl + G
    elif type(event) is ev.NewGroupTreeEvent:
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.is_updated = False
        if BlTrees.is_main_tree(event.parent_tree):
            parent = us.UpdateTree.get(event.parent_tree)
        else:
            parent = GroupUpdateTree.get(event.parent_tree)
        parent.is_updated = False
        GroupUpdateTree.set_update_path(event.update_path)
        GroupUpdateTree.mark_outdated_groups(event.tree)

    # Connections between trees were changed
    elif type(event) is ev.TreesGraphEvent:
        trees_graph.is_updated = False

    # nodes will have another hash id and the comparison method will decide that
    # all nodes are new, and won't be able to detect changes, and will update all
    # Unlike main trees, groups can't do this via GroupTreeEvent because it
    # should be called only when a group is edited by user
    elif type(event) is ev.UndoEvent:
        for gt in BlTrees().sv_group_trees:
            GroupUpdateTree.get(gt).is_updated = False

    else:
        was_executed = False

    return was_executed


class GroupUpdateTree(us.UpdateTree):
    """Group trees has their own update method separate from main tree to have
    more nice profiling statistics. Also, it keeps some specific to group trees
    statuses."""
    get: Callable[['GrTree'], 'GroupUpdateTree']  # type hinting does not work grate :/

    def update(self, node: 'GrNode'):
        """Updates outdated nodes of group tree. Also, it keeps proper state of
        the exec_path. If exec_path is equal to update path it also updates UI
        of the tree
        :node: group node which tree is executed"""
        self._exec_path.append(node)
        try:
            is_opened_tree = self.update_path == self._exec_path
            if not is_opened_tree:
                self._viewer_nodes = set(self.__viewer_nodes())

            walker = self._walk()
            # walker = self._debug_color(walker)
            for node, prev_socks in walker:
                with us.AddStatistic(node, self):
                    us.prepare_input_data(prev_socks, node.inputs)
                    if error := node.dependency_error:
                        raise error
                    node.process()

            if is_opened_tree:
                if self._tree.show_time_mode == "Cumulative":
                    times = self._calc_cam_update_time()
                else:
                    times = None
                us.update_ui(self._tree, times)

        except Exception:
            raise
        finally:
            self._exec_path.pop()

    @classmethod
    def set_update_path(cls, update_path: list['GrNode']):
        """It should be called when update_path is changed (enter/exit group
        trees). All group update trees should have actual information about
        update_path to update properly.
        Currently, only one tree editor can be used for editing node groups so
        all trees will share the same path between all of them."""
        for tree in cls._tree_catch.values():
            if hasattr(tree, 'update_path'):
                tree.update_path = update_path

    @classmethod
    def mark_outdated_groups(cls, gr_tree: 'GrTree'):
        """It searches upstream node groups till main trees which should be
        updated to update given group tree"""
        nodes_to_update = defaultdict(set)
        for gr_node in trees_graph.walk(gr_tree):
            nodes_to_update[gr_node.id_data].add(gr_node)

        for tree, nodes in nodes_to_update.items():
            us.UpdateTree.get(tree).add_outdated(nodes)
            if tree.bl_idname == BlTrees.MAIN_TREE_ID and tree.sv_process:
                ts.tasks.add(ts.Task(tree,
                                     us.UpdateTree.main_update(tree),
                                     is_scene_update=False))

    def __init__(self, tree):
        """Should node be used directly but wia the get class method
        :update_path: list of group nodes via which update trigger was executed
        :_exec_path: list of group nodes via which the tree is executed
        :_viewer_nodes: output nodes which should be updated. If not presented
        all output nodes will be updated. The main reason of having them is to
        update viewer nodes only in opened group tree, as a side effect it
        optimises nodes execution"""
        super().__init__(tree)
        # update UI for the tree opened under the given path
        self.update_path: list['GrNode'] = []
        self.input_connected_nodes: set[Node] = self._get_input_connected()

        self._exec_path: list['GrNode'] = []

        # if not presented all output nodes will be updated
        self._viewer_nodes: set[Node] = set()  # not presented in main trees yet

        self._copy_attrs.extend([
            '_exec_path', 'update_path', '_viewer_nodes'])

    def _walk(self) -> tuple[Node, list[NodeSocket]]:
        """Yields nodes in order of their proper execution. It starts yielding
        from outdated nodes. It keeps the outdated_nodes storage in proper
        state. It checks after yielding the error status of the node. If the
        node has error it goes into outdated_nodes. If tree has viewer nodes
        it yields only nodes which should be called to update viewers."""
        # walk all nodes in the tree
        if self._outdated_nodes is None:
            outdated = None
            viewers = None
            self._outdated_nodes = set()
            self._viewer_nodes = set()
        # walk triggered nodes and error nodes from previous updates
        else:
            outdated = frozenset(self._outdated_nodes)
            viewers = frozenset(self._viewer_nodes)
            self._outdated_nodes.clear()
            self._viewer_nodes.clear()

        for node, other_socks in self._sort_nodes(outdated, viewers):
            # execute node only if all previous nodes are updated
            if all(n.get(us.UPDATE_KEY, True) for sock in other_socks if (n := self._sock_node.get(sock))):
                yield node, other_socks
                if node.get(us.ERROR_KEY, False):
                    self._outdated_nodes.add(node)
            else:
                node[us.UPDATE_KEY] = False

    def _get_input_connected(self):
        if not (group_input := self._active_input()):
            return set()
        return self.nodes_from([group_input])

    def _active_input(self) -> Optional[Node]:
        for node in reversed(self._from_nodes.keys()):
            if node.bl_idname == 'NodeGroupInput':
                return node

    def __viewer_nodes(self) -> list['SvNode']:
        active_output = None
        viewers = []
        for node in reversed(self._from_nodes.keys()):
            if node.bl_idname == 'NodeGroupOutput' and active_output is None:
                active_output = node
            elif node.bl_idname == 'SvStethoscopeNodeMK2':
                viewers.append(node)
        if active_output:
            viewers.append(active_output)
        return viewers


class TreesGraph:
    """It keeps relationships between main trees and group trees."""
    _group_nodes: dict['GrTree', set['GrNode']]

    def __init__(self):
        """:is_updated: the graph can be marked as outdated in this case it will
        be updated automatically whenever data will be fetched from it
        :_group_main: it stores information about in which main trees a group
        tree is used. The group tree can be located in some nested groups too
        :_entry_nodes: it stores information about which group nodes in main
        tree should be called to update a group tree"""
        self.is_updated = False

        self._group_nodes = defaultdict(set)

    def __getitem__(self, gr_tree: 'GrTree') -> set['GrNode']:
        """It either returns related to given group tree Main tree or collection
        of group nodes to update given group tree"""
        if not self.is_updated:
            self._update()
        return self._group_nodes[gr_tree]

    def walk(self, gr_tree: 'GrTree') -> Iterator['GrNode']:
        """It expects a grop tree which was changed and returns iterator of
        all group nodes which should be updated"""
        if not self.is_updated:
            self._update()
        visited = set()
        to_visit = set(self._group_nodes[gr_tree])
        for _ in range(1000):
            if not to_visit:
                break
            next_node = to_visit.pop()
            if next_node in visited:
                continue
            yield next_node
            visited.add(next_node)

            # scan group nodes which also should be updated in trees above
            if (under_tree := next_node.id_data) in self._group_nodes:  # if not it is a main tree
                to_visit.update(self._group_nodes[under_tree])
        else:
            sv_logger.debug('Infinite walk detected')

    def _update(self):
        """Calculate relationships between group trees and main trees"""
        self._group_nodes.clear()
        for tree in BlTrees().sv_main_trees:
            for gr_tree, gr_node in self._walk(tree):
                self._group_nodes[gr_tree].add(gr_node)
        self.is_updated = True

    @staticmethod
    def _walk(from_: NodeTree) -> Iterator[tuple[NodeTree, 'GrNode']]:
        """Iterate over all nested node trees"""
        current_entry_node = None

        def next_(_tree):
            nonlocal current_entry_node
            for node in _tree.nodes:
                if node.bl_idname == 'SvGroupTreeNode' and node.node_tree:
                    current_entry_node = node
                    yield node.node_tree

        walker = recursion_dfs_walk([from_], next_)
        next(walker)  # ignore first itself tree
        for tree in walker:
            yield tree, current_entry_node

    def __repr__(self):
        def group_nodes_str():
            for gr_tree, gr_nodes in self._group_nodes.items():
                yield f"   {gr_tree.name}:"
                for gr_node in gr_nodes:
                    yield f"      {gr_node.name}"

        gn = "\n".join(group_nodes_str())
        str_ = f"<TreesGraph:\n" \
               f"{gn}\n" \
               ">"
        return str_


trees_graph = TreesGraph()
