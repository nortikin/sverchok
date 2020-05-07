from itertools import count
from operator import setitem

from sverchok.utils.testing import SverchokTestCase

import sverchok.core.tree_reconstruction as rec


class WalkTreeTest(SverchokTestCase):
    def setUp(self):
        #  1----2-----3-----4
        #            / \
        #  8---9----5   6---7
        #     /
        #   10
        # 4 nod id output node because it is  in OUTPUT_NODE_BL_IDNAMES set
        # in this case the 6,7 nodes will never be calculated
        # 2,10 are changed nodes by their parameters
        # the goal is visit 10-9-5-2-3-4 nodes in this order

        def next_id(counter=count()):
            return str(next(counter))

        def add_link(link_id, from_node, to_node):
            sv_link = rec.SvLink(link_id, from_node, to_node)
            from_node.outputs[link_id] = sv_link
            to_node.inputs[link_id] = sv_link
            return sv_link

        tree = rec.SvTree(next_id())
        nodes = [rec.SvNode(next_id(), f"{i + 1}") for i in range(10)]
        [setattr(node, 'is_outdated', False) for node in nodes]
        [setitem(tree.nodes._nodes, node.id, node) for node in nodes]
        links_data = [(next_id(), tree.nodes['1'], tree.nodes['2']),
                      (next_id(), tree.nodes['2'], tree.nodes['3']),
                      (next_id(), tree.nodes['3'], tree.nodes['4']),
                      (next_id(), tree.nodes['5'], tree.nodes['3']),
                      (next_id(), tree.nodes['3'], tree.nodes['6']),
                      (next_id(), tree.nodes['8'], tree.nodes['9']),
                      (next_id(), tree.nodes['9'], tree.nodes['5']),
                      (next_id(), tree.nodes['6'], tree.nodes['7']),
                      (next_id(), tree.nodes['10'], tree.nodes['9']),
                      ]
        [setitem(tree.links._links, link.id, link) for link in [add_link(*data) for data in links_data]]
        tree.walk.output_nodes.add(tree.nodes['4'])
        self.tree = tree

    def test_walk_sv_tree(self):
        self.tree.walk.recalculate_connected_to_output_nodes()
        nodes_connected_to_ouput = set([self.tree.nodes[str(i)] for i in [4, 3, 2, 1, 5, 9, 10, 8]])
        self.assertEqual(self.tree.walk.nodes_connected_to_output, nodes_connected_to_ouput)

        self.tree.nodes['2'].is_outdated = True
        self.tree.nodes['9'].is_outdated = True
        self.tree.walk.recalculate_effected_by_changes_nodes()
        effected_nodes = set([self.tree.nodes[str(i)] for i in [2, 3, 4, 9, 5, 6, 7]])
        self.assertEqual(self.tree.walk.effected_by_changes_nodes, effected_nodes)

        walker = self.tree.walk.walk_on_worth_recalculating_nodes()
        visited_nodes = set()
        visited_nodes.add(next(walker))
        visited_nodes.add(next(walker))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2]]))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2, 3]]))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2, 3, 4]]))

        self.tree.nodes['2'].is_outdated = False
        self.tree.nodes['9'].is_outdated = False
        self.tree.nodes['6'].is_outdated = True
        walker = self.tree.walk.walk_on_worth_recalculating_nodes()
        self.assertRaises(StopIteration, next, walker)

        self.tree.nodes['6'].is_outdated = False
        self.tree.nodes['4'].is_outdated = True
        walker = self.tree.walk.walk_on_worth_recalculating_nodes()
        self.assertEqual(next(walker), self.tree.nodes['4'])
