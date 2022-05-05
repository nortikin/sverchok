
import numpy as np

from mathutils import kdtree
from mathutils.bvhtree import BVHTree

from sverchok.utils.curve import SvCurve, SvIsoUvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.logging import debug, info, getLogger
from sverchok.utils.geom import PlaneEquation, LineEquation, locate_linear
from sverchok.dependencies import scipy

if scipy is not None:
    from scipy.optimize import root_scalar, root, minimize_scalar, minimize

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
    """
    Find the orthogonal projection of src_point to curve.
    inputs:
    * src_point: np.array of shape (3,)
    * curve: SvCurve
    * subdomain: either (u_min, u_max) or None (use whole curve)
    * init_samples: first subdivide the curve in N segments; search for the
      orthogonal projection on each segment.
    * on_fail: what to do if no projection was found:
        FAIL - raise exception
        RETURN_NONE - return None

    dependencies: scipy
    """
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

def nearest_point_on_curve(src_points, curve, samples=10, precise=True, method='Brent', output_points=True, logger=None):
    """
    Find nearest point on any curve.
    """
    if logger is None:
        logger = getLogger()

    t_min, t_max = curve.get_u_bounds()

    def init_guess(curve, points_from):
        us = np.linspace(t_min, t_max, num=samples)

        points = curve.evaluate_array(us).tolist()
        #print("P:", points)

        kdt = kdtree.KDTree(len(us))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        us_out = []
        nearest_out = []
        for point_from in points_from:
            nearest, i, distance = kdt.find(point_from)
            us_out.append(us[i])
            nearest_out.append(tuple(nearest))

        return us_out, np.array(nearest_out)

    def goal(t):
        dv = curve.evaluate(t) - np.array(src_point)
        return np.linalg.norm(dv)

    init_ts, init_points = init_guess(curve, src_points)
    result_ts = []
    if precise:
        for src_point, init_t, init_point in zip(src_points, init_ts, init_points):
            delta_t = (t_max - t_min) / samples
            logger.debug("T_min %s, T_max %s, init_t %s, delta_t %s", t_min, t_max, init_t, delta_t)
            if init_t <= t_min:
                if init_t - delta_t >= t_min:
                    bracket = (init_t - delta_t, init_t, t_max)
                else:
                    bracket = None # (t_min, t_min + delta_t, t_min + 2*delta_t)
            elif init_t >= t_max:
                if init_t + delta_t <= t_max:
                    bracket = (t_min, init_t, init_t + delta_t)
                else:
                    bracket = None # (t_max - 2*delta_t, t_max - delta_t, t_max)
            else:
                bracket = (t_min, init_t, t_max)
            result = minimize_scalar(goal,
                        bounds = (t_min, t_max),
                        bracket = bracket,
                        method = method
                    )

            if not result.success:
                if hasattr(result, 'message'):
                    message = result.message
                else:
                    message = repr(result)
                raise Exception("Can't find the nearest point for {}: {}".format(src_point, message))

            t0 = result.x
            if t0 < t_min:
                t0 = t_min
            elif t0 > t_max:
                t0 = t_max
            result_ts.append(t0)
    else:
        result_ts = init_ts

    if output_points:
        if precise:
            result_points = curve.evaluate_array(np.array(result_ts))
            return list(zip(result_ts, result_points))
        else:
            return list(zip(result_ts, init_points))
    else:
        return result_ts

