from collections import defaultdict
from typing import TYPE_CHECKING, overload, Iterator, Callable

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
        gr_tree.update_path = event.update_path
        for main_tree in trees_graph[event.tree]:
            us.UpdateTree.get(main_tree).add_outdated(trees_graph[main_tree, event.tree])
            if main_tree.sv_process:
                ts.tasks.add(ts.Task(main_tree,
                                     us.UpdateTree.main_update(main_tree),
                                     is_scene_update=False))

    # topology of a group tree was changed
    elif type(event) is ev.GroupTreeEvent:
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.is_updated = False
        gr_tree.update_path = event.update_path
        for main_tree in trees_graph[event.tree]:
            us.UpdateTree.get(main_tree).add_outdated(trees_graph[main_tree, event.tree])
            if main_tree.sv_process:
                ts.tasks.add(ts.Task(main_tree,
                                     us.UpdateTree.main_update(main_tree),
                                     is_scene_update=False))

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
                self._viewer_nodes = {node.active_output()}

            walker = self._walk()
            # walker = self._debug_color(walker)
            for node, prev_socks in walker:
                with us.AddStatistic(node):
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

        self._exec_path: list['GrNode'] = []

        # if not presented all output nodes will be updated
        self._viewer_nodes: set[Node] = set()  # not presented in main trees yet

        self._copy_attrs.extend(['_exec_path', 'update_path', '_viewer_nodes'])

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


class TreesGraph:
    """It keeps relationships between main trees and group trees."""
    _group_main: dict['GrTree', set['SvTree']]
    _entry_nodes: dict['SvTree', dict['GrTree', set['SvNode']]]

    def __init__(self):
        """:is_updated: the graph can be marked as outdated in this case it will
        be updated automatically whenever data will be fetched from it
        :_group_main: it stores information about in which main trees a group
        tree is used. The group tree can be located in some nested groups too
        :_entry_nodes: it stores information about which group nodes in main
        tree should be called to update a group tree"""
        self.is_updated = False

        self._group_main = defaultdict(set)
        self._entry_nodes = defaultdict(lambda: defaultdict(set))

    @overload
    def __getitem__(self, item: 'GrTree') -> set['SvTree']: ...
    @overload
    def __getitem__(self, item: tuple['SvTree', 'GrTree']) -> set['SvNode']: ...

    def __getitem__(self, item):
        """It either returns related to given group tree Main tree or collection
        of group nodes to update given group tree"""
        if not self.is_updated:
            self._update()
        if isinstance(item, tuple):
            sv_tree, gr_tree = item
            return self._entry_nodes[sv_tree][gr_tree]
        else:
            return self._group_main[item]

    def _update(self):
        """Calculate relationships between group trees and main trees"""
        self._group_main.clear()
        self._entry_nodes.clear()
        for tree in BlTrees().sv_main_trees:
            for gr_tree, gr_node in self._walk(tree):
                self._group_main[gr_tree].add(tree)
                self._entry_nodes[tree][gr_tree].add(gr_node)
        self.is_updated = True

    @staticmethod
    def _walk(from_: NodeTree) -> Iterator[tuple[NodeTree, 'SvNode']]:
        """Iterate over all nested node trees"""
        current_entry_node = None

        def next_(_tree):
            nonlocal current_entry_node
            for node in _tree.nodes:
                if node.bl_idname == 'SvGroupTreeNode' and node.node_tree:
                    if _tree.bl_idname == 'SverchCustomTreeType':
                        current_entry_node = node
                    yield node.node_tree

        walker = recursion_dfs_walk([from_], next_)
        next(walker)  # ignore first itself tree
        for tree in walker:
            yield tree, current_entry_node

    def __repr__(self):
        def group_main_str():
            for gr_tree, trees in self._group_main.items():
                yield f"   {gr_tree.name}:"
                for tree in trees:
                    yield f"      {tree.name}"

        def entry_nodes_str():
            for tree, groups in self._entry_nodes.items():
                yield f"   {tree.name}:"
                for group, nodes in groups.items():
                    yield f"      {group.name}:"
                    for node in nodes:
                        yield f"         {node.name}"

        gm = "\n".join(group_main_str())
        en = "\n".join(entry_nodes_str())
        str_ = f"<TreesGraph trees:\n" \
               f"{gm}\n" \
               f"entry nodes:\n" \
               f"{en}>"
        return str_


trees_graph = TreesGraph()
