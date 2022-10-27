import bpy

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.modules_inspection import iter_classes_from_module
import sverchok


class NodesAPITest(SverchokTestCase):

    def test_using_update_method(self):
        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            self.assertNotIn('update', node_class.__dict__,
                             f"Usage of 'update' method is found in node class: {node_class.__name__}."
                             f" This method is reserved for updates detection only.")

    def test_register_node(self):
        """All nodes should be either registered or saved as dummy nodes"""
        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            bl_class = bpy.types.Node.bl_rna_get_subclass_py(node_class.bl_idname)
            if bl_class is None and not node_class.missing_dependency:
                with self.subTest(node=node_class.bl_idname):
                    self.assertIsNotNone(
                        bl_class,
                        msg=f"{node_class=} is not registered")

    def test_enum_items(self):
        """All Enums should keep references of their items
        https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty
        https://github.com/nortikin/sverchok/issues/4316"""
        checked_nodes = {
            ('SvMeshFilterNode', 'submode'),  # it stores a reference to the items
            ('SvUVtextureNode', 'objects'),  # it seems does not appear in UI
        }

        def is_enum_keep_refs(prop_):
            item_func = prop_.keywords['items']
            if callable(item_func) and not hasattr(item_func, 'keep_ref'):
                return False
            return True

        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            for identifier, prop in node_class.__annotations__.items():
                if not isinstance(prop, bpy.props._PropertyDeferred):
                    continue
                if 'items' not in prop.keywords:
                    continue
                if (node_class.bl_idname, identifier) in checked_nodes:
                    continue
                with self.subTest(node=node_class.bl_idname, enum=identifier):
                    self.assertTrue(
                        is_enum_keep_refs(prop),
                        msg=f"Make sure that the {node_class=} store its items"
                            f" in memory and add its bl_idname to the exception list"
                            f" or add 'keep_enum_reference' decorator to the enum function")