def nearest_point_on_nurbs_curve(src_point, curve, init_samples=50, splits=3, method='Brent', linearity_threshold=1e-4):
    """
    Find nearest point on a NURBS curve.
    At the moment, this method is not, in general, faster than generic
    nearest_point_on_curve() method; although this method can be more precise.
    """

    src_point = np.asarray(src_point)
    default_splits = splits

    def farthest(cpts):
        distances = np.linalg.norm(src_point - cpts)
        return distances.max()

    def too_far(segment, distance):
        return segment.is_strongly_outside_sphere(src_point, distance)
        #bbox = segment.get_bounding_box()
        #ctr = bbox.mean()
        #distance_to_ctr = np.linalg.norm(ctr - src_point)
        #return (distance_to_ctr > bbox.radius() + distance)

    def split(segment, n_splits=splits):
        u_min, u_max = segment.get_u_bounds()
        us = np.linspace(u_min, u_max, num=n_splits+1)
        segments = [segment.cut_segment(u1, u2) for u1, u2 in zip(us, us[1:])]
        return segments

    def goal(t):
        dv = curve.evaluate(t) - src_point
        return (dv * dv).sum()
        #return np.linalg.norm(dv)

    def numeric_method(segment, approx=None):
        u_min, u_max = segment.get_u_bounds()
        if approx is not None:
            bracket = (u_min, approx, u_max)
        else:
            bracket = (u_min, u_max)
        result = minimize_scalar(goal,
                bounds = (u_min, u_max),
                bracket = bracket,
                method = method)

        if not result.success:
            if hasattr(result, 'message'):
                message = result.message
            else:
                message = repr(result)
            print(f"No solution for {u_min} - {u_max}: {message}")
            return None
        else:
            t0 = result.x
            if u_min <= t0 <= u_max:
                return t0, result.fun
            else:
                return None

    def merge(segments):
        if len(segments) <= 1:
            return segments
        result_us = []
        prev_start, prev_end = segments[0].get_u_bounds()
        current_pair = [prev_start, prev_end]
        to_end_last = False
        for segment in segments[1:]:
            to_end_last = False
            u1, u2 = segment.get_u_bounds()
            if u1 == current_pair[1]:
                current_pair[1] = u2
                to_end_last = True
            else:
                result_us.append(current_pair)
                current_pair = list(segment.get_u_bounds())

        result_us.append(current_pair)

        result = [curve.cut_segment(u1,u2) for u1, u2 in result_us]
        #print(f"Merge: {[s.get_u_bounds() for s in segments]} => {[s.get_u_bounds() for s in result]}")
        return result

    def linear_search(segment):
        cpts = segment.get_control_points()
        start, end = cpts[0], cpts[-1]
        line = LineEquation.from_two_points(start, end)
        p = line.projection_of_point(src_point)
        t = locate_linear(start, end, p)
        if 0.0 <= t <= 1.0:
            u1, u2 = segment.get_u_bounds()
            u = (1-t)*u1 + t*u2
            return u
        else:
            return None

    def process(segments, min_distance=0.0, step=0, n_splits=splits):
        if not segments:
            return []

        #print("Consider: ", [s.get_u_bounds() for s in segments])

        to_remove = set()
        for segment1_idx, segment1 in enumerate(segments):
            if segment1_idx in to_remove:
                continue
            farthest_distance = farthest(segment1.get_control_points())
            #print(f"S1: {segment1_idx}, {segment1.get_u_bounds()}: farthest = {farthest_distance}, min_distance={min_distance}")
            for segment2_idx, segment2 in enumerate(segments):
                if segment1_idx == segment2_idx:
                    continue
                if segment2_idx in to_remove:
                    continue
                if too_far(segment2, min(farthest_distance, min_distance)):
                    print(f"S2: {segment2_idx} {segment2.get_u_bounds()} - too far, remove")
                    to_remove.add(segment2_idx)

        stop_subdivide = step > 6
        #if stop_subdivide:
            #print("Will not subdivide anymore")
        if len(to_remove) == 0:
            n_splits += 2
        #else:
        #    n_splits = default_splits
        segments_to_consider = [segment for i, segment in enumerate(segments) if i not in to_remove]
        #segments_to_consider = merge(segments_to_consider)

        results = []
        new_segments = []
        for_numeric = []
        for segment in segments_to_consider:
            if segment.is_line(linearity_threshold):
                # find nearest on line
                print(f"Linear search for {segment.get_u_bounds()}")
                approx = linear_search(segment)
                if approx is not None:
                    result = numeric_method(segment, approx)
                    if result:
                        results.append(result)
            elif stop_subdivide:
                print(f"Schedule for numeric, subdivision is stopped: {segment.get_u_bounds()}")
                for_numeric.append(segment)
            elif segment.has_exactly_one_nearest_point(src_point):
                print(f"Schedule for numeric, it has one nearest point: {segment.get_u_bounds()}")
                for_numeric.append(segment)
            else:
                #print(f"Subdivide {segment.get_u_bounds()} at step {step}, into {n_splits} segments")
                sub_segments = split(segment, n_splits)
                new_segments.extend(sub_segments)

        for_numeric = merge(for_numeric)
        for segment in for_numeric:
            print(f"Run numeric method on {segment.get_u_bounds()}")
            result = numeric_method(segment)
            if result:
                results.append(result)

        if results:
            new_min_distance = min([r[1] for r in results])
        else:
            new_min_distance = min_distance
        return results + process(new_segments, min_distance=new_min_distance, step=step+1, n_splits=n_splits)

    def postprocess(rs):
        m = min(r[1] for r in rs)
        return [r[0] for r in rs if r[1] == m]

    u_min, u_max = curve.get_u_bounds()
    us = np.linspace(u_min, u_max, num=init_samples+1)
    init_points = curve.evaluate_array(us)
    init_distances = np.linalg.norm(init_points - src_point, axis=1)
    min_distance = init_distances.min()

    segments = split(curve)#, init_samples)
    rs = process(segments, min_distance=min_distance)
    rs = postprocess(rs)
    return rs

