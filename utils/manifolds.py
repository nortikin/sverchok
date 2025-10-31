
import numpy as np

from mathutils import kdtree
from mathutils.bvhtree import BVHTree

from sverchok.utils.curve import SvIsoUvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.sv_logging import sv_logger, get_logger
from sverchok.utils.geom import PlaneEquation, LineEquation, locate_linear
from sverchok.dependencies import scipy

from mathutils import Vector
from mathutils.geometry import intersect_plane_plane, intersect_line_plane, normal as face_normal

if scipy is not None:
    from scipy.optimize import root_scalar, root, minimize_scalar, minimize

SKIP = 'skip'
FAIL = 'fail'
RETURN_NONE = 'none'

module_logger = get_logger()

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
        logger = module_logger

    t_min, t_max = curve.get_u_bounds()


    def init_guess(curve, points_from):
        us = np.linspace(t_min, t_max, num=samples)

        points = curve.evaluate_array(us).tolist()

        polygons = [(i, i+1, i) for i in range(len(points)-1)]
        tree = BVHTree.FromPolygons( points, polygons, all_triangles = True ) # trick to search nearest points to edges

        us_out = []
        nearest_out = []
        is_closed = curve.is_closed()
        for point_from in points_from:
            # See: https://github.com/nortikin/sverchok/pull/4876 (ru)
            # Find start point for next steps for finding nearest point.
            nearest, normal, segment_i, distance = tree.find_nearest( point_from )
            nearest = np.array(nearest)
            
            # read this algorithm with image:
            # 1. General description: https://user-images.githubusercontent.com/14288520/212554689-b210fae1-d61a-47d2-90c8-33d32bd84490.png
            # 2. Examples: https://user-images.githubusercontent.com/14288520/212501468-69d43635-c7e5-4e7e-819c-d4e5bb34de0a.png
            
            # What points t01 was used in this algorithm. Algorithm select other segments_i because of drawback of counting
            log_t01 = []
            # At first time get point of intersection with line segment not curve segment.
            # If new point of intersection is not segment_i then select prev or next segment.
            # If it is not help then raise exception and think again. )))
            # 6 times is appoximating max count of attemps to count accurate point as nearest point.
            # Algorithm can go up to 5 times of selecting 
            for iter_over_segment in range(6):
                if iter_over_segment>=5:
                    raise TypeError( f'Can not calc start point #{points_from.index(point_from)} on segment {segment_i}, {point_from}. Drawback of counting algorithm. Exceed limit of iterations {iter_over_segment}.' )

                # Go throght the segment of curve
                # Search plane at begining of segment
                if segment_i==0 and is_closed==False:
                    # If current line segment is at begining of unclosed curve then searchable plane (red line) is perpendicular to current line segment
                    # and plane's normal equals line segment (norm_1)
                    # https://user-images.githubusercontent.com/14288520/212556100-841744af-2f89-4787-8471-6fb8f173f7d9.png
                    p1 = np.array(points[segment_i+0])
                    p2 = np.array(points[segment_i+1])
                    norm_1 = Vector(p2-p1).normalized()
                else:
                    if segment_i==0 and is_closed==True:
                        # If curve are closed then first and last points are equals then algorithm skip that point and
                        # select previous point for calculation.
                        # https://user-images.githubusercontent.com/14288520/212501785-fa7590bc-3acd-40bd-b4c6-65e31fc0b32b.png
                        p0 = np.array(points[-2]) # skip -1 and select -2 (-1 and zero points are equals)
                        p1 = np.array(points[0])
                        p2 = np.array(points[1])
                    else:
                        # For other points select -1, 0, +1 points (If curve are closed or not closed it is not important)
                        # https://user-images.githubusercontent.com/14288520/212501870-46b5dc10-6840-4047-b2cf-b9db13777a8e.png 
                        p0 = np.array(points[segment_i-1])
                        p1 = np.array(points[segment_i])
                        p2 = np.array(points[segment_i+1])

                    # Get bisect at point p1:
                    # https://user-images.githubusercontent.com/14288520/212501932-2b26b943-7fdd-42a7-a171-6f644c360661.png 
                    vec01 = Vector(p1-p0)
                    vec01_norm = vec01.normalized()
                    vec12 = Vector(p2-p1)
                    vec12_norm = vec12.normalized()

                    # A bisect is a normal norm_1 to start of curve segment
                    norm_1 = (vec01_norm + vec12_norm).normalized()

                
                # Find plane at the end of segment
                if segment_i==samples-2 and is_closed==False:
                    # If current curve segment is last and curve is not closed then searchable plane is perpendicular to end of current
                    # curve segment
                    # https://user-images.githubusercontent.com/14288520/212530354-e4c94cde-e444-41a5-8a1a-96174aef462b.png
                    p1 = np.array(points[segment_i+0])
                    p2 = np.array(points[segment_i+1])
                    norm_2 = Vector( p2-p1 ).normalized()
                else:
                    if segment_i==samples-2 and is_closed==True:
                        # If curve is closed then skip start point of curve and get 1-st point (not zero point. segment_i+1==0 point)
                        # https://user-images.githubusercontent.com/14288520/212530745-1bfcf416-fdca-464e-9791-56ac7a07161f.png
                        p1 = np.array( points[segment_i+0] )
                        p2 = np.array( points[segment_i+1] )
                        p3 = np.array( points[  1] )
                    else:
                        # For other points takes current, current+1, current+2 points.
                        # https://user-images.githubusercontent.com/14288520/212531194-9b8f1a07-f155-4bed-95ae-68a3479ad00b.png
                        p1 = np.array(points[ segment_i ])
                        p2 = np.array(points[ segment_i+1 ])
                        p3 = np.array(points[ segment_i+2 ])
                        
                    # Calc bisect at the end of line segment and next line segment:
                    vec12 = Vector(p2-p1)
                    vec12_norm = vec12.normalized()
                    vec23 = Vector(p3-p2)
                    vec23_norm = vec23.normalized()

                    # Bisect is a normal of searchable plane and is perpendicular of the end of segment:
                    # https://user-images.githubusercontent.com/14288520/212531391-cf60e6c5-408c-4f8f-bdeb-91acf7b0c582.png
                    norm_2 = (vec12_norm + vec23_norm).normalized()
                
                # There is two planes and their normals and now can be calculated line of intersection of planes,
                # https://user-images.githubusercontent.com/14288520/212531588-d1b7385b-4146-4f4f-a546-dd56bfacd14e.png
                line_point, line_vec = intersect_plane_plane(p1, norm_1, p2, norm_2)

                if line_point is None or line_vec is None:
                    # If planes are not intersected they are parallel and point tree.find_nearest is the nearest point at all.
                    pass
                elif segment_i==0 and is_closed==False and (nearest==p1).all():
                    # If first point on curve is a nearest to point_from then tree.find_nearest is the result.
                    # https://user-images.githubusercontent.com/14288520/212556932-f5e801e5-8fe0-4e96-845b-ecf237e72f14.png
                    pass
                elif segment_i==samples-2 and is_closed==False and (nearest==p2).all():
                    # If last point on curve is a nearest to point_from then tree.find_nearest is the result.
                    # https://user-images.githubusercontent.com/14288520/212556890-d721095d-1a38-4920-aa2a-b3aea804b3a4.png
                    pass
                else:
                    # Create plane by line (norm_1-norm_2) and point (point_from) to find a cross with line segment_i. This point is a
                    # first approximation to curve (point on a line segment of curve segment is a raw result and is better than simple perpendicular
                    # to line segment from source point)
                    face_p0, face_p1, face_p2 = line_point, line_point+line_vec, point_from
                    face_norm = face_normal(face_p0, face_p1, face_p2)
                    point_intersect = intersect_line_plane(p1, p2, point_from, face_norm)
                    #print(f"segment_i={segment_i}, line_point={line_point.xyz}, point_intersect={point_intersect}")
                    # Set nearest to the point of cross face_norm and segment_i
                    # https://user-images.githubusercontent.com/14288520/212532084-a758d899-e7f9-474e-8a56-8c996b8e380c.png
                    nearest = np.array(point_intersect)

                # Find raw_t on a segment

                segment_p0 = np.array(points[segment_i])
                segment_p1 = np.array(points[segment_i+1])

                segment_p10 = segment_p1 - segment_p0
                max_dist = segment_p10[abs( segment_p10 ).argmax()]
                
                nearest_p0 = nearest - segment_p0
                # what distance to p0 by axis is max?
                # https://user-images.githubusercontent.com/14288520/212532480-89b93d9d-7019-4f58-95a7-76ef537a2001.png
                dist_nearest_to_p0 = nearest_p0[abs(nearest_p0).argmax()] 

                nearest_point = None
                us0 = us[segment_i]
                # Count of segments always less count of points.
                us1 = us[segment_i+1]
                
                t01 = dist_nearest_to_p0/max_dist
                # If t is out of range[0-1] then select previous or next segment. Some times source points are very close to
                # the end points of line segment and algorithm start switch forward and back between selecting of sectors endless.
                # https://user-images.githubusercontent.com/14288520/212533422-8cd0b4eb-6013-47b3-a80a-607cc55e5daa.png
                
                # Test switching is cyclic.
                if t01 in log_t01:
                    # Manually select t01:
                    if t01<0: #if abs(t01)<0.00001:
                        t01 = 0
                    elif t01>1: #if abs(t01-1)<0.00001:
                        t01 = 1
                    else:
                        # This is strange point of algorithm. I don't know what to do if this happens. (Never happens before)
                        pass
                else:
                    # Save t01 to test cyclic in the future
                    log_t01.append( t01 )

                if t01<0 and segment_i==0 and is_closed==False:
                    # if t01 is on the left of left point of curve if curve is unclose then set this point as nearest.
                    # https://user-images.githubusercontent.com/14288520/212534357-1170f94c-d0c4-4dee-b6b6-ef0e420341b2.png
                    t01=0
                    raw_t = us[segment_i]
                    nearest_point = segment_p0
                elif t01<0 and segment_i==0 and is_closed==True:
                    # If t01 is on the left of left point of curve if curve is closed then select last segment
                    # of curve and recalc nearest
                    # https://user-images.githubusercontent.com/14288520/212535108-b1f552ee-5ddd-487b-8482-14b977a417a6.png
                    segment_i = samples-2
                    continue
                elif t01<0:
                    # if t01 is on the left of any middle of the curve segments then takes previous segment and recalc nearest point
                    # https://user-images.githubusercontent.com/14288520/212535214-ad2ceaf9-7014-43a4-865d-0305a54a4797.png
                    segment_i = segment_i-1
                    continue
                elif t01>1 and segment_i==samples-2 and is_closed==False:
                    # If t01 is right of right point on curve and curve is unclosed then select this point as nearest.
                    # https://user-images.githubusercontent.com/14288520/212535765-6eb06d65-4bb0-4404-8578-11c86697e95e.png
                    t01 = 1
                    raw_t = us[segment_i+1]
                    nearest_point = segment_p1
                elif t01>1 and segment_i==samples-2 and is_closed==True:
                    # If t01 is right of right point on curve and curve is closed then select first segment and go recalc
                    # https://user-images.githubusercontent.com/14288520/212535966-88fa3d52-5118-4560-ad9c-bc6e9d1bfa69.png
                    segment_i = 0
                    continue
                elif t01>1:
                    # If t01 is right of the middle segment on curve then select next segment and go recalc
                    # https://user-images.githubusercontent.com/14288520/212536223-956a7166-e58c-4e39-b7bf-7c43f0db5dc5.png
                    segment_i = segment_i+1
                    continue
                else:
                    # If t01 inside of segment then calc t01 projection.
                    # https://user-images.githubusercontent.com/14288520/212536439-776b4881-d746-44ea-b6b7-2fca8d9bd5ca.png
                    raw_t = us[segment_i] + t01*(us[segment_i+1]-us[segment_i])
                
                # Extend search range to surrounding segments because calculation can out of single segment.
                # Test if curve is closed.
                # https://user-images.githubusercontent.com/14288520/212537114-6d644998-5892-4fcf-b0ad-d5dc1bdbe0fd.png
                arr_intervals = [ [ us0, us1 ], ] 
                if segment_i==0:
                    us0 = us[segment_i]
                    # Third point is a transfer to start of curve. Use for test requirement to go to the next interval.
                    arr_intervals.append( [ us[segment_i-2], us[segment_i-1], us[0] ] )
                else:
                    us0 = us[segment_i-1]
                    arr_intervals[0][0] = us0

                if segment_i==samples-2:
                    us1 = us[segment_i+1]
                    # Third curve is a transfer to the end of curve.
                    arr_intervals.append( [ us[0], us[1], us[samples-1] ] )
                else:
                    us1 = us[segment_i+2]
                    arr_intervals[0][1] = us1
                
                # t0    - [0-1] in interval us[segment_i]-us[segment_i+1]
                # raw_t - translate t0 to curve t
                # nearest_t - if t0==0 or 1 then use points, else None and calc later
                us_out.append( ( arr_intervals, t01, raw_t, segment_p0, nearest_point, segment_p1 ) ) # interval to search minimum
                nearest_out.append(tuple(nearest))

                break # for iter_over_segment in range(6):

        return us_out, np.array(nearest_out)

    def goal(t):
        dv = curve.evaluate(t) - np.array(src_point)
        return np.linalg.norm(dv)

    intervals, init_points = init_guess(curve, src_points)
    result_ts = []
    result_points = []
    for src_point, interval, init_point in zip(src_points, intervals, init_points):

        t01       = interval[1]
        res_t     = interval[2]
        res_point = interval[4]  # remark: may be None. Calc of None will be later after getting final t.

        if precise==True:
            if t01==0 or t01==1:
                pass
            else:
                raw_t  = interval[2]
                bracket = (interval[0][0][0], raw_t, interval[0][0][1])
                bounds  = (interval[0][0][0], interval[0][0][1])
                
                logger.debug("T_min %s, T_max %s, init_t %s", t_min, t_max, raw_t)

                if method == 'Brent' or method == 'Golden':
                    t_segments = interval[0]
                    # Функция поиска точной минимальной точки может запускаться несколько раз для одной точки,
                    # т.к. диапозонов может быть 2. Определяется алгоритмом init_guess. Наличие минимума возможно
                    # и в первом цикле, поэтому не всегда расчёт минимума запускается на втором интервале.
                    for I in range( len(t_segments) ):
                        t_segments_I = t_segments[I]
                        bracket = (t_segments_I[0], t_segments_I[1])
                        result = minimize_scalar(goal,
                                    #bounds = bounds, - Use of `bounds` is incompatible with 'method=Brent/Golden'.
                                    bracket = bracket,
                                    method = method
                                )
                        if not result.success:
                            break
                        if I<=len(t_segments)-2:
                            # если результат находится на границе следующего сегмента (не в начале, а именно на одном из концов,
                            # т.к. направление поиска внутри сегментов неизвестно). Именно тут используется третье число,
                            # т.к. оно может быть признаком перехода к сегменту с другого конца кривой.
                            # Пример "рассуждения такой": алгоритм точного поиска вычисляет результат, а тут проверяется,
                            # если результат совпадает с одной из границ следующего диапазона, то перейти к расчёту в следующем
                            # диапазоне. В результате может оказаться, что граница диапазона является минимальной точкой.
                            # лишний раз убедились в том, что не ошиблись.
                            if ( result.x in t_segments[I+1] ) == False:
                                break
                else:
                    raw_t  = interval[2]
                    t_segments = interval[0]
                    # Функция поиска точной минимальной точки может запускаться несколько раз для одной точки,
                    # т.к. диапозонов может быть 2. Определяется алгоритмом init_guess. Наличие минимума возможно
                    # и в первом цикле, поэтому не всегда расчёт минимума запускается на втором интервале.
                    for I in range( len(t_segments) ):
                        t_segments_I = t_segments[I]
                        bracket = (t_segments_I[0], raw_t, t_segments_I[1])
                        bounds  = (t_segments_I[0], t_segments_I[1])
                        result = minimize_scalar(goal,
                                    bounds = bounds,
                                    bracket = bracket,
                                    method = method
                                )
                        if not result.success:
                            break
                        #print(f'result.x={result.x}')
                        if I<=len(t_segments)-2:
                            # если результат находится на границе следующего сегмента (не в начале, а именно на одном из концов,
                            # т.к. направление поиска внутри сегментов неизвестно). Именно тут используется третье число,
                            # т.к. оно может быть признаком перехода к сегменту с другого конца кривой.
                            # Пример "рассуждения такой": алгоритм точного поиска вычисляет результат, а тут проверяется,
                            # если результат совпадает с одной из границ следующего диапазона, то перейти к расчёту в следующем
                            # диапазоне. В результате может оказаться, что граница диапазона является минимальной точкой.
                            # лишний раз убедились в том, что не ошиблись.
                            if ( any( abs(result.x-x)<0.00001 for x in t_segments[I+1] ) ) == False:
                                break
                            else:
                                raw_t = result.x # Надо запомнить, т.к. новое значение этого параметра пойдёт на второй цикл поиска минимума (если второй цикл будет).

                if not result.success:
                    if hasattr(result, 'message'):
                        message = result.message
                    else:
                        message = repr(result)
                    raise Exception("Can't find the nearest point for {}: {}".format(src_point, message))

                res_t = result.x

        result_ts.append(res_t)
        result_points.append(res_point)

    if output_points:
        result_ts_none = []
        # get t where points is None value
        for i in range(len(result_points)):
            if result_points[i] is None:
                result_ts_none.append(result_ts[i])

        if len(result_ts_none)>0:
            # evaluate that points and save values:
            result_points_none = curve.evaluate_array(np.array(result_ts_none)).tolist()
            for i in range(len(result_points)):
                if result_points[i] is None:
                    result_points[i] = result_points_none.pop(0)

        return list(zip(result_ts, np.array(result_points) ))
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

