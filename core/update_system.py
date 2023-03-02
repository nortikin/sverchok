from collections import defaultdict
from copy import copy
from functools import lru_cache
from graphlib import TopologicalSorter
from itertools import chain
from time import perf_counter
from typing import TYPE_CHECKING, Optional, Generator, Iterable

from bpy.types import Node, NodeSocket, NodeTree, NodeLink
import sverchok.core.events as ev
import sverchok.core.tasks as ts
from sverchok.core.sv_custom_exceptions import CancelError, SvNoDataError
from sverchok.core.socket_conversions import conversions
from sverchok.utils.profile import profile
from sverchok.utils.sv_logging import node_error_logger
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
    was_executed = True

    # frame update
    # This event can't be handled via NodesUpdater during animation rendering
    # because new frame change event can arrive before timer finishes its tusk.
    # Or timer can start working before frame change is handled.
    if type(event) is ev.AnimationEvent:
        if event.tree.sv_animate:
            UpdateTree.get(event.tree).is_animation_updated = False
            UpdateTree.update_animation(event)

    # something changed in the scene
    elif type(event) is ev.SceneEvent:
        if event.tree.sv_scene_update and event.tree.sv_process:
            UpdateTree.get(event.tree).is_scene_updated = False
            ts.tasks.add(ts.Task(event.tree,
                                 UpdateTree.main_update(event.tree),
                                 is_scene_update=True))

    # nodes changed properties
    elif type(event) is ev.PropertyEvent:
        tree = UpdateTree.get(event.tree)
        tree.add_outdated(event.updated_nodes)
        if event.tree.sv_process:
            ts.tasks.add(ts.Task(event.tree,
                                 UpdateTree.main_update(event.tree),
                                 is_scene_update=False))

    # update the whole tree anyway
    elif type(event) is ev.ForceEvent:
        UpdateTree.reset_tree(event.tree)
        ts.tasks.add(ts.Task(event.tree,
                             UpdateTree.main_update(event.tree),
                             is_scene_update=False))

    # mark that the tree topology has changed
    # also this can be called (by Blender) during undo event in this case all
    # nodes will have another hash id and the comparison method will decide that
    # all nodes are new, and won't be able to detect changes, and will update all
    elif type(event) is ev.TreeEvent:
        UpdateTree.get(event.tree).is_updated = False
        if event.tree.sv_process:
            ts.tasks.add(ts.Task(event.tree,
                                 UpdateTree.main_update(event.tree),
                                 is_scene_update=False))

    # new file opened
    elif type(event) is ev.FileEvent:
        UpdateTree.reset_tree()

    else:
        was_executed = False
    return was_executed


