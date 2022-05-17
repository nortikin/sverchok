from collections import defaultdict
from contextlib import contextmanager
from functools import lru_cache
from graphlib import TopologicalSorter
from time import perf_counter
from typing import TYPE_CHECKING, TypeVar, Literal, Optional

from bpy_types import Node, NodeSocket, NodeTree
from sverchok.core.events import TreeEvent
from sverchok.core.socket_conversions import ConversionPolicies
from sverchok.utils.profile import profile
from sverchok.utils.logging import log_error
from sverchok.utils.tree_walk import bfs_walk

if TYPE_CHECKING:
    from sverchok.node_tree import SverchCustomTreeNode as SvNode


UPDATE_KEY = "US_is_updated"
ERROR_KEY = "US_error"
TIME_KEY = "US_time"

T = TypeVar('T')


def control_center(event: TreeEvent) -> bool:
    add_tusk = True

    # frame update
    # This event can't be handled via NodesUpdater during animation rendering because new frame change event
    # can arrive before timer finishes its tusk. Or timer can start working before frame change is handled.
    if event.type == TreeEvent.FRAME_CHANGE:
        Tree.get(event.tree).update(event)
        add_tusk = False

    # something changed in scene and it duplicates some tree events which should be ignored
    elif event.type == TreeEvent.SCENE_UPDATE:
        pass  # todo similar to animation
        # ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

    # mark given nodes as outdated
    elif event.type == TreeEvent.NODES_UPDATE:
        pass # todo add to outdated_nodes?

    # it will find changes in tree topology and mark related nodes as outdated
    elif event.type == TreeEvent.TREE_UPDATE:
        Tree.reset_tree(event.tree)  # todo should detect difference

    # force update
    elif event.type == TreeEvent.FORCE_UPDATE:
        Tree.reset_tree(event.tree)

    # new file opened
    elif event.type == TreeEvent.FILE_RELOADED:
        Tree.reset_tree()

    # Unknown event
    else:
        raise TypeError(f'Detected unknown event - {event}')

    # Add update tusk for the tree
    return add_tusk