class CurveSurfaceIntersections:
    def __init__(self):
        self.ts = []
        self.us = []
        self.vs = []
        self.points = []

    def add(self, t, u, v, point):
        self.ts.append(t)
        self.us.append(u)
        self.vs.append(v)
        self.points.append(point)

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
    for t1, t2, p1, p2, tangent1, tangent2 in zip(u_range, u_range[1:], points, points[1:], tangents,tangents[1:]):
        raycast = raycaster.raycast([p1, p2], [tangent1, -tangent2],
                    precise = False, calc_points=False,
                    on_init_fail = RETURN_NONE)
        if raycast is None:
            continue
        good_ranges.append((t1, t2, raycast.points[0], raycast.points[1]))

    def to_curve(point, curve, t1, t2, raycast=None):
        if support_nurbs and is_nurbs and raycast is not None:
            segment = curve.cut_segment(t1, t2)
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
            nearest = nearest_point_on_curve([point], curve.cut_segment(t1,t2), samples=2)
            if not nearest:
                return None
            else:
                return nearest[0]

    result = CurveSurfaceIntersections()
    for t1, t2, init_p1, init_p2 in good_ranges:

        tangent = curve.tangent(t1)
        point = curve.evaluate(t1)

        i = 0
        sign = 1
        prev_prev_point = None
        prev_point = init_p1
        t_root = None
        u_value = None
        v_value = None
        point_found = False
        raycast = None
        while True:
            i += 1
            if i > maxiter:
                raise Exception("Maximum number of iterations is exceeded; last step {} - {} = {}".format(prev_prev_point, point, step))

            on_curve = to_curve(prev_point, curve, t1, t2, raycast=raycast)
            if on_curve is None:
                break
            t_root, point = on_curve
            if t_root < t1 or t_root > t2:
                break
            step = np.linalg.norm(point - prev_point)
            if step < tolerance and i > 1:
                sv_logger.debug("After ortho: Point {}, prev {}, iter {}".format(point, prev_point, i))
                point_found = True
                break

            prev_point = point
            tangent = curve.tangent(t_root)
            sign, raycast = do_raycast(point, tangent, sign)
            if raycast is None:
                raise Exception("Iteration #{}: Can't do a raycast with point {}, direction {} onto surface {}".format(i, point, tangent, surface))
            point = raycast.points[0]
            u_value = raycast.us[0]
            v_value = raycast.vs[0]
            step = np.linalg.norm(point - prev_point)
            prev_prev_point = prev_point
            prev_point = point

        if point_found:
            result.add(t_root, u_value, v_value, point)

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
                sv_logger.debug("After ortho: Point {}, prev {}, iter {}".format(point, prev_point, i))
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
                sv_logger.debug("After raycast: Point {}, prev {}, iter {}".format(point, prev_point, i))
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
    def cut_to_segments(curve):
        u_min, u_max = curve.get_u_bounds()
        u_range = np.linspace(u_min, u_max, num=init_samples)
        return [curve.cut_segment(u1,u2) for u1, u2 in zip(u_range, u_range[1:])]

    def check_signs(segment):
        cpts = segment.get_control_points()
        signs = plane.side_of_points(cpts)
        all_one_side = (signs > 0).all() or (signs < 0).all()
        #print(f"Check: cpts {cpts} => signs {signs} => result not {all_one_side}")
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
            return v
        else:
            return None

    plane_inv_matrix = np.linalg.inv(np.array(plane.get_matrix()))
    is_rational = curve.is_rational()

    normalized_plane = plane.normalized()
    delta_z = normalized_plane.d

    def get_taylor_coeffs(segment):
        cpts = segment.get_control_points()
        cpts = np.array([plane_inv_matrix @ pt for pt in cpts])
        segment = segment.copy(control_points = cpts)
        taylor = segment.bezier_to_taylor()
        coeffs = taylor.get_coefficients()[:,2]
        return coeffs

    def solve_quadric(segment):
        coeffs = get_taylor_coeffs(segment)
        c,b,a = coeffs
        c += delta_z
        D = b*b - 4*a*c
        if D < 0:
            return []
        else:
            t_min, t_max = segment.get_u_bounds()
            t1 = (-b + np.sqrt(D))/(2*a)
            t2 = (-b - np.sqrt(D))/(2*a)
            return [t for t in [t1,t2] if t_min <= t <= t_max]

    def real_cbrt(x):
        if x.real < 0 and abs(x.imag) < 1e-10:
            return - (-x.real)**(1.0/3.0) + 0j
        else:
            return x ** (1.0/3.0)

    def solve_cubic(segment):
        t_min, t_max = segment.get_u_bounds()
        coeffs = get_taylor_coeffs(segment)
        d,c,b,a = coeffs
        d += delta_z
        p = (3*a*c - b*b) / (3*a*a)
        q = (2*b**3 - 9*a*b*c + 27*a*a*d)/(27*a**3)
        Q = (p/3)**3 + (q/2)**2
        sqrt_Q = np.sqrt(Q, dtype=complex)
        alpha = real_cbrt(-q/2 + sqrt_Q)
        beta = real_cbrt(-q/2 - sqrt_Q)
        #print(f"Cubic coeffs: {[a,b,c,d]} => p {p}, q {q}, Q {Q}, alpha {alpha}, beta {beta}")
        sqrt32 = np.sqrt(3.0)/2.0
        y1 = alpha + beta
        y2 = -(alpha + beta)/2.0 + (alpha - beta)*sqrt32*1j
        y3 = -(alpha + beta)/2.0 - (alpha - beta)*sqrt32*1j
        #print(f"Solve cubic: ys {[y1, y2, y3]}")
        ys = [y.real for y in [y1,y2,y3] if abs(y.imag) < 1e-6]
        #print(f"Solve cubic: real ys {ys}")
        xs = [y - b/(3*a) for y in ys]
        #print(t_min, t_max, xs)
        solutions = [t for t in xs if t_min <= t <= t_max]
        #print(f"Solve cubic: {xs}, range ({t_min} - {t_max})")
        return solutions

    def solve(segment, i=0):
        if is_small(segment):
            cpts = segment.get_control_points()
            p1, p2 = cpts[0], cpts[-1]
            p = 0.5*(p1 + p2)
            u = middle(segment)
            #print(f"I: small segment: {u} - {p}")
            return [u]
        elif not is_rational and (segment.get_degree() == 1 or segment.is_line(tolerance)):
            r = intersect_line(segment)
            if r is None:
                return []
            else:
                #print(f"I: linear: {r}")
                return [r]
        elif not is_rational and segment.get_degree() == 2:
            return solve_quadric(segment)
        elif not is_rational and segment.get_degree() == 3:
            return solve_cubic(segment)
        else:
            if i > maxiter:
                raise Exception("Maximum number of subdivision iterations reached")
            s1, s2 = split(segment)
            return solve(s1, i+1) + solve(s2, i+1)

    if is_rational:
        segments = cut_to_segments(curve)
    else:
        segments = curve.to_bezier_segments(to_bezier_class=False)

    segments = [segment for segment in segments if check_signs(segment)]
    solutions = [solve(segment) for segment in segments]
    #print(f"Intersect: segments {[s.get_control_points()[0] for s in segments]}")
    solutions = sum(solutions, [])
    ts = np.array(solutions)
    pts = curve.evaluate_array(ts)
    return list(zip(ts, pts))


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