class SearchTree:
    """Data structure which represents Blender node trees but with ability
    of efficient search tree elements. Also it keeps tree state so it can be
    compared with new one to define differences."""

    _from_nodes: dict['SvNode', set['SvNode']]
    _to_nodes: dict['SvNode', set['SvNode']]
    _from_sock: dict[NodeSocket, NodeSocket]
    _to_socks: dict[NodeSocket, set[NodeSocket]]
    _links: set[tuple[NodeSocket, NodeSocket]]
    _sock_node: dict[NodeSocket, Node]

    def __init__(self, tree: NodeTree):
        self._tree = tree
        self._from_nodes = {
            n: set() for n in tree.nodes if n.bl_idname != 'NodeFrame'}
        self._to_nodes = {
            n: set() for n in tree.nodes if n.bl_idname != 'NodeFrame'}
        self._from_sock = dict()  # only connected
        self._to_socks = defaultdict(set)  # only connected
        self._links = set()  # from to socket
        self._sock_node = dict()

        for link in (li for li in tree.links if not li.is_muted):
            self._from_nodes[link.to_node].add(link.from_node)
            self._to_nodes[link.from_node].add(link.to_node)
            self._from_sock[link.to_socket] = link.from_socket
            self._to_socks[link.from_socket].add(link.to_socket)
            self._links.add((link.from_socket, link.to_socket))

        for node in tree.nodes:
            for sock in chain(node.inputs, node.outputs):
                self._sock_node[sock] = node

        self._remove_reroutes()
        self._remove_wifi_nodes()
        self._remove_muted_nodes()

    def nodes_from(self, from_nodes: Iterable['SvNode']) -> set['SvNode']:
        """Returns all next nodes from given ones"""
        def node_walker_to(node_: 'SvNode'):
            for nn in self._to_nodes.get(node_, []):
                yield nn

        return set(bfs_walk(from_nodes, node_walker_to))

    def node_from_input(self, in_socket: NodeSocket) -> Optional['SvNode']:
        """It expects input socket and returns connected node to it.
        If socket is not connected it returns None"""
        prev_sock = self._from_sock.get(in_socket)
        return prev_sock and self._sock_node[prev_sock]

    def nodes_from_socket(self, socket: NodeSocket) -> list['SvNode']:
        """Returns linked to the given socket nodes.
        The list will be empty if the socket is not connected.
        Connected input socket will always return list with one node"""
        if socket.is_output:
            next_socks = self._to_socks.get(socket, [])
            return [self._sock_node[s] for s in next_socks]
        else:
            prev_sock = self._from_sock.get(socket)
            return [self._sock_node[s] for s in [prev_sock] if s is not None]

    def nodes_to(self, to_nodes: Iterable['SvNode']) -> set['SvNode']:
        """Returns all previous nodes from given ones"""
        def node_walker_from(node_: 'SvNode'):
            for nn in self._from_nodes.get(node_, []):
                yield nn

        return set(bfs_walk(to_nodes, node_walker_from))

    def sort_nodes(self, nodes: Iterable['SvNode']) -> list['SvNode']:
        """Returns nodes in order of their correct execution"""
        walk_structure: dict[SvNode, set[SvNode]] = defaultdict(set)
        for n in nodes:
            if n in self._from_nodes:
                walk_structure[n] = {_n for _n in self._from_nodes[n]
                                     if _n in nodes}
        nodes = []
        for node in TopologicalSorter(walk_structure).static_order():
            nodes.append(node)
        return nodes

    def previous_sockets(self, node: 'SvNode') -> list[Optional[NodeSocket]]:
        """Return output sockets connected to input ones of given node
        If input socket is not linked the output socket will be None"""
        return [self._from_sock.get(s) for s in node.inputs]

    def socket_from_input(self, in_socket: NodeSocket) -> Optional[NodeSocket]:
        """It expects input socket and returns opposite connected socket to it.
        If socket is not connected it returns None"""
        return self._from_sock.get(in_socket)

    def update_node(self, node: 'SvNode', suppress=True):
        """Fetches data from previous node, makes data conversion if connected
        sockets have different types, calls process method of the given node
        records nodes statistics
        If suppress is True an error during node execution will be suppressed"""
        with AddStatistic(node, suppress):
            prepare_input_data(self.previous_sockets(node), node.inputs)
            if error := node.dependency_error:
                raise error
            node.process()

    def _remove_reroutes(self):
        for r in self._tree.nodes:
            if r.bl_idname != "NodeReroute":
                continue

            # relink nodes
            from_n = None
            if self._from_nodes[r]:
                from_n = self._from_nodes[r].pop()
                self._to_nodes[from_n].remove(r)  # remove from
            del self._from_nodes[r]

            to_ns = self._to_nodes[r]
            for to_n in to_ns:
                self._from_nodes[to_n].remove(r)  # remove to
                if from_n:
                    self._from_nodes[to_n].add(from_n)  # add link from
                    self._to_nodes[from_n].add(to_n)  # add link to
            del self._to_nodes[r]

            # relink sockets
            if from_s := self._from_sock.get(r.inputs[0]):
                self._links.discard((from_s, r.inputs[0]))
                self._to_socks[from_s].remove(r.inputs[0])
                del self._from_sock[r.inputs[0]]

            if to_ss := self._to_socks.get(r.outputs[0]):
                for to_s in to_ss:
                    self._links.discard((r.outputs[0], to_s))
                    if from_s is not None:
                        self._links.add((from_s, to_s))
                        self._from_sock[to_s] = from_s
                        self._to_socks[from_s].add(to_s)
                    else:
                        del self._from_sock[to_s]
                del self._to_socks[r.outputs[0]]

    def _remove_wifi_nodes(self):
        wifi_in: dict[str, 'SvNode'] = dict()
        wifi_out: dict[str, set['SvNode']] = defaultdict(set)
        disconnected = []
        for node in self._tree.nodes:
            if (var := getattr(node, 'var_name', None)) is not None:
                if not var:
                    disconnected.append(node)
                elif node.bl_idname == 'WifiInNode':
                    wifi_in[var] = node
                elif node.bl_idname == 'WifiOutNode':
                    wifi_out[var].add(node)

        for n in disconnected:
            self._remove_node(n)

        for var, in_ in wifi_in.items():
            for out in wifi_out[var]:
                for in_sock, out_sock in zip(in_.inputs, out.outputs):
                    if from_s := self._from_sock.get(in_sock):
                        from_n = self._sock_node[from_s]
                        self._to_nodes[from_n].discard(in_)
                        self._to_socks[from_s].discard(in_sock)
                        self._links.discard((from_s, in_sock))
                    if to_ss := self._to_socks.get(out_sock):
                        for to_s in to_ss:
                            to_n = self._sock_node[to_s]
                            self._from_nodes[to_n].discard(out)
                            del self._from_sock[to_s]
                            self._links.discard((out_sock, to_s))
                    if from_s and to_ss:
                        for to_s in to_ss:
                            to_n = self._sock_node[to_s]
                            self._from_nodes[to_n].add(from_n)
                            self._to_nodes[from_n].add(to_n)
                            self._from_sock[to_s] = from_s
                            self._to_socks[from_s].add(to_s)
                            self._links.add((from_s, to_s))

                for out_s in out.outputs:
                    if out_s in self._to_socks:
                        del self._to_socks[out_s]
                del self._from_nodes[out]
                del self._to_nodes[out]

            for in_s in in_.inputs:
                if in_s in self._from_sock:
                    del self._from_sock[in_s]
            del self._from_nodes[in_]
            del self._to_nodes[in_]

    def _remove_muted_nodes(self):
        util_nodes = {'NodeFrame', 'NodeReroute', 'NodeGroupInput'}
        for node in self._tree.nodes:
            if node.bl_idname in util_nodes:
                continue
            if not node.mute:
                continue
            for in_s, out_s in node.sv_internal_links:
                from_s = self._from_sock.get(in_s)
                to_ss = self._to_socks.get(out_s)
                if from_s and to_ss:
                    for to_s in to_ss.copy():
                        self._add_link(from_s, to_s)
            self._remove_node(node)

    def _add_link(self, from_s, to_s):
        """If to_s is already connected the link will be removed and new one
        will be added"""
        if f_s := self._from_sock.get(to_s):
            self._remove_link(f_s, to_s)
        self._to_socks[from_s].add(to_s)
        self._from_sock[to_s] = from_s
        self._links.add((from_s, to_s))
        from_node = self._sock_node[from_s]
        to_node = self._sock_node[to_s]
        self._to_nodes[from_node].add(to_node)
        self._from_nodes[to_node].add(from_node)

    def _remove_link(self, from_s, to_s):
        del self._from_sock[to_s]
        if len(self._to_socks[from_s]) == 1:
            del self._to_socks[from_s]
        else:
            self._to_socks[from_s].discard(to_s)
        self._links.discard((from_s, to_s))

        to_node = self._sock_node[to_s]
        from_node = self._sock_node[from_s]
        for in_s in to_node.inputs:
            if f_s := self._from_sock.get(in_s):
                if self._sock_node[f_s] == from_node:
                    break
        else:
            self._from_nodes[to_node].discard(from_node)
            self._to_nodes[from_node].discard(to_node)

    def _remove_node(self, node: Node):
        """Remove node with all its links"""
        for in_s in node.inputs:
            if from_s := self._from_sock.get(in_s):
                self._to_socks[from_s].discard(in_s)
                if not self._to_socks[from_s]:
                    del self._to_socks[from_s]
                self._links.discard((from_s, in_s))
                del self._from_sock[in_s]
        for from_n in self._from_nodes[node]:
            self._to_nodes[from_n].discard(node)
        del self._from_nodes[node]

        for out_s in node.outputs:
            if to_ss := self._to_socks.get(out_s):
                for to_s in to_ss:
                    del self._from_sock[to_s]
                    self._links.discard((out_s, to_s))
                del self._to_socks[out_s]
        for to_n in self._to_nodes[node]:
            self._from_nodes[to_n].discard(node)
        del self._to_nodes[node]

    def __repr__(self):
        def from_nodes_str():
            for tn, fns in self._from_nodes.items():
                yield f"   {tn.name}"
                for fn in fns:
                    yield f"      {fn.name}"

        def to_nodes_str():
            for fn, tns in self._to_nodes.items():
                yield f"   {fn.name}"
                for tn in tns:
                    yield f"      {tn.name}"

        def from_sock_str():
            for tso, fso in self._from_sock.items():
                yield f"   From='{fso.node.name}|{fso.name}'" \
                      f" to='{tso.node.name}|{tso.name}'"

        def links_str():
            for from_, to in self._links:
                yield f"   From='{from_.node.name}|{from_.name}'" \
                      f" to='{to.node.name}|{to.name}'"

        from_nodes = "\n".join(from_nodes_str())
        to_nodes = "\n".join(to_nodes_str())
        from_sock = "\n".join(from_sock_str())
        links = "\n".join(links_str())
        msg = f"<{type(self).__name__}\n" \
              f"from_nodes:\n" \
              f"{from_nodes}\n" \
              f"to_nodes:\n" \
              f"{to_nodes}\n" \
              f"from sockets:\n" \
              f"{from_sock}\n" \
              f"links:\n" \
              f"{links}"
        return msg


