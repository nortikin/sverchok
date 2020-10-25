from typing import Dict

from sverchok.utils.testing import SverchokTestCase
import sverchok.utils.tree_walk as tw


class TreeWalkTest(SverchokTestCase):
    def setUp(self):
        self.tree = Tree()
        #  1----2-----3-----4
        #            / \
        #  8---9----5   6---7
        #     /
        #   10
        nodes_relations = {
            # node_id: (input nodes, output nodes)
            1: ([], [2]),
            2: ([1], [3]),
            3: ([2, 5], [4, 6]),
            4: ([3], []),
            5: ([9], [3]),
            6: ([3], [7]),
            7: ([6], []),
            8: ([], [9]),
            9: ([8, 10], [5]),
            10: ([], [9])
        }
        nodes = {n_id: Node(n_id) for n_id in nodes_relations}
        for node_id, (inputs, outputs) in nodes_relations.items():
            nodes[node_id].last_nodes.extend(nodes[i] for i in inputs)
            nodes[node_id].next_nodes.extend(nodes[i] for i in outputs)
        self.tree.nodes.update(nodes)

    def test_dfs_walk(self):
        with self.subTest(msg="With empty walk"):
            self.assertEqual(list(self.tree.dfs_walk([])), [])
        with self.subTest(msg='Go forward'):
            self.assertCountEqual((n.id for n in self.tree.nodes[10].dfs_walk()), [10, 9, 5, 3, 6, 7, 4])
        with self.subTest(msg='Go forward, multiple nodes'):
            node_indexes_walk = [n.id for n in self.tree.dfs_walk([self.tree.nodes[i] for i in [1, 3]])]
            self.assertCountEqual(node_indexes_walk, [1, 2, 3, 6, 4, 7])
        with self.subTest(msg='Go backward'):
            self.assertCountEqual((n.id for n in self.tree.nodes[6].dfs_walk(direction='BACKWARD')),
                                  [6, 3, 2, 1, 5, 9, 10, 8])
        with self.subTest(msg='Go backward, multiple nodes'):
            node_indexes_walk = [n.id for n in self.tree.dfs_walk([self.tree.nodes[i] for i in [4, 6]],
                                                                  direction='BACKWARD')]
            self.assertCountEqual(node_indexes_walk, [4, 6, 3, 2, 1, 5, 9, 8, 10])

    def test_bfs_walk(self):
        with self.subTest(msg="With empty walk"):
            self.assertCountEqual(list(self.tree.bfs_walk([])), [])
        with self.subTest(msg="Go forward"):
            self.assertCountEqual((n.id for n in self.tree.nodes[2].bfs_walk()), [2, 3, 6, 4, 7])
        with self.subTest(msg="Go forward, multiple nodes"):
            node_indexes = (n.id for n in self.tree.bfs_walk([self.tree.nodes[i] for i in [1, 5]]))
            self.assertCountEqual(node_indexes, [1, 2, 3, 4, 5, 6, 7])
        with self.subTest(msh="Go backward"):
            self.assertCountEqual((n.id for n in self.tree.nodes[3].bfs_walk(direction='BACKWARD')),
                                  [3, 2, 1, 5, 9, 8, 10])
        with self.subTest(msg="Go backward, multiple nodes"):
            node_indexes = (n.id for n in self.tree.bfs_walk([self.tree.nodes[i] for i in [4, 6]],
                                                             direction='BACKWARD'))
            self.assertCountEqual(node_indexes, [6, 4, 3, 2, 1, 5, 9, 8, 10])

    def test_input_output_nodes(self):
        with self.subTest(msg="Input nodes search"):
            self.assertCountEqual((n.id for n in self.tree.input_nodes), [1, 8, 10])
        with self.subTest(msg="Output nodes search"):
            self.assertCountEqual((n.id for n in self.tree.output_nodes), [4, 7])


class Tree(tw.Tree):
    def __init__(self):
        self._nodes = dict()

    @property
    def nodes(self) -> Dict[int, 'Node']:
        return self._nodes


class Node(tw.Node):
    def __init__(self, node_id):
        self.id: int = node_id
        self._next_nodes = []
        self._last_nodes = []

    @property
    def next_nodes(self):
        return self._next_nodes

    @property
    def last_nodes(self):
        return self._last_nodes

    def __repr__(self):
        return f'<Node={self.id}>'


if __name__ == '__main__':
    import unittest
    unittest.main(exit=False)
