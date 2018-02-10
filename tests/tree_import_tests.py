
import unittest
import json
from os.path import join, dirname, basename
from glob import glob

import sverchok
from sverchok.old_nodes import is_old
from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import import_tree

class ScriptUvImportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            import_tree(new_tree, self.get_reference_file_path("script_uv.json"))

            # Check links
            self.assert_nodes_linked("ImportedTree", "Scripted Node Lite", "verts", "UV Connection", "vertices")
            self.assert_nodes_linked("ImportedTree", "UV Connection", "vertices", "Viewer Draw", "vertices")
            self.assert_nodes_linked("ImportedTree", "UV Connection", "data", "Viewer Draw", "edg_pol")

            # Check random node properties
            self.assert_node_property_equals("ImportedTree", "UV Connection", "cup_U", False)
            self.assert_node_property_equals("ImportedTree", "UV Connection", "polygons", 'Edges')
            self.assert_node_property_equals("ImportedTree", "UV Connection", "dir_check", 'U_dir')

class ProfileImportTest(ReferenceTreeTestCase):

    reference_file_name = "profile_ref.blend.gz"

    def test_profile_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            import_tree(new_tree, self.get_reference_file_path("profile.json"))

class MeshExprImportTest(ReferenceTreeTestCase):

    reference_file_name = "mesh_expr_ref.blend.gz"

    def test_mesh_expr_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            import_tree(new_tree, self.get_reference_file_path("mesh.json"))

class MonadImportTest(ReferenceTreeTestCase):

    reference_file_name = "monad_1_ref.blend.gz"

    def test_monad_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            import_tree(new_tree, self.get_reference_file_path("monad_1.json"))
            self.assert_node_property_equals("ImportedTree", "Monad", "amplitude", 0.6199999451637268)

@batch_only
class ExamplesImportTest(SverchokTestCase):
    def test_import_examples(self):
        sv_init = sverchok.__file__
        examples_dir = join(dirname(sv_init), "json_examples")

        for path in glob(join(examples_dir, "*.json")):
            name = basename(path)
            with self.subTest(file=name):
                info("Importing: %s", name)
                with self.temporary_node_tree("ImportedTree") as new_tree:
                    with self.assert_logs_no_errors():
                        # Do not try to process imported tree,
                        # that will just take time anyway
                        new_tree.sv_process = False
                        import_tree(new_tree, path)
                    for node in new_tree.nodes:
                        if is_old(node):
                            self.fail("This example contains deprecated node `{}' ({}). Please upgrade the example file.".format(node.name, node.bl_idname))