def ortho_project_surface(src_point, surface, init_samples=10, maxiter=30, tolerance=1e-4):
    """
    Find the orthogonal projection of src_point to surface.
    dependencies: scipy
    """
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

    dependencies: scipy
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

def intersect_curve_surface(curve, surface, init_samples=10, raycast_samples=10, tolerance=1e-3, maxiter=50, raycast_method='hybr', support_nurbs=False):
    """
    Intersect a curve with a surface.
    dependencies: scipy
    """
    u_min, u_max = curve.get_u_bounds()
    is_nurbs = False
    c = SvNurbsCurve.to_nurbs(curve)
    if c is not None:
        curve = c
        is_nurbs = True

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

    def to_curve(point, curve, u1, u2, raycast=None):
        if support_nurbs and is_nurbs and raycast is not None:
            segment = curve.cut_segment(u1, u2)
            surface_u, surface_v = raycast.us[0], raycast.vs[0]
            point_on_surface = raycast.points[0]
            surface_normal = surface.normal(surface_u, surface_v)
            plane = PlaneEquation.from_normal_and_point(surface_normal, point_on_surface)
            r = intersect_curve_plane_nurbs(segment, plane,
                        init_samples=2,
                        tolerance=tolerance,
                        maxiter=maxiter)
            if not r:
                return None
            else:
                return r[0]
        else:
            ortho = ortho_project_curve(point, curve,
                        subdomain = (u1, u2),
                        init_samples = 2,
                        on_fail = RETURN_NONE)
            if ortho is None:
                return None
            else:
                return ortho.nearest_u, ortho.nearest

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
        raycast = None
        while True:
            i += 1
            if i > maxiter:
                raise Exception("Maximum number of iterations is exceeded; last step {} - {} = {}".format(prev_prev_point, point, step))

            on_curve = to_curve(prev_point, curve, u1, u2, raycast=raycast)
            if on_curve is None:
                break
            u_root, point = on_curve
            if u_root < u1 or u_root > u2:
                break
            step = np.linalg.norm(point - prev_point)
            if step < tolerance and i > 1:
                debug("After ortho: Point {}, prev {}, iter {}".format(point, prev_point, i))
                point_found = True
                break

            prev_point = point
            tangent = curve.tangent(u_root)
            sign, raycast = do_raycast(point, tangent, sign)
            if raycast is None:
                raise Exception("Iteration #{}: Can't do a raycast with point {}, direction {} onto surface {}".format(i, point, tangent, surface))
            point = raycast.points[0]
            step = np.linalg.norm(point - prev_point)
            prev_prev_point = prev_point
            prev_point = point

        if point_found:
            result.append((u_root, point))

    return result

