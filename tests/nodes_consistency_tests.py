import bpy

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.modules_inspection import iter_classes_from_module
import sverchok
from sverchok.utils.dummy_nodes import is_dependent


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
            if bl_class is None and not is_dependent(node_class.bl_idname):
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

        def is_enum_keep_refs(bl_class_, prop_identifier):
            prop = bl_class_.bl_rna.properties[prop_identifier]
            if prop.enum_items:
                return True
            item_func = bl_class_.__annotations__[prop_identifier].keywords['items']
            return hasattr(item_func, 'keep_ref')

        for node_class in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            bl_class = bpy.types.Node.bl_rna_get_subclass_py(node_class.bl_idname)
            if bl_class is None:
                continue
            for enum in bl_class.bl_rna.properties:
                if (node_class.bl_idname, enum.identifier) in checked_nodes:
                    continue
                if enum.type == 'ENUM':
                    with self.subTest(node=node_class.bl_idname, enum=enum.identifier):
                        self.assertTrue(
                            is_enum_keep_refs(bl_class, enum.identifier),
                            msg=f"Make sure that the {node_class=} store its items"
                                f" in memory and add its bl_idname to the exception list"
                                f" or add 'keep_enum_reference' decorator to the enum function")
