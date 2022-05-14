from collections import defaultdict, deque
from graphlib import TopologicalSorter
from time import perf_counter
from typing import Optional, Generator

from bpy_types import Node, NodeSocket, NodeTree
from sverchok.core.events import TreeEvent
from sverchok.core.socket_conversions import ConversionPolicies
from sverchok.utils.profile import profile
from sverchok.utils.logging import log_error


UPDATE_KEY = "US_is_updated"
ERROR_KEY = "US_error"
TIME_KEY = "US_time"


@profile(section="UPDATE")
def process_nodes(event: TreeEvent):
    if event.is_frame_changed:
        for node, prev_socks in Tree.get(event.tree).walk(event.updated_nodes):
            # node.set_temp_color([1, 1, 1])  # execution debug
            try:
                t = perf_counter()
                prepare_input_data(prev_socks, node.inputs)
                node.process()
                node[UPDATE_KEY] = True
                node[ERROR_KEY] = None
                node[TIME_KEY] = perf_counter() - t
            except Exception as e:
                log_error(e)
                node[UPDATE_KEY] = False
                node[ERROR_KEY] = repr(e)

    if not event.is_animation_playing:
        update_ui(event.tree)


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


class Tree:
    """It catches some data for more efficient searches compare to Blender
    tree data structure"""
    _tree_catch: dict[str, 'Tree'] = dict()  # the module should be auto-reloaded to prevent crashes

    def __init__(self, tree: NodeTree):
        self._from_nodes: dict[Node, set[Node]] = defaultdict(set)
        self._to_nodes: dict[Node, set[Node]] = defaultdict(set)
        self._from_sock: dict[NodeSocket, NodeSocket] = dict()
        self._sock_node: dict[NodeSocket, Node] = dict()
        self.__walk_catch: Optional[tuple[Node, list[NodeSocket]]] = None

        for link in (li for li in tree.links if not li.is_muted):
            self._from_nodes[link.to_node].add(link.from_node)
            self._to_nodes[link.from_node].add(link.to_node)
            self._from_sock[link.to_socket] = link.from_socket
            self._sock_node[link.from_socket] = link.from_node

        self._remove_reroutes()

    @classmethod
    def get(cls, tree: NodeTree):
        if tree.tree_id not in cls._tree_catch:
            cls._tree_catch[tree.tree_id] = cls(tree)
        return cls._tree_catch[tree.tree_id]

    def walk(self, outdated: list[Node]) -> tuple[Node, list[NodeSocket]]:
        if self.__walk_catch is None:
            outdated_nodes = set(self._bfs_walk(list(outdated)))
            from_outdated: dict[Node, set[Node]] = defaultdict(set)
            for n in outdated_nodes:
                if n in self._from_nodes:
                    from_outdated[n] = {_n for _n in self._from_nodes[n] if _n in outdated_nodes}
            self.__walk_catch = []
            for node in TopologicalSorter(from_outdated).static_order():
                self.__walk_catch.append((node, [self._from_sock.get(s) for s in node.inputs]))

        for node, other_socks in self.__walk_catch:
            if all(n.get(UPDATE_KEY, True) for sock in other_socks if (n := self._sock_node.get(sock))):
                yield node, other_socks
            else:
                node[UPDATE_KEY] = False

    @classmethod
    def reset_tree(cls, tree: NodeTree = None):
        """It can be called when the tree changed its topology with the tree
        parameter or when Undo event has happened without arguments"""
        if tree is not None and tree.tree_id in cls._tree_catch:
            del cls._tree_catch[tree.tree_id]
        else:
            cls._tree_catch.clear()

    def reset_walk(self):
        """It should be called when some animation properties of the tree
        nodes were changed"""
        self.__walk_catch = None

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

    def _bfs_walk(self, nodes: list[Node]) -> Generator[Node, None, None]:
        """
        Walk from the current node, it will visit all next nodes
        First will be visited children nodes than children of children nodes etc.
        https://en.wikipedia.org/wiki/Breadth-first_search
        """

        def node_walker(_node: Node):
            for nn in self._to_nodes.get(_node, []):
                yield nn

        waiting_nodes = deque(nodes)
        discovered = set(nodes)

        for i in range(20000):
            if not waiting_nodes:
                break
            n = waiting_nodes.popleft()
            yield n
            for next_node in node_walker(n):
                if next_node not in discovered:
                    waiting_nodes.append(next_node)
                    discovered.add(next_node)
        else:
            raise RecursionError(f'The tree has either more then={20000} nodes '
                                 f'or most likely it is circular')
