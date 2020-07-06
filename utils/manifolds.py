
import numpy as np
from math import sqrt, atanh, sinh, cosh

from mathutils import kdtree
from mathutils.bvhtree import BVHTree

from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok.utils.logging import debug, info
from sverchok.utils.geom import PlaneEquation, LineEquation

from sverchok.dependencies import scipy, skimage
from sverchok.utils.marching_squares import make_contours

if scipy is not None:
    from scipy.optimize import root_scalar, root

if skimage is not None:
    from skimage import measure

SKIP = 'skip'
FAIL = 'fail'
RETURN_NONE = 'none'

class CurveProjectionResult(object):
    def __init__(self, us, points, source):
        self.us = us
        self.points = points
        self.source = source

        self.kdt = kdt = kdtree.KDTree(len(points))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        nearest, i, distance = kdt.find(source)
        self.nearest = np.array(nearest)
        self.nearest_idx = i
        self.nearest_distance = distance
        self.nearest_u = us[i]

def ortho_project_curve(src_point, curve, subdomain = None, init_samples=10, on_fail=FAIL):
    def goal(t):
        point_on_curve = curve.evaluate(t)
        dv = src_point - point_on_curve
        tangent = curve.tangent(t)
        return dv.dot(tangent)

    if subdomain is None:
        u_min, u_max = curve.get_u_bounds()
    else:
        u_min, u_max = subdomain
    u_samples = np.linspace(u_min, u_max, num=init_samples)

    u_ranges = []
    prev_value = goal(u_min)
    prev_u = u_min
    for u in u_samples[1:]:
        value = goal(u)
        if value * prev_value <= 0:
            u_ranges.append((prev_u, u))
        prev_u = u
        prev_value = value

    points = []
    us = []
    for u1, u2 in u_ranges:
        u0 = (u1 + u2) / 2.0
        result = root_scalar(goal, method='ridder',
                        bracket = (u1, u2),
                        x0 = u0)
        u = result.root
        us.append(u)
        point = curve.evaluate(u)
        points.append(point)

    if not us:
        if on_fail == FAIL:
            raise Exception("Can't calculate the projection of {} onto {}".format(src_point, curve))
        elif on_fail == RETURN_NONE:
            return None
        else:
            raise Exception("Unsupported on_fail value")
    result = CurveProjectionResult(us, points, src_point)
    return result

def ortho_project_surface(src_point, surface, init_samples=10, maxiter=30, tolerance=1e-4):
    u_min, u_max = surface.get_u_min(), surface.get_u_max()
    v_min, v_max = surface.get_v_min(), surface.get_v_max()

    u0 = (u_min + u_max) / 2.0
    v0 = (v_min + v_max) / 2.0

    fixed_axis = 'U'
    fixed_axis_value = u0
    prev_fixed_axis_value = v0
    prev_point = surface.evaluate(u0, v0)

    i = 0
    while True:
        if i > maxiter:
            raise Exception("No convergence")
        curve = SvIsoUvCurve(surface, fixed_axis, fixed_axis_value)
        projection = ortho_project_curve(src_point, curve, init_samples=init_samples)
        point = projection.nearest
        dv = point - prev_point
        fixed_axis_value = projection.nearest_u
        if np.linalg.norm(dv) < tolerance:
            break
        if fixed_axis == 'U':
            fixed_axis = 'V'
        else:
            fixed_axis = 'U'
        prev_fixed_axis_value = fixed_axis_value
        prev_point = point
        i += 1

    if fixed_axis == 'U':
        u, v = prev_fixed_axis_value, fixed_axis_value
    else:
        u, v = fixed_axis_value, prev_fixed_axis_value

    return u, v, point

class RaycastResult(object):
    def __init__(self):
        self.init_us = None
        self.init_vs = None
        self.init_ts = None
        self.init_points = None
        self.points = []
        self.uvs = []
        self.us = []
        self.vs = []

class RaycastInitGuess(object):
    def __init__(self):
        self.us = []
        self.vs = []
        self.ts = []
        self.nearest = []
        self.all_good = True

