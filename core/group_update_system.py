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
    was_executed = False

    # property of some node of a group tree was changed
    if type(event) is ev.GroupPropertyEvent:
        was_executed = True
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.add_outdated(event.updated_nodes)
        gr_tree.update_path = event.update_path
        for main_tree in trees_graph[event.tree]:
            us.UpdateTree.get(main_tree).add_outdated(trees_graph[main_tree, event.tree])
            if main_tree.sv_process:
                ts.tasks.add(ts.Task(main_tree, us.UpdateTree.main_update(main_tree)))

    # topology of a group tree was changed
    elif type(event) is ev.GroupTreeEvent:
        was_executed = True
        gr_tree = GroupUpdateTree.get(event.tree)
        gr_tree.is_updated = False
        # gr_tree.update_path = event.update_path
        for main_tree in trees_graph[event.tree]:
            us.UpdateTree.get(main_tree).add_outdated(trees_graph[main_tree, event.tree])
            if main_tree.sv_process:
                ts.tasks.add(ts.Task(main_tree, us.UpdateTree.main_update(main_tree)))

    # Connections between trees were changed
    elif type(event) is ev.TreesGraphEvent:
        was_executed = True
        trees_graph.is_updated = False

    return was_executed


class GroupUpdateTree(us.UpdateTree):
    get: Callable[['GrTree'], 'GroupUpdateTree']

    def update(self, node: 'GrNode'):
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
                    node.process()

            if is_opened_tree:
                us.update_ui(self._tree)

        except Exception:
            raise
        finally:
            self._exec_path.pop()

    def __init__(self, tree):
        super().__init__(tree)
        # update UI for the tree opened under the given path
        self.update_path: list['GrNode'] = []

        self._exec_path: list['GrNode'] = []

        # if not presented all output nodes will be updated
        self._viewer_nodes: set[Node] = set()  # not presented in main trees yet

        self._copy_attrs.extend(['_exec_path', 'update_path', '_viewer_nodes'])

    def _walk(self) -> tuple[Node, list[NodeSocket]]:
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
            self._outdated_nodes.clear()  # todo what if execution was canceled?
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
    _group_main: dict['GrTree', set['SvTree']]
    _entry_nodes: dict['SvTree', dict['GrTree', set['SvNode']]]

    def __init__(self):
        self.is_updated = False

        self._group_main = defaultdict(set)
        self._entry_nodes = defaultdict(lambda: defaultdict(set))

    @overload
    def __getitem__(self, item: 'GrTree') -> set['SvTree']: ...
    @overload
    def __getitem__(self, item: tuple['SvTree', 'GrTree']) -> set['SvNode']: ...

    def __getitem__(self, item):
        # print(self)
        if not self.is_updated:
            self._update()
        if isinstance(item, tuple):
            sv_tree, gr_tree = item
            return self._entry_nodes[sv_tree][gr_tree]
        else:
            return self._group_main[item]

    def _update(self):
        # print("REFRESH TreesGraph")
        self._group_main.clear()
        self._entry_nodes.clear()
        for tree in BlTrees().sv_main_trees:
            for gr_tree, gr_node in self._walk(tree):
                self._group_main[gr_tree].add(tree)
                self._entry_nodes[tree][gr_tree].add(gr_node)
        self.is_updated = True

    @staticmethod
    def _walk(from_: NodeTree) -> Iterator[tuple[NodeTree, 'SvNode']]:
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