class UpdateTree(SearchTree):
    """It caches the trees to keep outdated nodes and to perform tree updating
    efficiently."""
    _tree_catch: dict[str, 'UpdateTree'] = dict()  # the module should be auto-reloaded to prevent crashes

    @classmethod
    def get(cls, tree: "SvTree", refresh_tree=False) -> "UpdateTree":
        """
        Get cached tree. If tree was not cached it will be.
        :refresh_tree: if True it will convert update flags into outdated
        nodes. This can be expensive, so it should be called only before tree
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
                    _tree = old.copy(tree)

                # update outdated nodes list
                if _tree._outdated_nodes is not None:
                    if not _tree.is_updated:
                        changed_nodes = _tree._update_difference(old)

                        # disconnected input sockets can remember previous data
                        # a node can be laizy and don't recalculate output
                        util_nodes = {'NodeGroupInput', 'NodeGroupOutput'}
                        for node in changed_nodes:
                            if node.bl_idname in util_nodes:
                                continue
                            for s in chain(node.inputs, node.outputs):
                                s.sv_forget()

                        _tree._outdated_nodes.update(changed_nodes)
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
        """Should be called to updated animated nodes"""
        try:
            g = cls.main_update(event.tree, event.is_frame_changed, not event.is_animation_playing)
            while True:
                next(g)
        except StopIteration:
            pass

    @classmethod
    def main_update(cls, tree: NodeTree, update_nodes=True, update_interface=True) -> Generator['SvNode', None, None]:
        """This generator is for the triggers. It can update outdated nodes and
        update UI. Should be used only with main trees, the group trees should
        use different method to separate profiling statistics. When it's called
        the tree should have information of what is outdated"""

        # print(f"UPDATE NODES {event.type=}, {event.tree.name=}")
        up_tree = cls.get(tree, refresh_tree=True)
        if update_nodes:
            walker = up_tree._walk()
            # walker = up_tree._debug_color(walker)
            try:
                for node, prev_socks in walker:
                    with AddStatistic(node):
                        yield node
                        prepare_input_data(prev_socks, node.inputs)
                        if error := node.dependency_error:
                            raise error
                        node.process()
            except CancelError:
                pass

        if update_interface:
            if up_tree._tree.show_time_mode == "Cumulative":
                times = up_tree._calc_cam_update_time()
            else:
                times = None
            update_ui(tree, times)

    @classmethod
    def reset_tree(cls, tree: NodeTree = None):
        """Remove tree data or data of all trees from the cache"""
        if tree is not None and tree.tree_id in cls._tree_catch:
            del cls._tree_catch[tree.tree_id]

            # reset nested trees too
            for group in (n for n in tree.nodes if hasattr(n, 'node_tree')):
                UpdateTree.reset_tree(group.node_tree)
        else:
            cls._tree_catch.clear()

    def copy(self, new_tree: NodeTree) -> 'UpdateTree':
        """They copy will be with new topology if original tree was changed
        since instancing of the first tree. Other attributes copied as is.
        :new_tree: it's import to pass fresh tree object because during undo
        events all previous tree objects invalidates"""
        copy_ = type(self)(new_tree)
        for attr in self._copy_attrs:
            setattr(copy_, attr, copy(getattr(self, attr)))
        return copy_

    def add_outdated(self, nodes: Iterable):
        """Add outdated nodes explicitly. Animation and scene dependent nodes
        can be marked as outdated via dedicated flags for performance."""
        if self._outdated_nodes is not None:
            self._outdated_nodes.update(nodes)

    def __init__(self, tree: NodeTree):
        """Should not use be used directly, only via the get class method
        :is_updated: Should be False if topology of the tree was changed
        :is_animation_updated: Should be False animation dependent nodes should
        be updated
        :is_scene_updated: Should be False if scene dependent nodes should be
        updated
        :_outdated_nodes: Keeps nodes which properties were changed or which
        have errors. Can be None when what means that all nodes are outdated
        :_copy_attrs: list of attributes which should be copied by the copy
        method"""
        super().__init__(tree)
        self._tree_catch[tree.tree_id] = self

        self.is_updated = True  # False if topology was changed
        self.is_animation_updated = True
        self.is_scene_updated = True
        self._outdated_nodes: Optional[set[SvNode]] = None  # None means outdated all

        # https://stackoverflow.com/a/68550238
        self._sort_nodes = lru_cache(maxsize=1)(self.__sort_nodes)

        self._copy_attrs = [
            'is_updated',
            'is_animation_updated',
            'is_scene_updated',
            '_outdated_nodes',
        ]

    def _animation_nodes(self) -> set['SvNode']:
        """Returns nodes which are animation dependent"""
        an_nodes = set()
        if not self.is_animation_updated:
            for node in self._tree.nodes:
                if getattr(node, 'is_animation_dependent', False) \
                        and getattr(node, 'is_animatable', False):
                    an_nodes.add(node)
        return an_nodes

    def _scene_nodes(self) -> set['SvNode']:
        """Returns nodes which are scene dependent"""
        sc_nodes = set()
        if not self.is_scene_updated:
            for node in self._tree.nodes:
                if getattr(node, 'is_scene_dependent', False) \
                        and getattr(node, 'is_interactive', False):
                    sc_nodes.add(node)
        return sc_nodes

    def _walk(self) -> tuple[Node, list[NodeSocket]]:
        """Yields nodes in order of their proper execution. It starts yielding
        from outdated nodes. It keeps the outdated_nodes storage in proper
        state. It checks after yielding the error status of the node. If the
        node has error it goes into outdated_nodes. It uses cached walker, so
        it works more efficient when outdated nodes are the same between the
        method calls."""

        # walk all nodes in the tree
        if self._outdated_nodes is None:
            outdated = None
            self._outdated_nodes = set()
        # walk triggered nodes and error nodes from previous updates
        else:
            outdated = frozenset(self._outdated_nodes)
            self._outdated_nodes.clear()

        for node, other_socks in self._sort_nodes(outdated):
            # execute node only if all previous nodes are updated
            if all(n.get(UPDATE_KEY, True) for sock in other_socks if (n := self._sock_node.get(sock))):
                yield node, other_socks
                if node.get(ERROR_KEY, False):
                    self._outdated_nodes.add(node)
            else:
                node[UPDATE_KEY] = False

    def __sort_nodes(self,
                     from_nodes: frozenset['SvNode'] = None,
                     to_nodes: frozenset['SvNode'] = None)\
                     -> list[tuple['SvNode', list[NodeSocket]]]:
        """Sort nodes of the tree in proper execution order. When all given
        parameters are None it uses all tree nodes
        :from_nodes: if given it sorts only next nodes from given ones
        :to_nodes: if given it sorts only previous nodes from given
        If from_nodes and to_nodes are given it uses only intersection of next
        nodes from from_nodes and previous nodes from to_nodes"""
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
        """Returns nodes which should be updated according to changes in the
        tree topology
        :old: previous state of the tree to compare with"""
        nodes_to_update = self._from_nodes.keys() - old._from_nodes.keys()
        new_links = self._links - old._links
        for from_sock, to_sock in new_links:
            if from_sock not in old._from_sock:  # socket was not connected
                # protect from if not self.outputs[0].is_linked: return
                nodes_to_update.add(self._sock_node[from_sock])
            else:
                nodes_to_update.add(self._sock_node[to_sock])
        removed_links = old._links - self._links
        for from_sock, to_sock in removed_links:
            if to_sock not in self._sock_node:
                continue  # the link was removed together with the node
            nodes_to_update.add(self._sock_node[to_sock])
        return nodes_to_update

    def _calc_cam_update_time(self) -> Iterable['SvNode']:
        """Return cumulative update time in order of node_group.nodes collection"""
        cum_time_nodes = dict()  # don't have frame nodes
        for node, prev_socks in self.__sort_nodes():
            prev_nodes = self._from_nodes[node]
            if len(prev_nodes) > 1:
                cum_time = sum(n.get(TIME_KEY, 0) for n in self.nodes_to([node]))
            else:
                cum_time = sum(cum_time_nodes.get(n, 0) for n in prev_nodes)
                cum_time += node.get(TIME_KEY, 0)
            cum_time_nodes[node] = cum_time
        return (cum_time_nodes.get(n) for n in self._tree.nodes)

    def _debug_color(self, walker: Generator, use_color: bool = True):
        """Colorize nodes which were previously executed. Before execution, it
        resets all dbug colors"""
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
    """It caches errors during execution of process method of a node and saves
    update time, update status and error"""

    # this probably can be inside the Node class as an update method
    # using context manager from contextlib has big overhead
    # https://stackoverflow.com/questions/26152934/why-the-staggering-overhead-50x-of-contextlib-and-the-with-statement-in-python
    def __init__(self, node: 'SvNode', supress=True):
        """:supress: if True any errors during node execution will be suppressed"""
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
            node_error_logger.error(exc_val, exc_info=True)
            self._node[UPDATE_KEY] = False
            self._node[ERROR_KEY] = repr(exc_val)

        if self._supress and exc_type is not None:
            if issubclass(exc_type, CancelError):
                return False
            return issubclass(exc_type, Exception)


def prepare_input_data(prev_socks: list[Optional[NodeSocket]],
                       input_socks: list[NodeSocket]):
    """Reads data from given outputs socket make it conversion if necessary and
    put data into input given socket"""
    # this can be a socket method
    for ps, ns in zip(prev_socks, input_socks):
        if ps is None:
            continue
        try:
            data = ps.sv_get()
        except SvNoDataError:
            # let to the node handle No Data error
            ns.sv_forget()
        else:
            # cast data
            if ps.bl_idname != ns.bl_idname:
                implicit_conversion = conversions[ns.default_conversion_name]
                data = implicit_conversion.convert(ns, ps, data)

            ns.sv_set(data)


def update_ui(tree: NodeTree, times: Iterable[float] = None):
    """Updates UI of the given tree
    :times: optional node timing in order of group_tree.nodes collection"""
    # probably this can be moved to tree.update_ui method
    errors = (n.get(ERROR_KEY, None) for n in tree.nodes)
    times = times or (n.get(TIME_KEY, 0) for n in tree.nodes)
    tree.update_ui(errors, times)
