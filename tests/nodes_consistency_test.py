import bpy

from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.modules_inspection import iter_classes_from_module
import sverchok


class UsingMethodsTest(SverchokTestCase):

    def test_using_update_method(self):
        for cls in iter_classes_from_module(sverchok.nodes, [bpy.types.Node]):
            self.assertNotIn('update', cls.__dict__, f"Usage of 'update' method is found in node class: {cls.__name__}."
                                                     f" This method is reserved for updates detection only.")
