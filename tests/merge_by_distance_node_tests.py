# SPDX-License-Identifier: GPL-3.0-or-later
"""Real Blender node regressions for Merge by Distance.

Discovered by Sverchok's ``run_tests.sh`` (tests/*_tests.py). These checks
exercise socket order, Blender data transfer and the process() call that a
standalone geometric-kernel test cannot cover.
"""
import bpy
import numpy as np

from sverchok.core.socket_data import sv_set_socket
from sverchok.utils.testing import SverchokTestCase


INPUT_ORDER = ('Vertices', 'Edges', 'Polygons', 'Verts Mask', 'Distance',
               'VertData', 'EdgeData', 'FaceData')
OUTPUT_ORDER = ('Vertices', 'Edges', 'Polygons', 'Doubles', 'Mask',
                'VertData', 'EdgeData', 'FaceData',
                'Vert Init Index', 'Edge Init Index', 'Face Init Index')


class MergeByDistanceNodeTests(SverchokTestCase):
    def setUp(self):
        super().setUp()
        self.tree = bpy.data.node_groups.new('SverchokMergeByDistanceCI', 'SverchCustomTreeType')
        self.tree.sv_process = False

    def tearDown(self):
        bpy.data.node_groups.remove(self.tree)
        super().tearDown()

    def node(self):
        node = self.tree.nodes.new('SvMergeByDistanceNumpyNode')
        node.neighbor_backend = 'GRID_PY'
        return node

    def run_node(self, inputs, output_names):
        node = self.node()
        if set(output_names) & set(OUTPUT_ORDER[5:]) or set(inputs) & set(INPUT_ORDER[5:]):
            node.mesh_data = True
        for name, value in inputs.items():
            reroute = self.tree.nodes.new('NodeReroute')
            self.tree.links.new(reroute.outputs[0], node.inputs[name])
            sv_set_socket(node.inputs[name], value)
        for name in output_names:
            reroute = self.tree.nodes.new('NodeReroute')
            self.tree.links.new(node.outputs[name], reroute.inputs[0])
        node.process()
        return {name: node.outputs[name].sv_get(deepcopy=False) for name in output_names}

    def test_compact_socket_order_and_toggle(self):
        node = self.node()
        self.assertEqual([s.name for s in node.inputs], list(INPUT_ORDER))
        self.assertEqual([s.name for s in node.outputs], list(OUTPUT_ORDER))
        self.assertFalse(node.mesh_data)
        self.assertTrue(all(not node.inputs[name].hide for name in INPUT_ORDER[:5]))
        self.assertTrue(all(node.inputs[name].hide for name in INPUT_ORDER[5:]))
        self.assertTrue(all(not node.outputs[name].hide for name in OUTPUT_ORDER[:5]))
        self.assertTrue(all(node.outputs[name].hide for name in OUTPUT_ORDER[5:]))
        node.mesh_data = True
        self.assertTrue(all(not node.outputs[name].hide for name in OUTPUT_ORDER[5:]))
        node.mesh_data = False
        self.assertTrue(all(node.outputs[name].hide for name in OUTPUT_ORDER[5:]))

    def test_compact_process_preserves_mesh_and_order(self):
        vertices = np.array([[0,0,0], [0,0,0], [1,0,0], [0,1,0]], dtype=np.float32)
        data = self.run_node(
            {'Vertices': [vertices], 'Polygons': [[[0,2,3],[1,2,3]]],
             'Distance': [[.001]]}, OUTPUT_ORDER[:5])
        self.assertEqual(len(data['Vertices'][0]), 3)
        self.assertEqual(len(data['Polygons'][0]), 1)
        self.assertEqual(len(data['Doubles'][0]), 1)
        self.assertEqual(len(data['Edges'][0]), 3)

    def test_provenance_metadata_and_numpy_output(self):
        vertices = np.array([[0,0,0], [0,0,0], [1,0,0], [1,0,0],
                             [1,1,0], [1,1,0], [0,1,0]], dtype=np.float32)
        result = self.run_node(
            {'Vertices':[vertices],
             'Polygons':[[[0,2,4,6],[1,3,5,6]]],
             'Edges':[[[0,2],[1,3],[2,4]]],
             'VertData':[['v0','v1','v2','v3','v4','v5','v6']],
             'EdgeData':[['e0','e1','e2']],
             'FaceData':[['first','duplicate']]}, OUTPUT_ORDER)
        self.assertEqual(result['Vert Init Index'][0], [[0,1],[2,3],[4,5],[6]])
        self.assertEqual(result['Face Init Index'][0], [[0,1]])
        self.assertEqual(result['Edge Init Index'][0][0], [0,1])
        self.assertEqual(result['VertData'][0], ['v0','v2','v4','v6'])
        self.assertEqual(result['EdgeData'][0][0], 'e0')
        self.assertEqual(result['FaceData'][0], ['first'])
        self.assertEqual(len(result['Edges'][0]), len(result['Edge Init Index'][0]))

    def test_mesh_data_toggle_keeps_existing_links(self):
        node = self.node()
        node.mesh_data = True
        output = node.outputs['FaceData']
        reroute = self.tree.nodes.new('NodeReroute')
        self.tree.links.new(output, reroute.inputs[0])
        node.mesh_data = False
        self.assertTrue(output.is_linked)
        self.assertFalse(output.hide)
        self.assertTrue(node.outputs['EdgeData'].hide)


if __name__ == '__main__':
    import unittest
    unittest.main()
