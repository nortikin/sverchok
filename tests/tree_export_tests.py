
import unittest
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import create_dict_of_tree

class ExportTreeTests(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_export(self):
        export_result = create_dict_of_tree(self.tree)
        print(json.dumps(export_result))

