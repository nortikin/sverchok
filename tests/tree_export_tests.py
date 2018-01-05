
import unittest
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import create_dict_of_tree

class ScriptUvExportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_export(self):
        export_result = create_dict_of_tree(self.tree)
        print(json.dumps(export_result))

class ProfileExportTest(ReferenceTreeTestCase):

    reference_file_name = "profile_ref.blend.gz"

    def test_profile_export(self):
        export_result = create_dict_of_tree(self.tree)
        print(json.dumps(export_result))

class MeshExprExportTest(ReferenceTreeTestCase):

    reference_file_name = "mesh_expr_ref.blend.gz"

    def setUp(self):
        # We have to load text block as well
        link_text_block(self.get_reference_file_path(), "Mesh Expression")
        super().setUp()

    def test_mesh_expr_export(self):
        export_result = create_dict_of_tree(self.tree)

        # JSON of Mesh Expression is too fancy to write it here inline
        with open(self.get_reference_file_path("mesh.json"), 'rb') as f:
            data = f.read().decode('utf8')
            expected_result = json.loads(data)

            self.assert_json_equals(export_result, expected_result)

