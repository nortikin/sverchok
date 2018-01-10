
from sverchok.core.socket_conversions import ImplicitConversionProhibited
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

class SocketConversionTests(EmptyTreeTestCase):
    
    def test_vertices_to_matrices(self):
        """
        Test that vertices -> matrices conversion work correctly.
        """
        ngon = create_node("SvNGonNode")
        ngon.sides_ = 4
        matrix_apply = create_node("MatrixApplyNode")

        # Connect NGon node to MatrixApply node
        self.tree.links.new(ngon.outputs['Vertices'], matrix_apply.inputs['Matrixes'])

        # Trigger processing of NGon node
        ngon.process()
        # Read what MatrixApply node sees
        data = matrix_apply.inputs['Matrixes'].sv_get()

        # It should see this list of matrices.
        expected_data = [
                [(1.0, 0.0, 0.0, 1.0),
                 (0.0, 1.0, 0.0, 0.0),
                 (0.0, 0.0, 1.0, 0),
                 (0.0, 0.0, 0.0, 1.0)],
                [(1.0, 0.0, 0.0, 0.0),
                 (0.0, 1.0, 0.0, 1.0),
                 (0.0, 0.0, 1.0, 0),
                 (0.0, 0.0, 0.0, 1.0)],
                [(1.0, 0.0, 0.0, -1.0),
                 (0.0, 1.0, 0.0, 0),
                 (0.0, 0.0, 1.0, 0),
                 (0.0, 0.0, 0.0, 1.0)],
                [(1.0, 0.0, 0.0, 0),
                 (0.0, 1.0, 0.0, -1.0),
                 (0.0, 0.0, 1.0, 0),
                 (0.0, 0.0, 0.0, 1.0)]
            ]

        self.assert_sverchok_data_equal(data, expected_data, precision=8)

    def test_no_edges_to_verts(self):
        """
        Test that edges -> vertices conversion raises an exception.
        """

        ngon = create_node("SvNGonNode")
        matrix_apply = create_node("MatrixApplyNode")

        # Connect NGon node to MatrixApply node
        self.tree.links.new(ngon.outputs['Edges'], matrix_apply.inputs['Vectors'])

        # Trigger processing of NGon node
        ngon.process()

        with self.assertRaises(ImplicitConversionProhibited):
            # Try to read from Vectors input of MatrixApply node
            # This should raise an exception
            data = matrix_apply.inputs['Vectors'].sv_get()
            error(data)

