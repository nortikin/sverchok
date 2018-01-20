
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info

# Some "smoke tests" for simple generator nodes.
# These test cases exist mostly in demonstration purposes,
# I hardly think anyone is going to break them "just that easy".
# Failure of these tests can also indicate that something
# is badly broken in general node processing mechanism.

class ViewerTextNodeTest(NodeProcessTestCase):
    node_bl_idname = "ViewerNodeTextMK3"

    def test_box(self):
        # It is not in general necessary to set properties of the node
        # to their default values.
        # However you may consider setting them, to exclude influence of
        # node_defaults mechanism.
        self.node.inputs[0] = [[[1,2,3,4],[2,3,4,5]],[[3,4,5,6],[4,5,6,7]]]
        
        # This one is necessary
        self.node.process()