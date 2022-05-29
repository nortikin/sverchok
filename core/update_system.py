from collections import defaultdict
from copy import copy
from functools import lru_cache
from graphlib import TopologicalSorter
from time import perf_counter
from typing import TYPE_CHECKING, Optional, Generator, Iterable

from bpy.types import Node, NodeSocket, NodeTree, NodeLink
import sverchok.core.events as ev
import sverchok.core.tasks as ts
from sverchok.core.socket_conversions import ConversionPolicies
from sverchok.utils.profile import profile
from sverchok.utils.logging import log_error
from sverchok.utils.tree_walk import bfs_walk

if TYPE_CHECKING:
    from sverchok.node_tree import (SverchCustomTreeNode as SvNode,
                                    SverchCustomTree as SvTree)


UPDATE_KEY = "US_is_updated"
ERROR_KEY = "US_error"
TIME_KEY = "US_time"


def control_center(event):
    """
    1. Update tree model lazily
    2. Check whether the event should be processed
    3. Process event or create task to process via timer"""
    was_executed = False

    # frame update
    # This event can't be handled via NodesUpdater during animation rendering
    # because new frame change event can arrive before timer finishes its tusk.
    # Or timer can start working before frame change is handled.
    if type(event) is ev.AnimationEvent:
        was_executed = True
        if event.tree.sv_animate:
            UpdateTree.get(event.tree).is_animation_updated = False
            UpdateTree.update_animation(event)

    # something changed in the scene
    elif type(event) is ev.SceneEvent:
        was_executed = True
        if event.tree.sv_scene_update and event.tree.sv_process:
            UpdateTree.get(event.tree).is_scene_updated = False
            ts.tasks.add(ts.Task(event.tree, UpdateTree.main_update(event.tree)))

    # nodes changed properties
    elif type(event) is ev.PropertyEvent:
        was_executed = True
        tree = UpdateTree.get(event.tree)
        tree.add_outdated(event.updated_nodes)
        if event.tree.sv_process:
            ts.tasks.add(ts.Task(event.tree, UpdateTree.main_update(event.tree)))

    # update the whole tree anyway
    elif type(event) is ev.ForceEvent:
        was_executed = True
        UpdateTree.reset_tree(event.tree)
        ts.tasks.add(ts.Task(event.tree, UpdateTree.main_update(event.tree)))

    # mark that the tree topology has changed
    elif type(event) is ev.TreeEvent:
        was_executed = True
        UpdateTree.get(event.tree).is_updated = False
        if event.tree.sv_process:
            ts.tasks.add(ts.Task(event.tree, UpdateTree.main_update(event.tree)))

    # new file opened
    elif type(event) is ev.FileEvent:
        was_executed = True
        UpdateTree.reset_tree()

    return was_executed


class SearchTree:
    _from_nodes: dict['SvNode', set['SvNode']]
    _to_nodes: dict['SvNode', set['SvNode']]
    _from_sock: dict[NodeSocket, NodeSocket]
    _sock_node: dict[NodeSocket, Node]
    _links: set[tuple[NodeSocket, NodeSocket]]

    def __init__(self, tree: NodeTree):
        self._tree = tree
        self._from_nodes = {
            n: set() for n in tree.nodes if n.bl_idname != 'NodeFrame'}
        self._to_nodes = {
            n: set() for n in tree.nodes if n.bl_idname != 'NodeFrame'}
        self._from_sock = dict()  # only connected
        self._sock_node = dict()  # only connected sockets
        self._links = set()  # from to socket

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

    # todo add links between wifi nodes