class Tree:
    """It catches some data for more efficient searches compare to Blender
    tree data structure"""
    _tree_catch: dict[str, 'Tree'] = dict()  # the module should be auto-reloaded to prevent crashes

    WALK_MODE = Literal['animation', 'all']

    @classmethod
    def get(cls, tree: NodeTree):
        if tree.tree_id not in cls._tree_catch:
            _tree = cls(tree)
            cls._tree_catch[tree.tree_id] = _tree
        return cls._tree_catch[tree.tree_id]

    @profile(section="UPDATE")
    def update(self, event: TreeEvent):
        if event.is_frame_changed:
            tree = Tree.get(event.tree)
            for node, prev_socks in tree._walk(list(event.updated_nodes)):
                # node.set_temp_color([1, 1, 1])  # execution debug
                with add_statistic(node):
                    prepare_input_data(prev_socks, node.inputs)
                    node.process()

        if not event.is_animation_playing:
            update_ui(event.tree)

    @classmethod
    def reset_tree(cls, tree: NodeTree = None):
        """It can be called when the tree changed its topology with the tree
        parameter or when Undo event has happened without arguments"""
        if tree is not None and tree.tree_id in cls._tree_catch:
            del cls._tree_catch[tree.tree_id]
        else:
            cls._tree_catch.clear()

    def __init__(self, tree: NodeTree):
        self._tree = tree
        self._from_nodes: dict[SvNode, set[SvNode]] = defaultdict(set)
        self._to_nodes: dict[SvNode, set[SvNode]] = defaultdict(set)
        self._from_sock: dict[NodeSocket, NodeSocket] = dict()
        self._sock_node: dict[NodeSocket, Node] = dict()
        self._outdated_nodes: Optional[list[SvNode]] = None  # None means outdated all

        for link in (li for li in tree.links if not li.is_muted):
            self._from_nodes[link.to_node].add(link.from_node)
            self._to_nodes[link.from_node].add(link.to_node)
            self._from_sock[link.to_socket] = link.from_socket
            self._sock_node[link.from_socket] = link.from_node

        self._remove_reroutes()

    def _walk(self, outdated: list['SvNode'] = None) -> tuple[Node, list[NodeSocket]]:
        # walk all nodes in the tree
        if self._outdated_nodes is None:
            outdated = None
            self._outdated_nodes = []
        # walk triggered nodes and error nodes from previous updates
        else:
            outdated.extend(self._outdated_nodes)
            outdated = frozenset(outdated)
            self._outdated_nodes.clear()

        for node, other_socks in self._sort_nodes(outdated):
            # execute node only if all previous nodes are updated
            if all(n.get(UPDATE_KEY, True) for sock in other_socks if (n := self._sock_node.get(sock))):
                yield node, other_socks
                if node.get(ERROR_KEY, False):
                    self._outdated_nodes.append(node)
            else:
                node[UPDATE_KEY] = False

    @lru_cache(maxsize=1)
    def _sort_nodes(self, outdated_nodes: frozenset['SvNode'] = None) -> list[tuple['SvNode', list[NodeSocket]]]:

        def node_walker(node_: 'SvNode'):
            for nn in self._to_nodes.get(node_, []):
                yield nn

        nodes = []
        if outdated_nodes is None:
            for node in TopologicalSorter(self._from_nodes).static_order():
                nodes.append((node, [self._from_sock.get(s) for s in node.inputs]))
        else:
            outdated_nodes = set(bfs_walk(outdated_nodes, node_walker))
            from_outdated: dict[SvNode, set[SvNode]] = defaultdict(set)
            for n in outdated_nodes:
                if n in self._from_nodes:
                    from_outdated[n] = {_n for _n in self._from_nodes[n] if _n in outdated_nodes}
            for node in TopologicalSorter(from_outdated).static_order():
                nodes.append((node, [self._from_sock.get(s) for s in node.inputs]))
        return nodes

    def _remove_reroutes(self):
        for _node in self._from_nodes:
            if _node.bl_idname == "NodeReroute":

                # relink nodes
                from_n = self._from_nodes[_node].pop()
                self._to_nodes[from_n].remove(_node)  # remove from
                to_ns = self._to_nodes[_node]
                for _next in to_ns:
                    self._from_nodes[_next].remove(_node)  # remove to
                    self._from_nodes[_next].add(from_n)  # add link from
                    self._to_nodes[from_n].add(_next)  # add link to

                    # relink sockets
                    for sock in _next.inputs:
                        from_s = self._from_sock.get(sock)
                        if from_s is None:
                            continue
                        from_s_node = self._sock_node[from_s]
                        if from_s_node == _node:
                            from_from_s = self._from_sock.get(from_s_node.inputs[0])
                            if from_from_s is not None:
                                self._from_sock[sock] = from_from_s
                            else:
                                del self._from_sock[sock]

        self._from_nodes = {n: k for n, k in self._from_nodes.items() if n.bl_idname != 'NodeReroute'}
        self._to_nodes = {n: k for n, k in self._to_nodes.items() if n.bl_idname != 'NodeReroute'}


@contextmanager
def add_statistic(node):
    try:
        t = perf_counter()
        yield None
        node[UPDATE_KEY] = True
        node[ERROR_KEY] = None
        node[TIME_KEY] = perf_counter() - t
    except Exception as e:
        log_error(e)
        node[UPDATE_KEY] = False
        node[ERROR_KEY] = repr(e)


def prepare_input_data(prev_socks, input_socks):
    for ps, ns in zip(prev_socks, input_socks):
        if ps is None:
            continue
        data = ps.sv_get()

        # cast data
        if ps.bl_idname != ns.bl_idname:
            implicit_conversion = ConversionPolicies.get_conversion(ns.default_conversion_name)
            data = implicit_conversion.convert(ns, ps, data)

        ns.sv_set(data)


def update_ui(tree: NodeTree):
    errors = (n.get(ERROR_KEY, None) for n in tree.nodes)
    times = (n.get(TIME_KEY, 0) for n in tree.nodes)
    tree.update_ui(errors, times)