def curve_extremes(curve, field, samples=10, direction = 'MAX', on_fail = 'FAIL', logger=None):
    if logger is None:
        logger = get_logger()

    def goal(t):
        p = curve.evaluate(t)
        v = field.evaluate(p[0], p[1], p[2])
        if direction == 'MAX':
            return -v
        else:
            return v

    t_min, t_max = curve.get_u_bounds()
    tknots = np.linspace(t_min, t_max, num=samples+1)

    res_ts = []
    res_vs = []

    for t1, t2 in zip(tknots, tknots[1:]):
        guess = (t1+t2)/2.0
        result = minimize_scalar(goal,
                    bounds = (t1, t2),
                    bracket = (t1, t2),
                    method = 'Bounded')
        if result.success:
            if t_min <= result.x <= t_max:
                t = result.x
                v = result.fun
                res_vs.append(v)
                res_ts.append(t)
            else:
                logger.info("Found T: %s, but it is outside of %s - %s", result.x, t_min, t_max)
        else:
            if on_fail == 'FAIL':
                raise Exception(f"Can't find the extreme point for {curve} on {t1} - {t2}: {result.message}")

    if len(res_ts) == 0:
        if on_fail == 'FAIL':
            raise Exception(f"Can't find the extreme point for {curve}: no candidate points")
        else:
            return []
    else:
        target_v = min(res_vs)
        res_ts = [t for t,v in zip(res_ts, res_vs) if v == target_v]
        return res_ts

