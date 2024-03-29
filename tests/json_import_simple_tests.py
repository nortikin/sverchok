
from sverchok.utils.testing import *


class ImportSingleSimpleNode(EmptyTreeTestCase):

    def test_box_import(self):
        node = create_node("SvBoxNodeMk2", self.tree.name)
        node.Divx = 1
        node.Divy = 3
        node.Divz = 4
        node.Size = 1.0299999713897705

        self.assert_node_equals_file(node, "Box", "box.json")

    def test_cylinder_import(self):
        node = create_node("SvCylinderNodeMK2", self.tree.name)
        node.separate = False
        node.cap_bottom = 1
        node.cap_top = 1
        node.center = 0
        node.angle_units = 'RAD'
        node.radius_t = 1.0299999713897705
        node.radius_b = 1.0299999713897705
        node.parallels = 2
        node.meridians = 33
        node.height = 2.0299999713897705
        node.twist = 1.0299999713897705
        node.phase = 1.0299999713897705
        node.scale = 1.0299999713897705

        self.assert_node_equals_file(node, "Cylinder", "cylinder.json")

    def test_torus_import(self):
        node = create_node("SvTorusNodeMK2", self.tree.name)
        node.mode = "MAJOR_MINOR"
        node.Separate = 0
        node.torus_eR = 1.2799999713897705
        node.torus_R = 1.0299999713897705
        node.torus_r = 0.25
        node.torus_iR = 0.7799999713897705
        node.torus_n1 = 33
        node.torus_n2 = 17
        node.torus_rP = 0.029999999329447746
        node.torus_sP = 0.029999999329447746
        node.torus_sT = 1

        self.assert_node_equals_file(node, "Torus", "torus.json")
