
import collections
import unittest

from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.core.update_system import make_dep_dict, make_update_list
#from sverchok.tests.mocks import *

class UpdateSystemTests(ReferenceTreeTestCase):

    reference_file_name = "complex_1_ref.blend.gz"

    def test_make_dep_dict(self):
        tree = get_node_tree()
        result = make_dep_dict(tree)
        #info(result)

        expected_result = {'Bevel': {'Box'}, 'VD Experimental': {'Bevel'}, 'Extrude Separate Faces': {'Box'}, 'Bevel.001': {'Extrude Separate Faces'}, 'Move': {'Bevel.001', 'Vector in'}, 'VD Experimental.001': {'Move', 'Bevel.001'}}

        #info("Dict: %s", result)
        self.assertEqual(result, expected_result)

    def test_make_update_list(self):
        tree = get_node_tree()
        result = make_update_list(tree)
        #info(result)

        # We can't test for exact equality of result and some expected_result,
        # because exact order depends on order of items in defaultdict(),
        # which may change from one run to another.
        # So we just test that each node is updated after all its dependencies.
        for node, deps in make_dep_dict(tree).items():
            node_idx = result.index(node)
            for dep in deps:
                dep_idx = result.index(dep)
                self.assertTrue(dep_idx < node_idx)