class SurfaceRaycaster(object):
    """
    Usage:
        
        raycaster = SurfaceRaycaster(surface)
        raycaster.init_bvh(samples)
        result = raycaster.raycast(src_points, directions, ...)
    """
    def __init__(self, surface):
        self.surface = surface
        self.bvh = None
        self.samples = None
        self.center_us = None
        self.center_vs = None

    def init_bvh(self, samples):
        self.samples = samples

        self.u_min = u_min = self.surface.get_u_min()
        self.u_max = u_max = self.surface.get_u_max()
        self.v_min = v_min = self.surface.get_v_min()
        self.v_max = v_max = self.surface.get_v_max()

        us = np.linspace(u_min, u_max, num=samples)
        vs = np.linspace(v_min, v_max, num=samples)
        us, vs = np.meshgrid(us, vs)
        self.us = us.flatten()
        self.vs = vs.flatten()

        points = self.surface.evaluate_array(self.us, self.vs).tolist()
        self.center_us, self.center_vs, faces = self._make_faces()

        self.bvh = BVHTree.FromPolygons(points, faces)

    def _make_faces(self):
        samples = self.samples
        uh2 = (self.u_max - self.u_min) / (2 * samples)
        vh2 = (self.v_max - self.v_min) / (2 * samples)
        faces = []
        center_us = []
        center_vs = []
        for row in range(samples - 1):
            for col in range(samples - 1):
                i = row * samples + col
                face = (i, i+samples, i+samples+1, i+1)
                u = self.us[i] + uh2
                v = self.vs[i] + vh2
                center_us.append(u)
                center_vs.append(v)
                faces.append(face)
        return center_us, center_vs, faces

    def _init_guess(self, src_points, directions):
        if self.bvh is None:
            raise Exception("You have to call init_bvh() method first!")

        guess = RaycastInitGuess()
        for src_point, direction in zip(src_points, directions):
            nearest, normal, index, distance = self.bvh.ray_cast(src_point, direction)
            if nearest is None:
                guess.us.append(None)
                guess.vs.append(None)
                guess.ts.append(None)
                guess.nearest.append(None)
                guess.all_good = False
            else:
                guess.us.append(self.center_us[index])
                guess.vs.append(self.center_vs[index])
                guess.ts.append(distance)
                guess.nearest.append(tuple(nearest))

        return guess

    def _goal(self, src_point, direction):
        def function(p):
            on_surface = self.surface.evaluate(p[0], p[1])
            on_line = src_point + direction * p[2]
            return (on_surface - on_line).flatten()
        return function

    def raycast(self, src_points, directions, precise=True, calc_points=True, method='hybr', on_init_fail = SKIP):
        result = RaycastResult()
        guess = self._init_guess(src_points, directions)
        result.init_us, result.init_vs = guess.us, guess.vs
        result.init_ts = guess.ts
        result.init_points = guess.nearest
        for point, direction, init_u, init_v, init_t, init_point in zip(src_points, directions, result.init_us, result.init_vs, result.init_ts, result.init_points):
            if init_u is None:
                if on_init_fail == SKIP:
                    continue
                elif on_init_fail == FAIL:
                    raise Exception("Can't find initial guess of the projection for {}".format(point))
                elif on_init_fail == RETURN_NONE:
                    return None
                else:
                    raise Exception("Invalid on_init_fail value")

            if precise:
                direction = np.array(direction)
                direction = direction / np.linalg.norm(direction)
                projection = root(self._goal(np.array(point), direction),
                            x0 = np.array([init_u, init_v, init_t]),
                            method = method)
                if not projection.success:
                    raise Exception("Can't find the projection for {}: {}".format(point, projection.message))
                u0, v0, t0 = projection.x
            else:
                u0, v0 = init_u, init_v
                result.points.append(init_point)

            result.uvs.append((u0, v0, 0))
            result.us.append(u0)
            result.vs.append(v0)

        if precise and calc_points:
            result.points = self.surface.evaluate_array(np.array(result.us), np.array(result.vs)).tolist()

        return result

