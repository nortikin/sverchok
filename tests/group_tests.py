from pathlib import Path

import bpy

import sverchok
from sverchok.utils.testing import SverchokTestCase, unittest
from sverchok.utils.sv_json_import import JSONImporter


class GroupingTest(SverchokTestCase):

    @unittest.skipIf(bpy.app.background, "Blender should be lunched with UI")
    def test_grouping_nodes(self):

        examples_path = Path(sverchok.__file__).parent / 'json_examples'

        with self.temporary_node_tree("ImportedTree") as new_tree:
            bpy.context.area.ui_type = 'SverchCustomTreeType'
            bpy.context.space_data.node_tree = new_tree
            with self.assert_logs_no_errors():  # just in case if the operators will get logger someday
                new_tree.sv_process = False
                importer = JSONImporter.init_from_path(
                    str(examples_path / "Architecture" / "Power_transmission_tower.json"))
                importer.import_into_tree(new_tree, print_log=False)
                [setattr(n, 'select', False) for n in new_tree.nodes]
                [setattr(new_tree.nodes[n], 'select', True) for n in ['A Number', 'Formula',
                                                                      'Vector polar input', 'Vector polar output']]
                with self.subTest(msg="Grouping nodes"):
                    bpy.ops.node.add_group_tree_from_selected()
                with self.subTest(msg="Ungrouping nodes"):
                    bpy.context.space_data.path.pop()
                    [setattr(n, 'select', False) for n in new_tree.nodes]
                    group_node, *_ = [n for n in new_tree.nodes if hasattr(n, 'node_tree')]
                    group_node.select = True
                    bpy.ops.node.ungroup_group_tree({'node': group_node})


class GroupInputDefaultsTest(SverchokTestCase):
    """Regression test for #5286 - group node sockets should pick up the
    default values configured on the group tree's interface sockets.
    """

    def _new_interface_socket(self, sub_tree, name, socket_type, in_out='INPUT'):
        if bpy.app.version >= (4, 0):
            return sub_tree.interface.new_socket(
                name=name, in_out=in_out, socket_type=socket_type)
        socks = sub_tree.inputs if in_out == 'INPUT' else sub_tree.outputs
        return socks.new(socket_type, name)

    @unittest.skipIf(bpy.app.background, "Blender should be lunched with UI")
    def test_default_value_propagates_to_group_node_socket(self):
        with self.temporary_node_tree("DefaultsTestTree") as new_tree:
            bpy.context.area.ui_type = 'SverchCustomTreeType'
            bpy.context.space_data.node_tree = new_tree
            new_tree.sv_process = False

            sub_tree = bpy.data.node_groups.new('Sverchok group defaults', 'SvGroupTree')
            sub_tree.use_fake_user = True
            try:
                interface_sock = self._new_interface_socket(
                    sub_tree, 'Size', 'SvStringsSocket')
                interface_sock.default_type = 'float'
                interface_sock.default_float_value = 4.2

                group_node = new_tree.nodes.new('SvGroupTreeNode')
                group_node.group_tree = sub_tree

                self.assertTrue(len(group_node.inputs) >= 1)
                node_sock = group_node.inputs[0]
                self.assertAlmostEqual(
                    node_sock.default_property, 4.2, places=5,
                    msg="interface default value should be copied to the new group node socket")
            finally:
                bpy.data.node_groups.remove(sub_tree)


if __name__ == '__main__':
    unittest.main(exit=False)
