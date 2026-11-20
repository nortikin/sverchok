# SPDX-License-Identifier: GPL-3.0-or-later
"""Output NumPy compatibility and area regression tests (no Blender needed).

    python3 tests/test_mesh_numpy_outputs.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'utils' / 'mesh'
NODES = ROOT / 'nodes' / 'modifier_make'
sys.path.insert(0, str(CORE))
from mesh_cut_parts import _surface_area, _surface_area_slow
from mesh_intersections import intersect_meshes
from mesh_cut_parts import cut_mesh_parts


class Socket:
    def __init__(self, name):
        self.name, self.is_linked, self.hide_safe = name, True, False
        self.data, self.value = None, None
    def sv_set(self, data):
        self.data = data
    def sv_get(self, default=None):
        return self.value if self.value is not None else default


class Sockets(list):
    def new(self, _kind, name):
        s = Socket(name)
        self.append(s)
        return s
    def __getitem__(self, key):
        if isinstance(key, str):
            return next(s for s in self if s.name == key)
        return super().__getitem__(key)
    def __contains__(self, name):
        return any(s.name == name for s in self)


def load_node(path):
    # Import Blender-facing module using stubs, without importing Blender.
    bpy = types.ModuleType('bpy')
    props = types.ModuleType('bpy.props')
    for name in ('BoolProperty', 'BoolVectorProperty', 'EnumProperty',
                 'FloatProperty', 'IntProperty'):
        setattr(props, name, lambda **kwargs: kwargs)
    bpy.props = props
    bpy.types = types.SimpleNamespace(Node=type('Node', (), {}))
    bpy.utils = types.SimpleNamespace(register_class=lambda _: None,
                                      unregister_class=lambda _: None)
    modules = {
        'bpy': bpy, 'bpy.props': props,
        'sverchok': types.ModuleType('sverchok'),
        'sverchok.node_tree': types.ModuleType('sverchok.node_tree'),
        'sverchok.data_structure': types.ModuleType('sverchok.data_structure'),
        'sverchok.utils': types.ModuleType('sverchok.utils'),
        'sverchok.utils.mesh': types.ModuleType('sverchok.utils.mesh'),
        'sverchok.utils.mesh.mesh_intersections': sys.modules['mesh_intersections'],
        'sverchok.utils.mesh.mesh_cut': sys.modules['mesh_cut'],
        'sverchok.utils.mesh.mesh_cut_parts': sys.modules['mesh_cut_parts'],
    }
    modules['sverchok.node_tree'].SverchCustomTreeNode = type('SverchCustomTreeNode', (), {})
    modules['sverchok.data_structure'].updateNode = lambda *a: None
    modules['sverchok.data_structure'].zip_long_repeat = lambda *args: zip(*args)
    saved = {key: sys.modules.get(key) for key in modules}
    try:
        sys.modules.update(modules)
        spec = importlib.util.spec_from_file_location('test_node_'+path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value


CUBE_V = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],
          [-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]]
CUBE_F = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],
          [2,3,7,6],[3,0,4,7]]
PLANE_V = [[-2,-2,0],[2,-2,0],[2,2,0],[-2,2,0]]
PLANE_F = [[0,1,2,3]]


class OutputModeTests(unittest.TestCase):
    def make_node(self, file, cls):
        mod = load_node(NODES/file)
        node = getattr(mod, cls)()
        node.inputs = Sockets()
        node.outputs = Sockets()
        node.advanced_outputs = False
        node.out_np = (False, False)
        node.acceleration = 'AUTO'
        node.tolerance = 1e-6
        node.include_coplanar = True
        if cls == 'SvCutByMeshNpNode':
            node.mode = 'CUT'
            node.keep = 'ALL'
            node.piece_index = 0
            node.preserve_polygons = True
        node.sv_init(None)
        for name, obj in [('Vertices A', CUBE_V), ('Faces A', CUBE_F),
                          ('Vertices Cutter', PLANE_V), ('Faces Cutter', PLANE_F)]:
            node.inputs[name].value = [obj]
        return node

    def check_formats(self, node):
        for flags in ((False,False),(True,False),(False,True),(True,True)):
            node.out_np = flags
            node.process()
            vertices = node.outputs['Vertices'].data[0]
            edges = node.outputs['Edges'].data[0]
            self.assertIsInstance(vertices, np.ndarray if flags[0] else list)
            self.assertIsInstance(edges, np.ndarray if flags[1] else list)
            self.assertEqual(np.asarray(vertices).shape[1],3)
            self.assertEqual(np.asarray(edges).shape[1],2)
            # Numeric content remains the same regardless of output setting.
            if flags == (False,False):
                self.reference = (np.asarray(vertices),np.asarray(edges))
            else:
                np.testing.assert_array_equal(np.asarray(vertices),self.reference[0])
                np.testing.assert_array_equal(np.asarray(edges),self.reference[1])

    def test_mesh_intersection_output_numpy(self):
        node = self.make_node('mesh_intersection.py','SvMeshIntersectionNpNode')
        self.check_formats(node)

    def test_cut_by_mesh_output_numpy(self):
        node = self.make_node('cut_by_mesh.py','SvCutByMeshNpNode')
        self.check_formats(node)

    def test_cut_by_mesh_separate_numpy_per_piece(self):
        node = self.make_node('cut_by_mesh.py','SvCutByMeshNpNode')
        node.mode = 'SEPARATE'
        node.out_np = (True,True)
        node.process()
        vs = node.outputs['Vertices'].data
        es = node.outputs['Edges'].data
        self.assertEqual(len(vs), 2)
        self.assertEqual(len(es), 2)
        self.assertTrue(all(isinstance(x, np.ndarray) for x in vs+es))
        self.assertTrue(all(len(x)>0 for x in vs))

    def test_unlinked_outputs_not_computed(self):
        node = self.make_node('mesh_intersection.py','SvMeshIntersectionNpNode')
        node.outputs['Edges'].is_linked = False
        node.out_np = (True,False)
        node.process()
        self.assertIsInstance(node.outputs['Vertices'].data[0],np.ndarray)
        self.assertIsNone(node.outputs['Edges'].data)

    def test_vector_area_matches_reference(self):
        for faces, vertices in [
            ([[0,1,2]],[[0,0,0],[2,0,0],[0,1,0]]),
            ([[0,1,2,3]],[[0,0,0],[2,0,0],[2,2,0],[0,2,0]]),
            ([[0,1,2,3,4]],[[0,0,0],[3,0,0],[3,2,0],[1,0.5,0],[0,2,0]]),
        ]:
            v=np.asarray(vertices,dtype=np.float64)
            self.assertAlmostEqual(_surface_area(v,faces),_surface_area_slow(v,faces),places=12)


if __name__ == '__main__':
    unittest.main()
