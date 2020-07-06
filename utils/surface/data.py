# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi, cos, sin
from collections import defaultdict

from mathutils import Matrix, Vector

class SurfaceCurvatureData(object):
    """Container class for calculated curvature values"""
    def __init__(self):
        self.principal_value_1 = self.principal_value_2 = None
        self.principal_direction_1 = self.principal_direction_2 = None
        self.principal_direction_1_uv = self.principal_direction_2_uv = None
        self.mean = self.gauss = None
        self.matrix = None

class SurfaceDerivativesData(object):
    def __init__(self, points, du, dv):
        self.points = points
        self.du = du
        self.dv = dv
        self._normals = None
        self._normals_len = None
        self._unit_normals = None
        self._unit_du = None
        self._unit_dv = None
        self._du_len = self._dv_len = None

    def normals(self):
        if self._normals is None:
            self._normals = np.cross(self.du, self.dv)
        return self._normals

    def normals_len(self):
        if self._normals_len is None:
            normals = self.normals()
            self._normals_len = np.linalg.norm(normals, axis=1)[np.newaxis].T
        return self._normals_len

    def unit_normals(self):
        if self._unit_normals is None:
            normals = self.normals()
            norm = self.normals_len()
            self._unit_normals = normals / norm
        return self._unit_normals

    def tangent_lens(self, keepdims=True):
        if self._du_len is None:
            self._du_len = np.linalg.norm(self.du, axis=1, keepdims=True)
            self._dv_len = np.linalg.norm(self.dv, axis=1, keepdims=True)
        return self._du_len, self._dv_len

    def unit_tangents(self):
        if self._unit_du is None:
            du_norm, dv_norm = self.tangent_lens()
            self._unit_du = self.du / du_norm
            self._unit_dv = self.dv / dv_norm
        return self._unit_du, self._unit_dv

    def matrices(self, as_mathutils = False):
        normals = self.unit_normals()
        du, dv = self.unit_tangents()
        matrices_np = np.dstack((du, dv, normals))
        matrices_np = np.transpose(matrices_np, axes=(0,2,1))
        matrices_np = np.linalg.inv(matrices_np)
        if as_mathutils:
            matrices = [Matrix(m.tolist()).to_4x4() for m in matrices_np]
            for m, p in zip(matrices, self.points):
                m.translation = Vector(p)
            return matrices
        else:
            return matrices_np

