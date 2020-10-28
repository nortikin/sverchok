from pathlib import Path

import bpy

import sverchok
from sverchok.utils.testing import SverchokTestCase, unittest
from sverchok.utils.sv_json_import import JSONImporter


class GroupingTest(SverchokTestCase):

    @unittest.skip("On Travis it is lunched looks like without UI and it can't tests operators in this way")
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


if __name__ == '__main__':
    unittest.main(exit=False)
