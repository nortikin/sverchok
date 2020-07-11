# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

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

class SurfaceCurvatureCalculator(object):
    """
    This class contains pre-calculated first and second surface derivatives,
    and calculates any curvature information from them.
    """
    def __init__(self, us, vs, order=True):
        self.us = us
        self.vs = vs
        self.order = order
        self.fu = self.fv = None
        self.duu = self.dvv = self.duv = None
        self.nuu = self.nvv = self.nuv = None
        self.points = None
        self.normals = None

    def set(self, points, normals, fu, fv, duu, dvv, duv, nuu, nvv, nuv):
        """Set derivatives information"""
        self.points = points
        self.normals = normals
        self.fu = fu   # df/du
        self.fv = fv   # df/dv
        self.duu = duu # (fu, fv), a.k.a. E
        self.dvv = dvv # (fv, fv), a.k.a. G
        self.duv = duv # (fu, fv), a.k.a F
        self.nuu = nuu # (fuu, normal), a.k.a l
        self.nvv = nvv # (fvv, normal), a.k.a n
        self.nuv = nuv # (fuv, normal), a.k.a m

    def mean(self):
        """Calculate mean curvature"""
        duu, dvv, duv, nuu, nvv, nuv = self.duu, self.dvv, self.duv, self.nuu, self.nvv, self.nuv
        A = duu*dvv - duv*duv
        B = duu*nvv - 2*duv*nuv + dvv*nuu
        return -B / (2*A)

    def gauss(self):
        """Calculate Gaussian curvature"""
        duu, dvv, duv, nuu, nvv, nuv = self.duu, self.dvv, self.duv, self.nuu, self.nvv, self.nuv
        numerator = nuu * nvv - nuv*nuv
        denominator = duu * dvv - duv*duv
        return numerator / denominator

    def values(self):
        """
        Calculate two principal curvature values.
        If "order" parameter is set to True, then it will be guaranteed,
        that C1 value is always less than C2.
        """
        # It is possible to calculate principal curvature values
        # as solutions of quadratic equation, without calculating
        # corresponding principal curvature directions.

        # lambda^2 (E G - F^2) - lambda (E N - 2 F M + G L) + (L N - M^2) = 0

        duu, dvv, duv, nuu, nvv, nuv = self.duu, self.dvv, self.duv, self.nuu, self.nvv, self.nuv
        A = duu*dvv - duv*duv
        B = duu*nvv - 2*duv*nuv + dvv*nuu
        C = nuu*nvv - nuv*nuv
        D = B*B - 4*A*C
        c1 = (-B - np.sqrt(D))/(2*A)
        c2 = (-B + np.sqrt(D))/(2*A)

        c1[np.isnan(c1)] = 0
        c2[np.isnan(c2)] = 0

        c1mask = (c1 < c2)
        c2mask = np.logical_not(c1mask)

        c1_r = np.where(c1mask, c1, c2)
        c2_r = np.where(c2mask, c1, c2)

        return c1_r, c2_r

    def values_and_directions(self):
        """
        Calculate principal curvature values together with principal curvature directions.
        If "order" parameter is set to True, then it will be guaranteed, that C1 value
        is always less than C2. Curvature directions are always output correspondingly,
        i.e. principal_direction_1 corresponds to principal_value_1 and principal_direction_2
        corresponds to principal_value_2.
        """
        # If we need not only curvature values, but principal curvature directions as well,
        # we have to solve an eigenvalue problem to find values and directions at once.

        # L p = lambda G p

        fu, fv = self.fu, self.fv
        duu, dvv, duv, nuu, nvv, nuv = self.duu, self.dvv, self.duv, self.nuu, self.nvv, self.nuv
        n = len(self.us)

        L = np.empty((n,2,2))
        L[:,0,0] = nuu
        L[:,0,1] = nuv
        L[:,1,0] = nuv
        L[:,1,1] = nvv

        G = np.empty((n,2,2))
        G[:,0,0] = duu
        G[:,0,1] = duv
        G[:,1,0] = duv
        G[:,1,1] = dvv

        M = np.matmul(np.linalg.inv(G), L)
        eigvals, eigvecs = np.linalg.eig(M)
        # Values of first and second principal curvatures
        c1 = eigvals[:,0]
        c2 = eigvals[:,1]

        if self.order:
            c1mask = (c1 < c2)
            c2mask = np.logical_not(c1mask)
            c1_r = np.where(c1mask, c1, c2)
            c2_r = np.where(c2mask, c1, c2)
        else:
            c1_r = c1
            c2_r = c2

        # dir_1 corresponds to c1, dir_2 corresponds to c2
        dir_1_x = eigvecs[:,0,0][np.newaxis].T
        dir_2_x = eigvecs[:,0,1][np.newaxis].T
        dir_1_y = eigvecs[:,1,0][np.newaxis].T
        dir_2_y = eigvecs[:,1,1][np.newaxis].T

        # another possible approach
