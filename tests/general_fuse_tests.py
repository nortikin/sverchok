
from sverchok.data_structure import get_data_nesting_level
from sverchok.utils.testing import *
from sverchok.utils.logging import debug, info
from sverchok.dependencies import FreeCAD

if FreeCAD is not None:
    from FreeCAD import Base
    import Part

@requires(FreeCAD)
class GeneralFuseTests(NodeProcessTestCase):
    node_bl_idname = "SvSolidGeneralFuseNode"
    connect_output_sockets = ["Solid"]

    def _make_box(self, x, y, z, size=1):
        up = Base.Vector(0,0,1)
        box = Part.makeBox(size,size,size, Base.Vector(x,y,z), up)
        return box

    def _make_box_node(self, x, y, z, size=1):
        node = create_node("SvBoxSolidNode")
        node.box_length = node.box_width = node.box_height = size
        node.origin = (x, y, z)
        return node

    def _make_list_join(self):
        node = create_node("ListJoinNode")
        return node

    def test_fuse_1(self):
        "Input level 1, Merge = On"
        box1 = self._make_box_node(0, 0, 0, size=2)
        box2 = self._make_box_node(1, 1, 1, size=2)
        join = self._make_list_join()

        self.tree.links.new(box1.outputs[0], join.inputs[0])
        self.tree.links.new(box2.outputs[0], join.inputs[1])

        self.tree.links.new(join.outputs[0], self.node.inputs["Solids"])

        self.node.process()

        out = self.get_output_data("Solid")
        out_level = get_data_nesting_level(out, data_types=(Part.Shape,))
        self.assertEquals(out_level, 1)
        out_len = len(out)
        self.assertEquals(out_len, 1)

        map = self.get_output_data("SolidSources")
        self.assert_sverchok_data_equal(map, [[0, 1]])

        mask = self.get_output_data("EdgesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)
        self.assertEqual(len(mask[0]), 30)

        map = self.get_output_data("EdgeSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)
        self.assertEqual(len(map[0]), 30)

        mask = self.get_output_data("FacesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)
        self.assertEqual(len(mask[0]), 12)

        map = self.get_output_data("FaceSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)
        self.assertEqual(len(map[0]), 12)

    def test_fuse_2(self):
        "Input level 1, Merge = Off"
        box1 = self._make_box_node(0, 0, 0, size=2)
        box2 = self._make_box_node(1, 1, 1, size=2)
        join = self._make_list_join()

        self.tree.links.new(box1.outputs[0], join.inputs[0])
        self.tree.links.new(box2.outputs[0], join.inputs[1])
        self.tree.links.new(join.outputs[0], self.node.inputs["Solids"])

        self.node.merge_result = False

        self.node.process()

        out = self.get_output_data("Solid")
        out_level = get_data_nesting_level(out, data_types=(Part.Shape,))
        self.assertEquals(out_level, 1)
        out_len = len(out)
        self.assertEquals(out_len, 3)

        map = self.get_output_data("SolidSources")
        self.assert_sverchok_data_equal(map, [[0], [0,1], [1]])

        mask = self.get_output_data("EdgesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)

        map = self.get_output_data("EdgeSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)

        mask = self.get_output_data("FacesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)

        map = self.get_output_data("FaceSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)

    def test_fuse_3(self):
        "Input level 2, Merge = On"
        box1 = self._make_box_node(0, 0, 0, size=2)
        box2 = self._make_box_node(1, 1, 1, size=2)
        join = self._make_list_join()
        join.JoinLevel = 2

        self.tree.links.new(box1.outputs[0], join.inputs[0])
        self.tree.links.new(box2.outputs[0], join.inputs[1])
        self.tree.links.new(join.outputs[0], self.node.inputs["Solids"])

        self.node.process()

        out = self.get_output_data("Solid")
        out_level = get_data_nesting_level(out, data_types=(Part.Shape,))
        self.assertEquals(out_level, 1)
        out_len = len(out)
        self.assertEquals(out_len, 1)

        map = self.get_output_data("SolidSources")
        self.assert_sverchok_data_equal(map, [[0,1]])

        mask = self.get_output_data("EdgesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)

        map = self.get_output_data("EdgeSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)

        mask = self.get_output_data("FacesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 2)

        map = self.get_output_data("FaceSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 3)

    def test_fuse_4(self):
        "Input level 2, Merge = Off"
        box1 = self._make_box_node(0, 0, 0, size=2)
        box2 = self._make_box_node(1, 1, 1, size=2)
        join = self._make_list_join()
        join.JoinLevel = 2

        self.tree.links.new(box1.outputs[0], join.inputs[0])
        self.tree.links.new(box2.outputs[0], join.inputs[1])
        self.tree.links.new(join.outputs[0], self.node.inputs["Solids"])

        self.node.merge_result = False

        self.node.process()

        out = self.get_output_data("Solid")
        out_level = get_data_nesting_level(out, data_types=(Part.Shape,))
        self.assertEquals(out_level, 2)
        #out_len = len(out)
        #self.assertEquals(out_len, 1)

        map = self.get_output_data("SolidSources")
        self.assert_sverchok_data_equal(map, [[[0], [0,1], [1]]])

        mask = self.get_output_data("EdgesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 3)

        map = self.get_output_data("EdgeSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 4)

        mask = self.get_output_data("FacesMask")
        mask_level = get_data_nesting_level(mask)
        self.assertEqual(mask_level, 3)

        map = self.get_output_data("FaceSources")
        map_level = get_data_nesting_level(map)
        self.assertEqual(map_level, 4)

