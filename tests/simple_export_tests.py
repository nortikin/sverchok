
import unittest
import json

from sverchok.utils.testing import *
from sverchok.utils.sv_IO_panel_tools import create_dict_of_tree

class ExportSingleSimpleNode(SverchokTestCase):

    def test_box_export(self):
        node = create_node("SvBoxNode", self.tree.name)
        node.Divx = 1
        node.Divy = 3
        node.Divz = 4
        node.Size = 1.0299999713897705

        export_result = create_dict_of_tree(self.tree)

        expected_result = json.loads("""
        {"groups": {}, "update_lists": [], "framed_nodes": {}, "nodes": {"Box":
        {"height": 100.0, "use_custom_color": true, "color": [0.0, 0.5, 0.5],
        "location": [0.0, 0.0], "hide": false, "params": {"Divz": 4, "Divx": 1,
        "Divy": 3, "Size": 1.0299999713897705}, "bl_idname": "SvBoxNode",
        "label": "", "width": 140.0}}, "export_version": "0.07"}
        """)

        self.assert_json_equals(export_result, expected_result)

    def test_cylinder_export(self):
        node = create_node("CylinderNode", self.tree.name)
        node.Separate = 1
        node.cap_ = 0
        node.radTop_ = 1.0299999713897705
        node.radBot_ = 1.0299999713897705
        node.vert_ = 33
        node.height_ = 2.0299999713897705
        node.subd_ = 1

        export_result = create_dict_of_tree(self.tree)

        expected_result = json.loads("""
        {"export_version": "0.07", "update_lists": [], "groups": {},
        "framed_nodes": {}, "nodes": {"Cylinder": {"use_custom_color": true,
        "color": [0.0, 0.5, 0.5], "location": [0.0, 0.0], "params": {"height_":
            2.0299999713897705, "Separate": 1, "radTop_": 1.0299999713897705,
            "cap_": 0, "subd_": 1, "radBot_": 1.0299999713897705, "vert_": 33},
        "bl_idname": "CylinderNode", "label": "", "height": 100.0, "width":
        140.0, "hide": false}}}
        """)

        self.assert_json_equals(export_result, expected_result)

    def test_torus_export(self):
        node = create_node("SvTorusNode", self.tree.name)
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

        export_result = create_dict_of_tree(self.tree)

        expected_result = json.loads("""
        {"framed_nodes": {}, "update_lists": [], "groups": {}, "nodes":
        {"Torus": {"height": 100.0, "width": 140.0, "hide": false, "location":
        [0.0, 0.0], "color": [0.0, 0.5, 0.5], "params": {"torus_r": 0.25,
        "torus_sP": 0.029999999329447746, "torus_eR": 1.2799999713897705,
        "torus_R": 1.0299999713897705, "torus_iR": 0.7799999713897705,
        "torus_n1": 33, "torus_n2": 17, "torus_sT": 1, "mode": "MAJOR_MINOR",
        "Separate": 0, "torus_rP": 0.029999999329447746}, "label": "",
        "use_custom_color": true, "bl_idname": "SvTorusNode"}},
        "export_version": "0.07"}
        """)

        self.assert_json_equals(export_result, expected_result)

