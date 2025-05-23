
from sverchok.utils.testing import *


class TextViewerTest(EmptyTreeTestCase):

    def test_text_viewer(self):

        cyl = create_node("SvCylinderNodeMK2")
        cyl.Separate = True
        viewer_text = create_node("ViewerNodeTextMK3")

        # Connect Cylinder -> Viewer
        self.tree.links.new(cyl.outputs['Edges'], viewer_text.inputs[0])

        # Trigger processing of Cylinder node
        cyl.process()
        viewer_text.inputs[0].sv_set(cyl.outputs['Edges'].sv_get())
        # Invoke "VIEW" operator
        bpy.ops.node.sverchok_viewer_buttonmk1('EXEC_DEFAULT', treename=self.tree.name, nodename=viewer_text.name)

        # Read what the operator has written to the text buffer.
        text = bpy.data.texts['Sverchok_viewer'].as_string()
        # Test that text in buffer equals exactly to the text saved
        # in the file from the first test run.
        with open(self.get_reference_file_path("text_viewer_out.txt"), "r") as f:
            expected_text = f.read()
            self.assertEqual(text, expected_text)