class UpdateTree(SearchTree):
    """It catches some data for more efficient searches compare to Blender
    tree data structure"""
    _tree_catch: dict[str, 'UpdateTree'] = dict()  # the module should be auto-reloaded to prevent crashes

    @classmethod
    def get(cls, tree: "SvTree", refresh_tree=False) -> "UpdateTree":
        """
        :refresh_tree: if True it will convert update flags into outdated
        nodes. This can be expensive so it should be called only before tree
        reevaluation
        """
        if tree.tree_id not in cls._tree_catch:
            _tree = cls(tree)
        else:
            _tree = cls._tree_catch[tree.tree_id]

            if refresh_tree:
                # update topology
                if not _tree.is_updated:
                    old = _tree
                    _tree = old.copy()

                # update outdated nodes list
                if _tree._outdated_nodes is not None:
                    if not _tree.is_updated:
                        _tree._outdated_nodes.update(_tree._update_difference(old))
                    if not _tree.is_animation_updated:
                        _tree._outdated_nodes.update(_tree._animation_nodes())
                    if not _tree.is_scene_updated:
                        _tree._outdated_nodes.update(_tree._scene_nodes())

                _tree.is_updated = True
                _tree.is_animation_updated = True
                _tree.is_scene_updated = True

        return _tree

    @classmethod
    @profile(section="UPDATE")
    def update_animation(cls, event: ev.AnimationEvent):
        try:
            g = cls.main_update(event.tree, event.is_frame_changed, not event.is_animation_playing)
            while True:
                next(g)
        except StopIteration:
            pass

    @classmethod
    def main_update(cls, tree: NodeTree, update_nodes=True, update_interface=True) -> Generator['SvNode', None, None]:
        """Only for main trees
        1. Whe it called the tree should have information of what is outdated"""
        # todo add cancelling
        # print(f"UPDATE NODES {event.type=}, {event.tree.name=}")
        if update_nodes:
            up_tree = cls.get(tree, refresh_tree=True)
            walker = up_tree._walk()
            # walker = up_tree._debug_color(walker)
            for node, prev_socks in walker:
                with AddStatistic(node):
                    yield node
                    prepare_input_data(prev_socks, node.inputs)
                    node.process()

        if update_interface:
            update_ui(tree)

    @classmethod
    def reset_tree(cls, tree: NodeTree = None):
        """Remove tree data or data of all trees"""
        if tree is not None and tree.tree_id in cls._tree_catch:
            del cls._tree_catch[tree.tree_id]
        else:
            cls._tree_catch.clear()

    def copy(self) -> 'UpdateTree':
        """They copy will be with new topology if original tree was changed
        since berth of the first tree. Other attributes copied as is."""
        copy_ = type(self)(self._tree)
        for attr in self._copy_attrs:
            setattr(copy_, attr, copy(getattr(self, attr)))
        return copy_

    def add_outdated(self, nodes: Iterable):
        if self._outdated_nodes is not None:
            self._outdated_nodes.update(nodes)

    def __init__(self, tree: NodeTree):
        super().__init__(tree)
        self._tree_catch[tree.tree_id] = self

        self.is_updated = True  # False if topology was changed
        self.is_animation_updated = True
        self.is_scene_updated = True
        self._outdated_nodes: Optional[set[SvNode]] = None  # None means outdated all

        # https://stackoverflow.com/a/68550238
        self._sort_nodes = lru_cache(maxsize=1)(self._sort_nodes)

        self._copy_attrs = [
            'is_updated',
            'is_animation_updated',
            'is_scene_updated',
            '_outdated_nodes',
        ]

    def _animation_nodes(self) -> set['SvNode']:
        an_nodes = set()
        if not self.is_animation_updated:
            for node in self._tree.nodes:
                if getattr(node, 'is_animation_dependent', False) \
                        and getattr(node, 'is_animatable', False):
                    an_nodes.add(node)
        return an_nodes

    def _scene_nodes(self) -> set['SvNode']:
        sc_nodes = set()
        if not self.is_scene_updated:
            for node in self._tree.nodes:
                if getattr(node, 'is_scene_dependent', False) \
                        and getattr(node, 'is_interactive', False):
                    sc_nodes.add(node)
        return sc_nodes

    def _walk(self) -> tuple[Node, list[NodeSocket]]:
        # walk all nodes in the tree
        if self._outdated_nodes is None:
            outdated = None
            self._outdated_nodes = set()
        # walk triggered nodes and error nodes from previous updates
        else:
            outdated = frozenset(self._outdated_nodes)
            self._outdated_nodes.clear()  # todo what if execution was canceled?

        for node, other_socks in self._sort_nodes(outdated):
            # execute node only if all previous nodes are updated
            if all(n.get(UPDATE_KEY, True) for sock in other_socks if (n := self._sock_node.get(sock))):
                yield node, other_socks
                if node.get(ERROR_KEY, False):
                    self._outdated_nodes.add(node)
            else:
                node[UPDATE_KEY] = False

    def _sort_nodes(self,
                    from_nodes: frozenset['SvNode'] = None,
                    to_nodes: frozenset['SvNode'] = None)\
                    -> list[tuple['SvNode', list[NodeSocket]]]:
        nodes_to_walk = set()
        walk_structure = None
        if from_nodes is None and to_nodes is None:
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

    def _update_difference(self, old: 'UpdateTree') -> set['SvNode']:
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
    # todo cumulative time
    errors = (n.get(ERROR_KEY, None) for n in tree.nodes)
    times = (n.get(TIME_KEY, 0) for n in tree.nodes)
    tree.update_ui(errors, times)
