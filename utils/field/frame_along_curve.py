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
from sverchok.utils.curve.algorithms import SvCurveLengthSolver
from sverchok.utils.field.vector import SvVectorField
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.spatial.transform import Rotation, Slerp, RotationSpline

class IntersectionParams:
    def __init__(self, init_samples=10, tolerance=1e-3, max_iterations=50):
        self.init_samples = init_samples
        self.tolerance = tolerance
        self.max_iterations = max_iterations

DEFAULT_INTERSECTION_PARAMS = IntersectionParams(init_samples=10, tolerance=1e-3, max_iterations=50)

class SvFrameAlongCurveField(SvVectorField):
    INTERP_LINEAR = 'LIN'
    INTERP_SPLINE = 'SPL'

    CURVE_PARAMETER = 'T'
    CURVE_LENGTH = 'L'

    def __init__(self, curve, tknots, quats, z_axis='Z',
                 parametrization = CURVE_PARAMETER,
                 length_resolution = 50,
                 interpolation = INTERP_SPLINE):
        self.curve = curve
        self.tknots = tknots
        self.quats = quats
        self.z_axis = z_axis
        self.interpolation = interpolation
        self.parametrization = parametrization
        self.length_resolution = length_resolution

        self._init_slerp()

    @staticmethod
    def from_matrices(curve, matrices,
                      z_axis = 'Z',
                      interpolation = INTERP_SPLINE,
                      parametrization = CURVE_PARAMETER,
                      length_resolution = 50,
                      intersection_params = DEFAULT_INTERSECTION_PARAMS):
        quats, tknots = SvFrameAlongCurveField._quats_from_matrices(curve, matrices,
                                                           z_axis=z_axis,
                                                           intersection_params=intersection_params)
        field = SvFrameAlongCurveField(curve, tknots, quats,
                                       z_axis = z_axis,
                                       parametrization = parametrization,
                                       length_resolution = length_resolution,
                                       interpolation = interpolation)
        return field

    @staticmethod
    def from_quaternions(curve, t_values, quats,
                         z_axis = 'Z',
                         interpolation = INTERP_SPLINE,
                         parametrization = CURVE_PARAMETER,
                         length_resolution = 50):
        tknots = SvFrameAlongCurveField._calc_tknots(t_values, curve, length_resolution)
        return SvFrameAlongCurveField(curve, tknots, quats,
                                      z_axis = z_axis,
                                      parametrization = parametrization,
                                      length_resolution = length_resolution,
                                      interpolation = interpolation)

    @staticmethod
    def from_track_vectors(curve, t_values, track_vectors,
                        z_axis = 'Z', track_axis = 'X',
                        interpolation = INTERP_SPLINE,
                        parametrization = CURVE_PARAMETER,
                        length_resolution = 50):
        tknots = SvFrameAlongCurveField._calc_tknots(t_values, curve, parametrization, length_resolution)
        quats = SvFrameAlongCurveField._quats_from_track(curve, tknots, track_vectors,
                                                         z_axis = z_axis,
                                                         track_axis = track_axis)
        return SvFrameAlongCurveField(curve, tknots, quats,
                                      z_axis = z_axis,
                                      parametrization = parametrization,
                                      length_resolution = length_resolution,
                                      interpolation = interpolation)

    @staticmethod
    def _calc_tknots(t_values, curve, parametrization = CURVE_PARAMETER, length_resolution = 50):
        if parametrization == SvFrameAlongCurveField.CURVE_PARAMETER:
            tknots = t_values
        else:
            solver = SvCurveLengthSolver(curve)
            solver.prepare('SPL', length_resolution)
            tknots = solver.solve(np.array(t_values)).tolist()
        return tknots

    @staticmethod
    def _quats_from_track(curve, tknots, track_vectors,
                          z_axis = 'Z', track_axis = 'X'):
        if z_axis == track_axis:
            raise Exception("Orientation axis must differ from track axis!")
        z_axis = "XYZ".index(z_axis)
        track_axis = "XYZ".index(track_axis)
        y_axis = 3 - (z_axis + track_axis)
        tknots = np.array(tknots)
        z_vectors = curve.tangent_array(tknots)
        z_vectors /= np.linalg.norm(z_vectors, axis=1, keepdims=True)
        track_vectors = np.array(track_vectors)
        track_vectors /= np.linalg.norm(track_vectors, axis=1, keepdims=True)
        y_vectors = np.cross(track_vectors, z_vectors)
        x_vectors = np.cross(z_vectors, y_vectors)
        if (z_axis - track_axis) % 3 != 2:
            x_vectors = - x_vectors
        vectors = [None, None, None]
        vectors[z_axis] = z_vectors
        vectors[track_axis] = x_vectors
        vectors[y_axis] = y_vectors
        matrices = np.dstack(vectors)
        matrices = np.transpose(matrices, axes=(0,2,1))
        matrices = np.linalg.inv(matrices)
        quats = [Matrix(m).to_quaternion() for m in matrices]
        return quats

    @staticmethod
    def _quats_from_matrices(curve, matrices, z_axis = 'Z',
                    intersection_params = DEFAULT_INTERSECTION_PARAMS):
        pairs = []
        for matrix in matrices:
            tk, quat = SvFrameAlongCurveField._matrix_to_curve(curve, matrix,
                                                               z_axis=z_axis,
                                                               intersection_params=intersection_params)
            quat = list(quat)
            pairs.append((tk, quat))

        pairs = list(sorted(pairs, key = lambda p: p[0]))
        quats = [p[1] for p in pairs]
        tknots = [p[0] for p in pairs]
        return quats, tknots

    def _init_slerp(self):
        if len(self.quats) == 1:
            self.slerp = lambda ts: Rotation.from_quat([self.quats[0] for t in ts])
        else:
            u_min, u_max = self.curve.get_u_bounds()
            if self.tknots[0] != u_min:
                self.tknots.insert(0, u_min)
                self.quats.insert(0, self.quats[0])

            if self.tknots[-1] != u_max:
                self.tknots.append(u_max)
                self.quats.append(self.quats[-1])

            self.quats = Rotation.from_quat(self.quats)
            self.tknots = np.array(self.tknots)
            self.tknots = (self.tknots - u_min) / (u_max - u_min)
            #self.t_min, self.t_max = min(self.tknots), max(self.tknots)
            #self.tknots = (self.tknots - self.t_min) / (self.t_max - self.t_min)
            if self.interpolation == SvFrameAlongCurveField.INTERP_LINEAR:
                self.slerp = Slerp(self.tknots, self.quats)
            else:
                self.slerp = RotationSpline(self.tknots, self.quats)

    @staticmethod
    def _matrix_to_curve(curve, matrix, z_axis,
                         intersection_params = DEFAULT_INTERSECTION_PARAMS):
        plane = PlaneEquation.from_matrix(matrix, normal_axis=z_axis)

        nurbs_curve = SvNurbsCurve.to_nurbs(curve)
        if nurbs_curve is None:
            is_nurbs = False
        else:
            curve = nurbs_curve
            is_nurbs = True
        # Or take nearest point?
        solutions = intersect_curve_plane(curve, plane,
                        method = NURBS if is_nurbs else EQUATION,
                        init_samples = intersection_params.init_samples,
                        tolerance = intersection_params.tolerance,
                        maxiter = intersection_params.max_iterations)
        t, point = SvFrameAlongCurveField._nearest_solution(matrix.translation, solutions)
        if t is None:
            raise Exception(f"Can't project the matrix {matrix} to the {curve}!")
        #matrix.translation = Vector(point)
        return t, matrix.to_quaternion()

    @staticmethod
    def _nearest_solution(point, solutions):
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
        if self.parametrization == SvFrameAlongCurveField.CURVE_PARAMETER:
            ts = pts[:,z_axis]
        else:
            solver = SvCurveLengthSolver(self.curve)
            solver.prepare('SPL', self.length_resolution)
            lengths = pts[:,z_axis]
            ts = solver.solve(lengths)
            t_min, t_max = self.curve.get_u_bounds()
            ts = np.clip(ts, t_min, t_max)
        quats = self.slerp(ts).as_quat(scalar_first=False)
        matrices = [Quaternion(q).to_matrix() for q in quats]
        matrices = np.array(matrices)
        zero_pts = pts.copy()
        zero_pts[:,z_axis] = 0
        new_pts = np_multiply_matrices_vectors(matrices, zero_pts)
        origins = self.curve.evaluate_array(ts)
        new_pts += origins
        R = (new_pts - pts).T
        return R[0], R[1], R[2]

    def evaluate(self, x, y, z):
        rxs, rys, rzs = self.evaluate_grid([x], [y], [z])
        return rxs[0], rys[0], rzs[0]

