from collections import defaultdict
from functools import lru_cache
from graphlib import TopologicalSorter
from time import perf_counter
from typing import TYPE_CHECKING, Optional, Generator, Callable, Iterable

from bpy.types import Node, NodeSocket, NodeTree, NodeLink
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


def control_center(event: TreeEvent) -> Optional[Callable[[TreeEvent], Generator]]:
    # frame update
    # This event can't be handled via NodesUpdater during animation rendering because new frame change event
    # can arrive before timer finishes its tusk. Or timer can start working before frame change is handled.
    if event.type == TreeEvent.FRAME_CHANGE:
        Tree.update_animation(event)
        return

    # something changed in scene and it duplicates some tree events which should be ignored
    elif event.type == TreeEvent.SCENE_UPDATE:
        pass  # todo similar to animation
        # ContextTrees.mark_nodes_outdated(event.tree, event.updated_nodes)

    # mark given nodes as outdated
    elif event.type == TreeEvent.NODES_UPDATE:
        pass  # todo add to outdated_nodes?

    # it will find changes in tree topology and mark related nodes as outdated
    elif event.type == TreeEvent.TREE_UPDATE:
        Tree.mark_outdated(event.tree)

    # force update
    elif event.type == TreeEvent.FORCE_UPDATE:
        Tree.reset_tree(event.tree)

    # new file opened
    elif event.type == TreeEvent.FILE_RELOADED:
        Tree.reset_tree()
        return

    # Unknown event
    else:
        raise TypeError(f'Detected unknown event - {event}')

    # Add update tusk for the tree
    return Tree.update


class SearchTree:
    def __init__(self, tree: NodeTree):
        self._tree = tree
        self._from_nodes: dict[SvNode, set[SvNode]] = {n: set() for n in tree.nodes}
        self._to_nodes: dict[SvNode, set[SvNode]] = {n: set() for n in tree.nodes}
        self._from_sock: dict[NodeSocket, NodeSocket] = dict()  # only connected
        self._sock_node: dict[NodeSocket, Node] = dict()  # only connected sockets
        self._links: set[tuple[NodeSocket, NodeSocket]] = set()  # from to socket

        for link in (li for li in tree.links if not li.is_muted):
            self._from_nodes[link.to_node].add(link.from_node)
            self._to_nodes[link.from_node].add(link.to_node)
            self._from_sock[link.to_socket] = link.from_socket
            self._sock_node[link.from_socket] = link.from_node
            self._sock_node[link.to_socket] = link.to_node
            self._links.add((link.from_socket, link.to_socket))

        self._remove_reroutes()

    def nodes_from(self, from_nodes: Iterable['SvNode']) -> set['SvNode']:
        def node_walker_to(node_: 'SvNode'):
            for nn in self._to_nodes.get(node_, []):
                yield nn

        return set(bfs_walk(from_nodes, node_walker_to))

    def nodes_to(self, to_nodes: Iterable['SvNode']) -> set['SvNode']:
        def node_walker_from(node_: 'SvNode'):
            for nn in self._from_nodes.get(node_, []):
                yield nn

        return set(bfs_walk(to_nodes, node_walker_from))

    def sort_nodes(self, nodes: Iterable['SvNode']) -> list['SvNode']:
        walk_structure: dict[SvNode, set[SvNode]] = defaultdict(set)
        for n in nodes:
            if n in self._from_nodes:
                walk_structure[n] = {_n for _n in self._from_nodes[n]
                                     if _n in nodes}
        nodes = []
        for node in TopologicalSorter(walk_structure).static_order():
            nodes.append(node)
        return nodes

    def previous_sockets(self, node: 'SvNode') -> list[NodeSocket]:
        return [self._from_sock.get(s) for s in node.inputs]

    def update_node(self, node: 'SvNode', supress=True):
        with AddStatistic(node, supress):
            prepare_input_data(self.previous_sockets(node), node.inputs)
            node.process()

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