def raycast_surface(surface, src_points, directions, samples=50, precise=True, calc_points=True, method='hybr', on_init_fail = SKIP):
    """Shortcut for SurfaceRaycaster"""
    raycaster = SurfaceRaycaster(surface)
    raycaster.init_bvh(samples)
    return raycaster.raycast(src_points, directions, precise=precise, calc_points=calc_points, method=method, on_init_fail=on_init_fail)

def intersect_curve_surface(curve, surface, init_samples=10, raycast_samples=10, tolerance=1e-3, maxiter=50, raycast_method='hybr'):
    u_min, u_max = curve.get_u_bounds()

    raycaster = SurfaceRaycaster(surface)
    raycaster.init_bvh(raycast_samples)

    def do_raycast(point, tangent, sign=1):
        good_sign = sign
        raycast = raycaster.raycast([point], [sign*tangent],
                    method = raycast_method,
                    on_init_fail = RETURN_NONE)
        if raycast is None:
            good_sign = -sign
            raycast = raycaster.raycast([point], [-sign*tangent],
                        method = raycast_method,
                        on_init_fail = RETURN_NONE)
        return good_sign, raycast

    good_ranges = []
    u_range = np.linspace(u_min, u_max, num=init_samples)
    points = curve.evaluate_array(u_range)
    tangents = curve.tangent_array(u_range)
    for u1, u2, p1, p2, tangent1, tangent2 in zip(u_range, u_range[1:], points, points[1:], tangents,tangents[1:]):
        raycast = raycaster.raycast([p1, p2], [tangent1, -tangent2],
                    precise = False, calc_points=False,
                    on_init_fail = RETURN_NONE)
        if raycast is None:
            continue
        good_ranges.append((u1, u2, raycast.points[0], raycast.points[1]))

    result = []
    for u1, u2, init_p1, init_p2 in good_ranges:

        tangent = curve.tangent(u1)
        point = curve.evaluate(u1)

        i = 0
        sign = 1
        prev_prev_point = None
        prev_point = init_p1
        u_root = None
        point_found = False
        while True:
            i += 1
            if i > maxiter:
                raise Exception("Maximum number of iterations is exceeded; last step {} - {} = {}".format(prev_prev_point, point, step))

            ortho = ortho_project_curve(prev_point, curve,
                        subdomain = (u1, u2),
                        init_samples = 2,
                        on_fail = RETURN_NONE)
            if ortho is None:
                break
            point = ortho.nearest
            u_root = ortho.nearest_u
            if u_root < u1 or u_root > u2:
                break
            step = np.linalg.norm(point - prev_point)
            if step < tolerance and i > 1:
                debug("After ortho: Point {}, prev {}, iter {}".format(point, prev_point, i))
                point_found = True
                break

            prev_point = point
            tangent = curve.tangent(ortho.nearest_u)
            sign, raycast = do_raycast(point, tangent, sign)
            if raycast is None:
                raise Exception("Can't do a raycast with point {}, direction {} onto surface {}".format(point, tangent, surface))
            point = raycast.points[0]
            step = np.linalg.norm(point - prev_point)
            prev_prev_point = prev_point
            prev_point = point

        if point_found:
            result.append((u_root, point))

    return result

ORTHO = 'ortho'
EQUATION = 'equation'

