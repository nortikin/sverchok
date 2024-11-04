# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

from mathutils import kdtree
from mathutils import Vector, Matrix, Quaternion

from sverchok.utils.math import np_multiply_matrices_vectors
from sverchok.utils.geom import PlaneEquation
from sverchok.utils.manifolds import intersect_curve_plane, EQUATION, NURBS
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.field.vector import SvVectorField
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial.transform import Rotation, Slerp

class IntersectionParams:
    def __init__(self, init_samples=10, tolerance=1e-3, max_iterations=50):
        self.init_samples = init_samples
        self.tolerance = tolerance
        self.max_iterations = max_iterations

DEFAULT_INTERSECTION_PARAMS = IntersectionParams(init_samples=10, tolerance=1e-3, max_iterations=50)

class SvFrameAlongCurveField(SvVectorField):
    def __init__(self, curve, matrices, z_axis='Z',
                 intersection_params = DEFAULT_INTERSECTION_PARAMS):
        nurbs_curve = SvNurbsCurve.to_nurbs(curve)
        if nurbs_curve is None:
            self.curve = curve
            self.is_nurbs = False
        else:
            self.curve = nurbs_curve
            self.is_nurbs = True
        self.matrices = matrices
        self.z_axis = z_axis
        self.intersection_params = intersection_params

        self._calc_quats()

    def _calc_quats(self):
        pairs = []
        for matrix in self.matrices:
            tk, quat = self._matrix_to_curve(matrix)
            quat = list(quat)
            pairs.append((tk, quat))

        pairs = list(sorted(pairs, key = lambda p: p[0]))
        self.quats = [p[1] for p in pairs]
        self.tknots = [p[0] for p in pairs]

        self.quats.insert(0, self.quats[0])
        self.quats.append(self.quats[-1])

        u_min, u_max = self.curve.get_u_bounds()
        self.tknots.insert(0, u_min)
        self.tknots.append(u_max)

        self.quats = Rotation.from_quat(self.quats)
        self.tknots = np.array(self.tknots)
        #self.t_min, self.t_max = min(self.tknots), max(self.tknots)
        #self.tknots = (self.tknots - self.t_min) / (self.t_max - self.t_min)
        self.slerp = Slerp(self.tknots, self.quats)

    def _matrix_to_curve(self, matrix):
        plane = PlaneEquation.from_matrix(matrix, normal_axis=self.z_axis)
        # Or take nearest point?
        solutions = intersect_curve_plane(self.curve, plane,
                        method = NURBS if self.is_nurbs else EQUATION,
                        init_samples=self.intersection_params.init_samples,
                        tolerance=self.intersection_params.tolerance,
                        maxiter=self.intersection_params.max_iterations)
        t, point = self._nearest_solution(matrix.translation, solutions)
        if t is None:
            raise Exception(f"Can't project the matrix {matrix} to the {self.curve}!")
        #matrix.translation = Vector(point)
        return t, matrix.to_quaternion()

    def _nearest_solution(self, point, solutions):
        if len(solutions) == 0:
            return None, None
        if len(solutions) <= 1:
            return solutions[0]
        kdt = kdtree.KDTree(len(solutions))
        for i, solution in enumerate(solutions):
            v = solution[1]
            kdt.insert(v, i)
        kdt.balance()
        _, i, _ = kdt.find(point)
        return solutions[i]

    def evaluate_grid(self, xs, ys, zs):
        n = len(xs)
        pts = np.zeros((n,3))
        pts[:,0] = xs
        pts[:,1] = ys
        pts[:,2] = zs
        z_axis = "XYZ".index(self.z_axis)
        ts = pts[:,z_axis]
        #print("T", ts)
        #matrices = self.slerp(ts).as_matrix()
        #matrices[:,:,:] = matrices[:,:,::-1]
        #matrices[:,:,:] = matrices[:,::-1,:]
        quats = self.slerp(ts).as_quat(scalar_first=False)
        matrices = [Quaternion(q).to_matrix() for q in quats]
        matrices = np.array(matrices)
        #print("M", self.slerp(ts).as_euler('xyz', degrees=True))
        #print("M", matrices)
        zero_pts = pts.copy()
        zero_pts[:,z_axis] = 0
        new_pts = np_multiply_matrices_vectors(matrices, zero_pts)
        #new_pts = self.slerp(ts).apply(zero_pts, True)
        #new_pts[:,z_axis] = 0
        origins = self.curve.evaluate_array(ts)
        new_pts += origins
        R = (new_pts - pts).T
        return R[0], R[1], R[2]

    def evaluate(self, x, y, z):
        rxs, rys, rzs = self.evaluate_grid([x], [y], [z])
        return rxs[0], rys[0], rzs[0]