class Tree(SearchTree):
    """It catches some data for more efficient searches compare to Blender
    tree data structure"""
    _tree_catch: dict[str, 'Tree'] = dict()  # the module should be auto-reloaded to prevent crashes

    @classmethod
    def get(cls, tree: NodeTree) -> 'Tree':
        if tree.tree_id not in cls._tree_catch:
            _tree = cls(tree)
        else:
            _tree = cls._tree_catch[tree.tree_id]
            if not _tree._is_updated:
                old = _tree
                _tree = cls(tree)
                if old._outdated_nodes is not None:
                    _tree._outdated_nodes = old._outdated_nodes.copy()
                    _tree._outdated_nodes.update(_tree._update_difference(old))
        return _tree

    @classmethod
    @profile(section="UPDATE")
    def update_animation(cls, event: TreeEvent):
        try:
            g = cls.update(event, event.is_frame_changed, not event.is_animation_playing)
            while True:
                next(g)
        except StopIteration:
            pass

    @classmethod
    def update(cls, event: TreeEvent, update_nodes=True, update_interface=True) -> Generator['SvNode', None, None]:
        if update_nodes:
            tree = cls.get(event.tree)

            if not event.tree.sv_process and event.type in {event.TREE_UPDATE, event.NODES_UPDATE, event.SCENE_UPDATE}:
                tree._outdated_nodes.update(event.updated_nodes)
                return

            walker = tree._walk(list(event.updated_nodes or []))
            walker = tree._debug_color(walker)
            for node, prev_socks in walker:
                with AddStatistic(node):
                    yield node
                    prepare_input_data(prev_socks, node.inputs)
                    node.process()

        if update_interface:
            update_ui(event.tree)

    @classmethod
    def reset_tree(cls, tree: NodeTree = None):
        """Remove tree data or data of all trees"""
        if tree is not None and tree.tree_id in cls._tree_catch:
            del cls._tree_catch[tree.tree_id]
        else:
            cls._tree_catch.clear()

    @classmethod
    def mark_outdated(cls, tree: NodeTree):
        if _tree := cls._tree_catch.get(tree.tree_id):
            _tree._is_updated = False

    def __init__(self, tree: NodeTree):
        super().__init__(tree)
        self._tree_catch[tree.tree_id] = self
        self._is_updated = True  # False if topology was changed
        self._outdated_nodes: Optional[set[SvNode]] = None  # None means outdated all

    def _walk(self, outdated: list['SvNode'] = None) -> tuple[Node, list[NodeSocket]]:
        # walk all nodes in the tree
        if self._outdated_nodes is None:
            outdated = None
            self._outdated_nodes = set()
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
                    self._outdated_nodes.add(node)
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

    def __sort_nodes(self,
                    from_nodes: frozenset['SvNode'] = None,
                    to_nodes: frozenset['SvNode'] = None)\
                    -> list[tuple['SvNode', list[NodeSocket]]]:
        nodes_to_walk = set()
        walk_structure = None
        if not from_nodes and not to_nodes:
            walk_structure = self._from_nodes
        elif from_nodes and to_nodes:
            from_ = self.nodes_from(from_nodes)
            to_ = self.nodes_to(to_nodes)
            nodes_to_walk = from_.intersection(to_)
        elif from_nodes:
            nodes_to_walk = self.nodes_from(from_nodes)
        else:
            nodes_to_walk = self.nodes_to(from_nodes)

        if nodes_to_walk:
            walk_structure: dict[SvNode, set[SvNode]] = defaultdict(set)
            for n in nodes_to_walk:
                if n in self._from_nodes:
                    walk_structure[n] = {_n for _n in self._from_nodes[n]
                                         if _n in nodes_to_walk}

        nodes = []
        if walk_structure:
            for node in TopologicalSorter(walk_structure).static_order():
                nodes.append((node, [self._from_sock.get(s) for s in node.inputs]))
        return nodes

    def _update_difference(self, old: 'Tree') -> set['SvNode']:
        nodes_to_update = self._from_nodes.keys() - old._from_nodes.keys()
        new_links = self._links - old._links
        for from_sock, to_sock in new_links:
            if from_sock not in old._sock_node:  # socket was not connected
                # protect from if not self.outputs[0].is_linked: return
                nodes_to_update.add(self._sock_node[from_sock])
            else:
                nodes_to_update.add(self._sock_node[to_sock])
        removed_links = old._links - self._links
        for from_sock, to_sock in removed_links:
            nodes_to_update.add(old._sock_node[to_sock])
        return nodes_to_update

    def _debug_color(self, walker: Generator, use_color: bool = True):
        def _set_color(node: 'SvNode', _use_color: bool):
            use_key = "DEBUG_use_user_color"
            color_key = "DEBUG_user_color"

            # set temporary color
            if _use_color:
                # save overridden color (only once)
                if color_key not in node:
                    node[use_key] = node.use_custom_color
                    node[color_key] = node.color
                node.use_custom_color = True
                node.color = (1, 1, 1)

            else:
                if color_key in node:
                    node.use_custom_color = node[use_key]
                    del node[use_key]
                    node.color = node[color_key]
                    del node[color_key]

        for n in self._tree.nodes:
            _set_color(n, False)

        for node, *args in walker:
            _set_color(node, use_color)
            yield node, *args


class AddStatistic:
    # using context manager from contextlib has big overhead
    # https://stackoverflow.com/questions/26152934/why-the-staggering-overhead-50x-of-contextlib-and-the-with-statement-in-python
    def __init__(self, node: 'SvNode', supress=True):
        self._node = node
        self._start = perf_counter()
        self._supress = supress

    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._node[UPDATE_KEY] = True
            self._node[ERROR_KEY] = None
            self._node[TIME_KEY] = perf_counter() - self._start
        else:
            log_error(exc_type)
            self._node[UPDATE_KEY] = False
            self._node[ERROR_KEY] = repr(exc_val)

        if self._supress and exc_type is not None:
            return issubclass(exc_type, Exception)


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