def nearest_point_on_surface(points_from, surface, init_samples=50, precise=True, method='L-BFGS-B', sequential=False, output_points=True):

    u_min = surface.get_u_min()
    u_max = surface.get_u_max()
    v_min = surface.get_v_min()
    v_max = surface.get_v_max()

    def init_guess():
        us = np.linspace(u_min, u_max, num=init_samples)
        vs = np.linspace(v_min, v_max, num=init_samples)
        us, vs = np.meshgrid(us, vs)
        us = us.flatten()
        vs = vs.flatten()

        points = surface.evaluate_array(us, vs).tolist()

        kdt = kdtree.KDTree(len(us))
        for i, v in enumerate(points):
            kdt.insert(v, i)
        kdt.balance()

        us_out = []
        vs_out = []
        nearest_out = []
        for point_from in points_from:
            nearest, i, distance = kdt.find(point_from)
            us_out.append(us[i])
            vs_out.append(vs[i])
            nearest_out.append(tuple(nearest))

        return us_out, vs_out, nearest_out

    def goal(point_from):
        def distance(p):
            dv = surface.evaluate(p[0], p[1]) - np.array(point_from)
            return (dv * dv).sum(axis=0)
        return distance

    init_us, init_vs, init_points = init_guess()
    result_us = []
    result_vs = []
    result_points = []

    prev_uv = None
    for src_point, init_u, init_v, init_point in zip(points_from, init_us, init_vs, init_points):
        if precise:
            if sequential and prev_uv is not None:
                x0 = np.array(prev_uv)
            else:
                x0 = np.array([init_u, init_v])

            result = minimize(goal(src_point),
                        x0 = x0,
                        bounds = [(u_min, u_max), (v_min, v_max)],
                        method = method
                    )
            if not result.success:
                raise Exception("Can't find the nearest point for {}: {}".format(src_point, result.message))
            u0, v0 = result.x
            prev_uv = result.x
        else:
            u0, v0 = init_u, init_v
            result_points.append(init_point)

        result_us.append(u0)
        result_vs.append(v0)

    if precise and output_points:
        result_points = surface.evaluate_array(np.array(result_us), np.array(result_vs)).tolist()

    if output_points:
        return result_us, result_vs, result_points
    else:
        return result_us, result_vs

ORTHO = 'ortho'
EQUATION = 'equation'
NURBS = 'nurbs'

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

    dependencies: scipy
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

    dependencies: scipy
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

def intersect_curve_plane_nurbs(curve, plane, init_samples=10, tolerance=1e-3, maxiter=50):
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

    def check_signs(segment):
        cpts = segment.get_control_points()
        signs = plane.side_of_points(cpts)
        all_one_side = (signs > 0).all() or (signs < 0).all()
        return not all_one_side

    def middle(segment):
        u1, u2 = segment.get_u_bounds()
        u = (u1+u2)*0.5
        return u

    def split(segment):
        u = middle(segment)
        return segment.split_at(u)

    def is_small(segment):
        bbox = segment.get_bounding_box()
        return bbox.size() < tolerance

    def locate_p(p1, p2, p):
        if abs(p1[0] - p2[0]) > tolerance:
            return (p[0] - p1[0]) / (p2[0] - p1[0])
        elif abs(p1[1] - p2[1]) > tolerance:
            return (p[1] - p1[1]) / (p2[1] - p1[1])
        else:
            return (p[2] - p1[2]) / (p2[2] - p1[2])

    def intersect_line(segment):
        cpts = segment.get_control_points()
        p1, p2 = cpts[0], cpts[-1]
        line = LineEquation.from_two_points(p1, p2)
        p = plane.intersect_with_line(line)
        p = np.array(p)
        u = locate_p(p1, p2, p)
        u1, u2 = segment.get_u_bounds()
        if u >= 0 and u <= 1.0:
            v = (1-u)*u1 + u*u2
            return v, p
        else:
            return None

    def solve(segment, i=0):
        if check_signs(segment):
            if is_small(segment):
                cpts = segment.get_control_points()
                p1, p2 = cpts[0], cpts[-1]
                p = 0.5*(p1 + p2)
                u = middle(segment)
                #print(f"I: small segment: {u} - {p}")
                return [(u, p)]
            elif segment.is_line(tolerance):
                r = intersect_line(segment)
                if r is None:
                    return []
                else:
                    #print(f"I: linear: {r}")
                    return [r]
            else:
                if i > maxiter:
                    raise Exception("Maximum number of subdivision iterations reached")
                s1, s2 = split(segment)
                return solve(s1, i+1) + solve(s2, i+1)
        else:
            return []

    segments = [curve.cut_segment(u1, u2) for u1, u2 in good_ranges]
    solutions = [solve(segment) for segment in segments]
    return sum(solutions, [])

def intersect_curve_plane(curve, plane, method = EQUATION, **kwargs):
    """
    Call for intersect_curve_plane_equation, intersect_curve_plane_ortho,
    or intersect_curve_plane_nurbs, depending on `method` parameter.
    Inputs and outputs: see corresponding method docs.
    """
    if method == EQUATION:
        return intersect_curve_plane_equation(curve, plane, **kwargs)
    elif method == ORTHO:
        return intersect_curve_plane_ortho(curve, plane, **kwargs)
    elif method == NURBS:
        return intersect_curve_plane_nurbs(curve, plane, **kwargs)
    else:
        raise Exception("Unsupported method")