#         A = duv * nvv - dvv*nuv 
#         B = duu * nvv - dvv*nuu
#         C = duu*nuv - duv*nuu
#         D = B*B - 4*A*C
#         t1 = (-B - np.sqrt(D)) / (2*A)
#         t2 = (-B + np.sqrt(D)) / (2*A)

        dir_1 = dir_1_x * fu + dir_1_y * fv
        dir_2 = dir_2_x * fu + dir_2_y * fv

        dir_1 = dir_1 / np.linalg.norm(dir_1, axis=1, keepdims=True)
        dir_2 = dir_2 / np.linalg.norm(dir_2, axis=1, keepdims=True)

        if self.order:
            c1maskT = c1mask[np.newaxis].T
            c2maskT = c2mask[np.newaxis].T
            dir_1_r = np.where(c1maskT, dir_1, -dir_2)
            dir_2_r = np.where(c2maskT, dir_1, dir_2)
        else:
            dir_1_r = dir_1
            dir_2_r = dir_2
        #r = (np.cross(dir_1_r, dir_2_r) * self.normals).sum(axis=1)
        #print(r)

        dir1_uv = eigvecs[:,:,0]
        dir2_uv = eigvecs[:,:,1]
        if self.order:
            c1maskT = c1mask[np.newaxis].T
            c2maskT = c2mask[np.newaxis].T
            dir1_uv_r = np.where(c1maskT, dir1_uv, -dir2_uv)
            dir2_uv_r = np.where(c2maskT, dir1_uv, dir2_uv)
        else:
            dir1_uv_r = dir1_uv
            dir2_uv_r = dir2_uv
            
        return c1_r, c2_r, dir1_uv_r, dir2_uv_r, dir_1_r, dir_2_r

    def calc(self, need_values=True, need_directions=True, need_uv_directions = False, need_gauss=True, need_mean=True, need_matrix = True):
        """
        Calculate curvature information.
        Return value: SurfaceCurvatureData instance.
        """
        # We try to do as less calculations as possible,
        # by not doing complex computations if not required
        # and reusing results of other computations if possible.
        data = SurfaceCurvatureData()
        if need_matrix:
            need_directions = True
        if need_uv_directions:
            need_directions = True
        if need_directions:
            # If we need principal curvature directions, then the method
            # being used will calculate us curvature values for free.
            c1, c2, dir1_uv, dir2_uv, dir1, dir2 = self.values_and_directions()
            data.principal_value_1, data.principal_value_2 = c1, c2
            data.principal_direction_1, data.principal_direction_2 = dir1, dir2
            data.principal_direction_1_uv = dir1_uv
            data.principal_direction_2_uv = dir2_uv
            if need_gauss:
                data.gauss = c1 * c2
            if need_mean:
                data.mean = (c1 + c2)/2.0
        if need_matrix:
            matrices_np = np.dstack((data.principal_direction_2, data.principal_direction_1, self.normals))
            matrices_np = np.transpose(matrices_np, axes=(0,2,1))
            matrices_np = np.linalg.inv(matrices_np)
            matrices = [Matrix(m.tolist()).to_4x4() for m in matrices_np]
            for matrix, point in zip(matrices, self.points):
                matrix.translation = Vector(point)
            data.matrix = matrices
        if need_values and not need_directions:
            c1, c2 = self.values()
            data.principal_value_1, data.principal_value_2 = c1, c2
            if need_gauss:
                data.gauss = c1 * c2
            if need_mean:
                data.mean = (c1 + c2)/2.0
        if need_gauss and not need_directions and not need_values:
            data.gauss = self.gauss()
        if need_mean and not need_directions and not need_values:
            data.mean = self.mean()
        return data

