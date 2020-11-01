import sverchok
from sverchok.utils.testing import SverchokTestCase
import sverchok.utils.tree_structure as ts
from sverchok.utils.sv_json_import import JSONImporter


class TreeStructureTest(SverchokTestCase):

    def test_generating_tree_structure(self):

        examples_path = Path(sverchok.__file__).parent / 'json_examples'

        with self.temporary_node_tree("ImportedTree") as new_tree:
            new_tree.sv_process = False
            importer = JSONImporter.init_from_path(str(examples_path / "Architecture" / "ProfileBuilding.json"))
            importer.import_into_tree(new_tree, print_log=False)
            tree = ts.Tree(new_tree)
            self.are_trees_equal(new_tree, tree)

            with self.subTest(msg="Detecting changes in tree collections"):
                new_tree.nodes.remove(tree.nodes['Number Range.001'].bl_tween)
                changed_tree = ts.Tree(new_tree)
                self.assertCountEqual(tree.nodes - changed_tree.nodes, (tree.nodes['Number Range.001'], ))
                self.assertCountEqual(tree.links - changed_tree.links, tree.nodes['Number Range.001'].outputs[0].links)
                self.assertRaises(TypeError, lambda: tree.nodes - {'Name 1', 'Name 2'})

                tree.nodes['Note'].bl_tween.inputs.remove(tree.nodes['Note'].inputs[0].get_bl_socket(new_tree))
                self.assertRaises(LookupError, tree.nodes['Note'].inputs[0].get_bl_socket, new_tree)

    def are_trees_equal(self, bl_tree, tree: ts.Tree):
        self.assertEqual(len(bl_tree.nodes), len(tree.nodes), msg="Wrong number of nodes")
        self.assertEqual(len(bl_tree.links), len(tree.links), msg="Wrong number of links")
        self.assertEqual(bl_tree.name, tree.bl_tween.name)
        self.assertEqual(bl_tree.tree_id, tree.id)
        for i, bl_node in enumerate(bl_tree.nodes):
            with self.subTest(msg=f'Check copy of "{bl_node.name}" node'):
                node: ts.Node = tree.nodes[bl_node.name]
                self.assertEqual(bl_node.name, node.name, msg="Node in nodes collection bu wrong name")
                self.assertEqual(i, node.index)
                self.assertEqual(bl_node.name, node.get_bl_node(bl_tree).name)
                self.assertEqual(bl_node.name, node.bl_tween.name)
                self.assertEqual(len(bl_node.inputs), len(node.inputs))
                self.assertEqual(len(bl_node.outputs), len(node.outputs))
                for s_i, bl_socket in enumerate(bl_node.inputs):
                    socket: ts.Socket = node.inputs[s_i]
                    self.assertEqual(socket.is_output, False)
                    self.assertEqual(bl_socket.identifier, socket.identifier)
                    self.assertIs(node, socket.node)
                    self.assertEqual(socket.index, s_i)
                    self.assertEqual(bl_socket.identifier, socket.get_bl_socket(bl_tree).identifier)
                    self.assertEqual(bl_socket.is_linked, bool(socket.links))
                for s_i, bl_socket in enumerate(bl_node.outputs):
                    socket: ts.Socket = node.outputs[s_i]
                    self.assertEqual(socket.is_output, True)
                    self.assertEqual(bl_socket.identifier, socket.identifier)
                    self.assertIs(node, socket.node)
                    self.assertEqual(socket.index, s_i)
                    self.assertEqual(bl_socket.identifier, socket.get_bl_socket(bl_tree).identifier)
                    self.assertEqual(bl_socket.is_linked, bool(socket.links))

        for i, (bl_link, link) in enumerate(zip(bl_tree.links, tree.links)):
            with self.subTest(msg=f'Check copy of link from={bl_link.from_node} to={bl_link.to_node}'):
                link: ts.Link
                self.assertEqual(bl_link.from_socket.identifier, link.from_socket.identifier)
                self.assertEqual(bl_link.to_socket.identifier, link.to_socket.identifier)
                self.assertEqual(i, link.index)
                self.assertEqual(bl_link.from_node.name, link.from_node.name)
                self.assertEqual(bl_link.to_node.name, link.to_node.name)

        self.assertTrue('Inset faces.001' in tree.nodes)
        self.assertCountEqual((n.name for n in tree.nodes['Inset faces.001'].next_nodes), ('Mesh viewer', 'Switch.001'))
        self.assertCountEqual((n.name for n in tree.nodes['Profile Parametric Mk3.001'].last_nodes),
                              ('Formula.001', 'Number Range.004', 'Number Range.003', 'Number Range.002', 'Formula'))
        self.assertRaises(LookupError, tree.nodes['Inset faces.001'].get_input_socket, ('False name', ))
        self.assertRaises(LookupError, tree.nodes['Inset faces.001'].get_output_socket, ('False name', ))

        with self.subTest(msg="Test update method"):
            self.assertEqual(tree.nodes['Frame'].is_updated, False)
            tree.nodes['Frame'].update()
            self.assertEqual(tree.nodes['Frame'].is_updated, True)


if __name__ == '__main__':
    import unittest
    from coverage import Coverage
    from pathlib import Path

    cov = Coverage()
    cov.start()
    unittest.main(exit=False)
    cov.stop()
    cov.save()
    cov.html_report(ignore_errors=True)