def intersect_line_iso_surface(field, pt1, direction, max_distance, iso_value, sections=10, first_only=True, on_fail=FAIL):

    pt1 = np.array(pt1)
    direction = np.array(direction)
    direction /= np.linalg.norm(direction)
    pt2 = pt1 + max_distance * direction
    ts = np.linspace(0, max_distance, num=sections)
    pts = pt1 + ts[np.newaxis].T * direction
    values = field.evaluate_grid(pts[:,0], pts[:,1], pts[:,2]) - iso_value

    def goal(t):
        p = pt1 + t*direction
        v = field.evaluate(p[0], p[1], p[2])
        return v - iso_value

    ranges = []
    for i, (v1,v2) in enumerate(zip(values, values[1:])):
        if v1*v2 < 0:
            ranges.append(i)
    if len(ranges) == 0:
        if on_fail == FAIL:
            raise Exception(f"Ray {pt1} + {direction} does not intersect iso surface with iso_value={iso_value}")
        elif on_fail == RETURN_NONE:
            return None
        else:
            raise Exception("unsupported on_fail variant")
    if first_only:
        ranges = ranges[:1]

    result_ts = []
    result_pts = []
    for i in ranges:
        sol = root_scalar(goal, method='ridder',
                          x0 = ts[i],
                          bracket = (ts[i], ts[i+1])
                        )
        t = sol.root
        p = pt1 + t*direction
        result_ts.append(t)
        result_pts.append(tuple(p))
    return result_ts, result_pts


