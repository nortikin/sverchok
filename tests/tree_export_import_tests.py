import traceback

from sverchok.core import upgrade_nodes
from sverchok.utils.testing import *
from sverchok.utils.sv_json_export import JSONExporter


class ScriptUvExportTest(ReferenceTreeTestCase):

    reference_file_name = "script_uv_ref.blend.gz"

    def test_script_uv_export(self):
        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))


class ProfileExportTest(ReferenceTreeTestCase):

    reference_file_name = "profile_ref.blend.gz"

    def setUp(self):
        # We have to load text block as well
        self.link_text_block("Profile.txt")
        self.maxDiff = None
        super().setUp()

    def test_profile_export(self):

        try:
            upgrade_nodes.upgrade_nodes(self.tree)
        except:
            traceback.print_exc()

        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))


class MeshExprExportTest(ReferenceTreeTestCase):

    reference_file_name = "mesh_expr_ref.blend.gz"

    def setUp(self):
        # We have to load text block as well
        self.link_text_block("Mesh Expression")
        super().setUp()

    def test_mesh_expr_export(self):
        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))


class MonadExportTest(ReferenceTreeTestCase):

    reference_file_name = "monad_1_ref.blend.gz"

    def setUp(self):
        self.link_node_tree(tree_name="PulledCube")
        super().setUp()

    @unittest.skip("Linking node tree with Monad node does not work correctly.")
    def test_monad_export(self):
        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))

    def tearDown(self):
        remove_node_tree("PulledCube")
        super().tearDown()


class ViewerTextExportTest(ReferenceTreeTestCase):

    reference_file_name = "viewer_text_2018_01_20_12_10.gz"

    def test_textview_expr_export(self):
        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))


class ListJoinImportTest(ReferenceTreeTestCase):

    reference_file_name = "list_join_import.blend.gz"

    def test_list_join_node_import(self):
        export_result = JSONExporter.get_tree_structure(self.tree)
        importer = JSONImporter(export_result)
        importer.import_into_tree(self.tree)
        if importer.has_fails:
            raise(ImportError(importer.fail_massage))
