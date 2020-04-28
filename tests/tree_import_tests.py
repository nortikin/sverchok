
import unittest
import json
from os.path import join, dirname, basename
from glob import glob
from pathlib import Path

import sverchok
from sverchok.old_nodes import is_old
from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import import_tree
from sverchok.utils.sv_examples_utils import examples_paths

class ScriptUvImportTest(SverchokTestCase):

    def test_script_uv_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            with self.assert_logs_no_errors():
                import_tree(new_tree, self.get_reference_file_path("script_uv.json"))

            # Check links
            self.assert_nodes_linked("ImportedTree", "Scripted Node Lite", "verts", "UV Connection", "vertices")
            self.assert_nodes_linked("ImportedTree", "UV Connection", "vertices", "Viewer Draw", "verts")
            self.assert_nodes_linked("ImportedTree", "UV Connection", "data", "Viewer Draw", "edges")

            # Check random node properties
            self.assert_node_property_equals("ImportedTree", "UV Connection", "cap_U", False)
            self.assert_node_property_equals("ImportedTree", "UV Connection", "polygons", 'Edges')
            self.assert_node_property_equals("ImportedTree", "UV Connection", "dir_check", 'U_dir')

class ProfileImportTest(SverchokTestCase):

    def test_profile_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            with self.assert_logs_no_errors():
                import_tree(new_tree, self.get_reference_file_path("profile.json"))

class MeshExprImportTest(SverchokTestCase):

    def test_mesh_expr_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            with self.assert_logs_no_errors():
                import_tree(new_tree, self.get_reference_file_path("mesh.json"))

class MonadImportTest(SverchokTestCase):

    def test_monad_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            with self.assert_logs_no_errors():
                import_tree(new_tree, self.get_reference_file_path("monad_1.json"))
            self.assert_node_input_equals("ImportedTree", "Monad", "Num X", [[4]])


# to keep automated tests from breaking, i've collected a list of examples that need to be skipped
# because they 
#  1) require .blend data (greasepencil strokes) or
#  2) 3rd party python modules (mcubes, conway)

UNITTEST_BLACKLIST = [
    "GreacePencil_injection.json",
    "pointsONface_gather_lines.json",
    "Generative_Art_Lsystem.json",
    "Genetic_algorithm.blend.json",
    "Elfnor_topology_nodes.json",
    "l-systems.json",
    "waffle.json"
]

@batch_only
class ExamplesImportTest(SverchokTestCase):
    def test_import_examples(self):

        for cat in examples_paths:

            if not examples_paths.get(cat):
                info("Dir named: %s is empty", cat)
                continue

            info("Opening Dir named: %s", cat)

            examples_set = Path(examples_paths.get(cat))
            for listed_path in examples_set.iterdir():

                # cast from Path class to dumb string.
                path = str(listed_path)

                # assuming these are all jsons for now.
                name = basename(path)

                if name in UNITTEST_BLACKLIST:
                    info("Skipping (blacklisted) : %s to permit unit tests to continue", name)
                    continue

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
                                error_format = "This example contains deprecated node `{}' ({}). Please upgrade the example file." 
                                self.fail(error_format.format(node.name, node.bl_idname))

