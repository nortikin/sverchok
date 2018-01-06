
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import import_tree

class ScriptUvImportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            import_tree(new_tree, self.get_reference_file_path("script_uv.json"))

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

