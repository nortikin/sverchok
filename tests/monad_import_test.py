from sverchok.utils.testing import *


class MonadImportTest(SverchokTestCase):

    def test_monad_import(self):
        with self.temporary_node_tree("ImportedTree") as new_tree:
            importer = JSONImporter.init_from_path(self.get_reference_file_path("monad_1.json"))
            importer.import_into_tree(new_tree, print_log=False)
            if importer.has_fails:
                raise (ImportError(importer.fail_massage))

            self.assert_node_input_equals("ImportedTree", "Monad", "Num X", [[4]])
