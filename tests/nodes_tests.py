from typing import List
from itertools import product

import numpy as np

from mathutils import Matrix

from sverchok.utils.testing import SverchokTestCase

import sverchok.nodes.matrix.apply_and_join as apply_mat
from sverchok.utils.vectorize import SvVerts, SvEdges, SvPolys


class NodeCommonTest(SverchokTestCase):
    def setUp(self):
        self.node_funcs = [apply_mat.apply_matrices, apply_mat.apply_matrix, apply_mat.join_meshes]

        self.vertices = [[-1.0, -0.5, 0.0], [0.0, -0.5, 0.0], [1.0, -0.5, 0.0], [-1.0, 0.5, 0.0], [0.0, 0.5, 0.0], [1.0, 0.5, 0.0]]
        self.vertices_np = np.array(self.vertices, dtype=np.float32)
        self.edges = [[0, 3], [1, 4], [2, 5], [0, 1], [1, 2], [3, 4], [4, 5]]
        self.polys = [[1, 4, 3, 0], [2, 5, 4, 1]]
        self.matrix = Matrix.Translation((1.0, 0., 0.))

        self.args_data = {
            SvVerts: self.vertices_np,
            SvEdges: self.edges,
            SvPolys: self.polys,
            List[SvVerts]: [self.vertices_np, self.vertices_np],
            List[SvEdges]: [self.edges, self.edges],
            List[SvPolys]: [self.polys, self.edges],
            Matrix: self.matrix,
            List[Matrix]: [self.matrix, self.matrix]
        }

    def function_parameters_generator(self, func) -> dict:
        kwargs = {key: self.args_data[an] for key, an in func.__annotations__.items() if an in self.args_data}
        for mask in product([False, True], repeat=len(kwargs)):
            yield {key: data if m else None for (key, data), m in zip(kwargs.items(), mask)}

    def test_empty_data(self):
        """Assume that all node functions should be able to handle cases when one or more of input parameters are None
        it's quite fair since user may not add connections to a node"""
        for func in self.node_funcs:
            for kwargs in self.function_parameters_generator(func):
                with self.subTest(msg=f"Function: {func.__name__}; Module: {func.__module__}, Arguments: {kwargs}"):
                    func(**kwargs)

    # todo add passing vertices edges and polygons parameters


class ApplyMatrixNodeTest(SverchokTestCase):
    def setUp(self):
        self.vertices = [[-1.0, -0.5, 0.0], [0.0, -0.5, 0.0], [1.0, -0.5, 0.0], [-1.0, 0.5, 0.0], [0.0, 0.5, 0.0], [1.0, 0.5, 0.0]]
        self.polygons = [[1, 4, 3, 0], [2, 5, 4, 1]]
        self.matrices = [Matrix.Translation((0, 0, 0)), Matrix.Translation((1, 0, 0))]

    def test_apply_matrices(self):
        res_vertices = [(-1.0, -0.5, 0.0), (0.0, -0.5, 0.0), (1.0, -0.5, 0.0), (-1.0, 0.5, 0.0), (0.0, 0.5, 0.0), (1.0, 0.5, 0.0), (0.0, -0.5, 0.0), (1.0, -0.5, 0.0), (2.0, -0.5, 0.0), (0.0, 0.5, 0.0), (1.0, 0.5, 0.0), (2.0, 0.5, 0.0)]
        res_polygons = [[1, 4, 3, 0], [2, 5, 4, 1], [7, 10, 9, 6], [8, 11, 10, 7]]
        vertices, edges, polygons = apply_mat.apply_matrices(vertices=self.vertices, edges=None, polygons=self.polygons, matrices=self.matrices)
        self.assert_sverchok_data_equal(vertices, res_vertices, 5)
        self.assert_sverchok_data_equal(polygons, res_polygons)

    # todo other functions?


if __name__ == '__main__':
    import unittest
    unittest.main(exit=False)
