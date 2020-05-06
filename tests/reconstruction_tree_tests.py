from itertools import count
from operator import setitem

from sverchok.utils.testing import SverchokTestCase

import sverchok.core.events as ev


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
            sv_link = ev.SvLink(link_id, from_node, to_node)
            from_node.outputs[link_id] = sv_link
            to_node.inputs[link_id] = sv_link
            return sv_link

        tree = ev.SvTree(next_id())
        nodes = [ev.SvNode(next_id(), f"{i+1}") for i in range(10)]
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
        self.walk_tree = ev.WalkSvTree(tree)
        self.walk_tree.output_nodes.add(tree.nodes['4'])
        self.tree = tree

    def test_walk_sv_tree(self):
        self.walk_tree.recalculate_connected_to_output_nodes()
        nodes_connected_to_ouput = set([self.tree.nodes[str(i)] for i in [4, 3, 2, 1, 5, 9, 10, 8]])
        self.assertEqual(self.walk_tree.nodes_connected_to_output, nodes_connected_to_ouput)

        changed_nodes = [self.tree.nodes[str(i)] for i in [2, 9]]
        self.walk_tree.recalculate_effected_by_changes_nodes(changed_nodes)
        effected_nodes = set([self.tree.nodes[str(i)] for i in [2, 3, 4, 9, 5, 6, 7]])
        self.assertEqual(self.walk_tree.effected_by_changes_nodes, effected_nodes)

        walker = self.walk_tree.walk_on_worth_recalculating_nodes(changed_nodes)
        visited_nodes = set()
        visited_nodes.add(next(walker))
        visited_nodes.add(next(walker))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2]]))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2, 3]]))
        visited_nodes.add(next(walker))
        self.assertEqual(visited_nodes, set([self.tree.nodes[str(i)] for i in [9, 5, 2, 3, 4]]))

        walker = self.walk_tree.walk_on_worth_recalculating_nodes([self.tree.nodes['6']])
        self.assertRaises(StopIteration, next, walker)

        walker = self.walk_tree.walk_on_worth_recalculating_nodes([self.tree.nodes['4']])
        self.assertEqual(next(walker), self.tree.nodes['4'])
