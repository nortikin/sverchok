
import unittest
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import create_dict_of_tree

class ScriptUvExportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_export(self):
        export_result = create_dict_of_tree(self.tree)
        self.assert_json_equals_file(export_result, "script_uv.json")

class ProfileExportTest(ReferenceTreeTestCase):

    reference_file_name = "profile_ref.blend.gz"

    def test_profile_export(self):
        export_result = create_dict_of_tree(self.tree)
        self.assert_json_equals_file(export_result, "profile.json")

class MeshExprExportTest(ReferenceTreeTestCase):

    reference_file_name = "mesh_expr_ref.blend.gz"

    def setUp(self):
        # We have to load text block as well
        self.link_text_block("Mesh Expression")
        super().setUp()

    def test_mesh_expr_export(self):
        export_result = create_dict_of_tree(self.tree)
        self.assert_json_equals_file(export_result, "mesh.json")

