
from sverchok.core.socket_conversions import ImplicitConversionProhibited
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

class SocketConversionTests(EmptyTreeTestCase):
    
    def test_vertices_to_matrices(self):
        """
        Test that cyl -> viewer text works.
        """

        cyl = create_node("CylinderNode")
        cyl.Separate = True
        viewer_text = create_node("ViewerNodeTextMK3")

        # Connect NGon node to MatrixApply node
        self.tree.links.new(cyl.outputs['Vertices'], viewer_text.inputs[0])

        # Trigger processing of NGon node
        cyl.process()
        # Read what ViewerText node sees
        data = viewer_text.inputs[0].sv_get()