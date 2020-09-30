from sverchok.utils.testing import *
from sverchok.utils.sv_json_export import JSONExporter
from sverchok.utils.modules_inspection import iter_classes_from_module


class ExportImportEachNode(EmptyTreeTestCase):

    def test_export_import_all_nodes(self):
        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            try:
                create_node(node_class.bl_idname, self.tree.name)
            except RuntimeError:  # the node probably was not registered for missing dependencies
                pass
            else:
                tree_structure = None
                with self.subTest(type='EXPORT', node=node_class.bl_idname):
                    tree_structure = JSONExporter.get_tree_structure(self.tree)
                if tree_structure is not None:
                    with self.subTest(type='IMPORT', node=node_class.bl_idname):
                        JSONImporter(tree_structure).import_into_tree(self.tree)
            finally:
                # you have to clean tree by yourself
                self.tree.nodes.clear()
