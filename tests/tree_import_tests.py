
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import import_tree

class ScriptUvImportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_import(self):
        new_tree = get_or_create_node_tree("ImportedTree")
        import_tree(new_tree, self.get_reference_file_path("script_uv.json"))
        remove_node_tree("ImportedTree")

class ProfileImportTest(ReferenceTreeTestCase):

    reference_file_name = "profile_ref.blend.gz"

    def test_profile_import(self):
        new_tree = get_or_create_node_tree("ImportedTree")
        import_tree(new_tree, self.get_reference_file_path("profile.json"))
        remove_node_tree("ImportedTree")

class MeshExprImportTest(ReferenceTreeTestCase):

    reference_file_name = "mesh_expr_ref.blend.gz"

    def test_mesh_expr_import(self):
        new_tree = get_or_create_node_tree("ImportedTree")
        import_tree(new_tree, self.get_reference_file_path("mesh.json"))
        remove_node_tree("ImportedTree")

