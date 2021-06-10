from sverchok.utils.testing import *
from sverchok.utils.sv_json_import import FailsLog
from sverchok.utils.sv_json_struct import FileStruct
from sverchok.utils.modules_inspection import iter_classes_from_module


class ExportImportEachNode(EmptyTreeTestCase):

    @property
    def known_troubles(self) -> set:
        return {'SvScriptNodeLite', 'SvTextInNodeMK2'}

    def test_export_import_all_nodes_new(self):
        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            if node_class.bl_idname in self.known_troubles or node_class.bl_idname in self.new_known_troubles:
                continue

            try:
                create_node(node_class.bl_idname, self.tree.name)
            except RuntimeError:  # the node probably was not registered for missing dependencies
                pass
            else:
                structure = None
                with self.subTest(type='NEW EXPORT', node=node_class.bl_idname):
                    with self.assert_logs_no_errors():
                        structure = FileStruct().export_tree(self.tree)
                if structure is not None:
                    with self.subTest(type='NEW IMPORT', node=node_class.bl_idname):
                        with self.assert_logs_no_errors():
                            logger = FailsLog()
                            FileStruct(None, logger, structure).build_into_tree(self.tree)
                            if logger.has_fails:
                                raise (ImportError(logger.fail_message))
            finally:
                # you have to clean tree by yourself
                self.tree.nodes.clear()

    @property
    def new_known_troubles(self) -> set:
        return {'SvObjInLite',  # this one just unable to save empty object
                }


if __name__ == '__main__':
    import unittest
    unittest.main(exit=False)