def intersect_curve_plane_ortho(curve, plane, init_samples=10, ortho_samples=10, tolerance=1e-3, maxiter=50):
    """
    Find intersections of curve and a plane, by combination of orthogonal projections with tangent projections.
    inputs:
        * curve : SvCurve
        * plane : sverchok.utils.geom.PlaneEquation
        * init_samples: number of samples to subdivide the curve to; this defines the maximum possible number
            of solutions the method will return (the solution is searched at each segment).
        * ortho_samples: number of samples for ortho_project_curve method
        * tolerance: target tolerance
        * maxiter: maximum number of iterations
    outputs:
        list of intersection points
    """
    u_min, u_max = curve.get_u_bounds()
    u_range = np.linspace(u_min, u_max, num=init_samples)
    init_points = curve.evaluate_array(u_range)
    init_signs = plane.side_of_points(init_points)
    good_ranges = []
    for u1, u2, sign1, sign2 in zip(u_range, u_range[1:], init_signs, init_signs[1:]):
        if sign1 * sign2 < 0:
            good_ranges.append((u1, u2))
    if not good_ranges:
        return []

    solutions = []
    for u1, u2 in good_ranges:
        u0 = u1
        tangent = curve.tangent(u0)
        tangent /= np.linalg.norm(tangent)
        point = curve.evaluate(u0)
        line = LineEquation.from_direction_and_point(tangent, point)

        p = plane.intersect_with_line(line)
        if p is None:
            u0 = u2
            tangent = curve.tangent(u0)
            tangent /= np.linalg.norm(tangent)
            point = curve.evaluate(u0)
            line = LineEquation.from_direction_and_point(tangent, point)
            p = plane.intersect_with_line(line)
            if p is None:
                raise Exception("Can't find initial point for intersection")

        i = 0
        prev_prev_point = None
        prev_point = np.array(p)
        while True:
            i += 1
            if i > maxiter:
                raise Exception("Maximum number of iterations is exceeded; last step {} - {} = {}".format(prev_prev_point, point, step))

            ortho = ortho_project_curve(prev_point, curve, init_samples = ortho_samples)
            point = ortho.nearest
            step = np.linalg.norm(point - prev_point)
            if step < tolerance:
                debug("After ortho: Point {}, prev {}, iter {}".format(point, prev_point, i))
                break

            prev_point = point
            tangent = curve.tangent(ortho.nearest_u)
            tangent /= np.linalg.norm(tangent)
            point = curve.evaluate(ortho.nearest_u)
            line = LineEquation.from_direction_and_point(tangent, point)
            point = plane.intersect_with_line(line)
            if point is None:
                raise Exception("Can't intersect a line {} with a plane {}".format(line, point))
            point = np.array(point)
            step = np.linalg.norm(point - prev_point)
            if step < tolerance:
                debug("After raycast: Point {}, prev {}, iter {}".format(point, prev_point, i))
                break

            prev_prev_point = prev_point
            prev_point = point

        solutions.append(point)

    return solutions

def intersect_curve_plane_equation(curve, plane, init_samples=10, tolerance=1e-3, maxiter=50):
    """
    Find intersections of curve and a plane, by directly solving an equation.
    inputs:
        * curve : SvCurve
        * plane : sverchok.utils.geom.PlaneEquation
        * init_samples: number of samples to subdivide the curve to; this defines the maximum possible number
            of solutions the method will return (the solution is searched at each segment).
        * tolerance: target tolerance
        * maxiter: maximum number of iterations
    outputs:
        list of 2-tuples:
            * curve T value
            * point at the curve
    """
    u_min, u_max = curve.get_u_bounds()
    u_range = np.linspace(u_min, u_max, num=init_samples)
    init_points = curve.evaluate_array(u_range)
    init_signs = plane.side_of_points(init_points)
    good_ranges = []
    for u1, u2, sign1, sign2 in zip(u_range, u_range[1:], init_signs, init_signs[1:]):
        if sign1 * sign2 < 0:
            good_ranges.append((u1, u2))
    if not good_ranges:
        return []

    plane_normal = np.array(plane.normal)
    plane_d = plane.d

    def goal(t):
        point = curve.evaluate(t)
        value = (plane_normal * point).sum() + plane_d
        return value

    solutions = []
    for u1, u2 in good_ranges:
        sol = root_scalar(goal, method='ridder',
                bracket = (u1, u2),
                xtol = tolerance,
                maxiter = maxiter)
        u = sol.root
        point = curve.evaluate(u)
        solutions.append((u, point))

    return solutions

def intersect_curve_plane(curve, plane, method = EQUATION, **kwargs):
    """
    Call for intersect_curve_plane_equation or intersect_curve_plane_ortho,
    depending on `method` parameter.
    Inputs and outputs: see corresponding method docs.
    """
    if method == EQUATION:
        return intersect_curve_plane_equation(curve, plane, **kwargs)
    elif method == ORTHO:
        return intersect_curve_plane_ortho(curve, plane, **kwargs)
    else:
        raise Exception("Unsupported method")

