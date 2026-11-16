from typing import Iterable
from types import SimpleNamespace

from sverchok.utils.testing import SverchokTestCase
from sverchok.core.update_system import SearchTree, UpdateTree


class TreeCleaningTest(SverchokTestCase):
    def test_tree_cleaning(self):
        file = "TreeCleaningTest.blend"
        with self.tree_from_file(file, "FromTree") as from_tree,\
                self.tree_from_file(file, "ToTree") as to_tree:
            f_tree = SearchTree(from_tree)
            t_tree = SearchTree(to_tree)

            self._assert_nodes_equal(f_tree._from_nodes.keys(),
                                     t_tree._from_nodes.keys())
            for f_n, t_n in zip(sorted(f_tree._from_nodes, key=lambda k: k.name),
                                sorted(t_tree._from_nodes, key=lambda k: k.name)):
                self._assert_node_equal(f_n, t_n)
                self._assert_nodes_equal(
                    f_tree._from_nodes[f_n],
                    t_tree._from_nodes[t_n],
                    msg=f'Node="{f_n.name}" has different previous nodes'
                )

            self._assert_nodes_equal(f_tree._to_nodes.keys(),
                                     t_tree._to_nodes.keys())
            for f_n, t_n in zip(sorted(f_tree._to_nodes, key=lambda k: k.name),
                                sorted(t_tree._to_nodes, key=lambda k: k.name)):
                self._assert_node_equal(f_n, t_n)
                self._assert_nodes_equal(
                    f_tree._to_nodes[f_n],
                    t_tree._to_nodes[t_n],
                    msg=f'Node="{f_n.name}" has different next nodes')

            self._assert_socks_equal(f_tree._from_sock.keys(),
                                     t_tree._from_sock.keys())
            for f_s, t_s in zip(sorted(f_tree._from_sock, key=_path),
                                sorted(t_tree._from_sock, key=_path)):
                self._assert_sock_equal(f_s, t_s)
                self._assert_sock_equal(f_tree._from_sock[f_s],
                                        t_tree._from_sock[t_s])

            self._assert_socks_equal(f_tree._to_socks.keys(),
                                     t_tree._to_socks.keys())
            for f_s, t_s in zip(sorted(f_tree._to_socks, key=_path),
                                sorted(t_tree._to_socks, key=_path)):
                self._assert_sock_equal(f_s, t_s)
                self._assert_socks_equal(f_tree._to_socks[f_s],
                                         t_tree._to_socks[t_s])

            f_links = {(_path(s1), _path(s2)) for s1, s2 in f_tree._links}
            t_links = {(_path(s1), _path(s2)) for s1, s2 in t_tree._links}
            self.assertSetEqual(f_links, t_links)

    def _assert_sock_equal(self, sock1, sock2):
        self.assertEqual(sock1.node.name, sock2.node.name)
        self.assertEqual(sock1.name, sock2.name)

    def _assert_socks_equal(self, socks1, socks2):
        self.assertSetEqual(
            set(_path(s) for s in socks1),
            set(_path(s) for s in socks2)
        )

    def _assert_node_equal(self, node1, node2):
        self.assertEqual(node1.name, node2.name)

    def _assert_nodes_equal(self, nodes1, nodes2, msg=None):
        f_ns = set(_to_names(nodes1))
        t_ns = set(_to_names(nodes2))
        if msg is not None:
            msg = f'{msg}\n' \
                  f'   nodes1={f_ns}\n' \
                  f'   nodes2={t_ns}'
        self.assertSetEqual(f_ns, t_ns, msg=msg)


def _to_names(nodes: Iterable) -> Iterable[str]:
    for n in nodes:
        yield n.name


def _path(socket):
    return f"{socket.node.name}|{'out' if socket.is_output else 'in'}|{socket.name}"


class UpdateDifferenceTest(SverchokTestCase):
    def test_new_link_from_already_connected_output(self):
        source, heavy, receiver = object(), object(), object()
        output, heavy_input, receiver_input = object(), object(), object()
        old_link = (output, heavy_input)
        new_link = (output, receiver_input)

        old = SimpleNamespace(
            _from_nodes={source: set(), heavy: {source}, receiver: set()},
            _links={old_link},
            _from_sock={heavy_input: output},
            _to_socks={output: {heavy_input}},
        )
        new = SimpleNamespace(
            _from_nodes={source: set(), heavy: {source}, receiver: {source}},
            _links={old_link, new_link},
            _sock_node={output: source, heavy_input: heavy, receiver_input: receiver},
        )

        # The heavy branch must remain up to date.
        self.assertSetEqual(UpdateTree._update_difference(new, old), {receiver})

    def test_first_link_from_previously_unused_output(self):
        source, receiver = object(), object()
        output, receiver_input = object(), object()

        old = SimpleNamespace(
            _from_nodes={source: set(), receiver: set()},
            _links=set(),
            _from_sock={},
            _to_socks={},
        )
        new = SimpleNamespace(
            _from_nodes={source: set(), receiver: {source}},
            _links={(output, receiver_input)},
            _sock_node={output: source, receiver_input: receiver},
        )

        # Some nodes calculate their outputs only when an output is linked.
        self.assertSetEqual(UpdateTree._update_difference(new, old), {source})
