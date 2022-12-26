# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import math
import numpy as np

from mathutils import Vector

from sverchok.data_structure import repeat_last_for_length
from sverchok.utils.fillet import calc_fillet
from sverchok.utils.curve.primitives import SvLine
from sverchok.utils.curve.biarc import SvBiArc
from sverchok.utils.curve.algorithms import concatenate_curves
from sverchok.utils.curve.bezier import SvCubicBezierCurve, SvBezierCurve

FILLET_ARC = 'ARC'
FILLET_BEZIER = 'BEZIER2'
FILLET_BEVEL = 'BEVEL'

SMOOTH_POSITION = '0'
SMOOTH_TANGENT = '1'
SMOOTH_BIARC = '1b'
SMOOTH_ARC = '1a'
SMOOTH_QUAD = '1q'
SMOOTH_NORMAL = '2'
SMOOTH_CURVATURE = '3'
SMOOTH_G2 = 'G2'

def calc_single_fillet(smooth, curve1, curve2, k1, k2, bulge_factor = 0.5, biarc_parameter = 1.0, planar_tolerance = 1e-6):
    u1_max = curve1.get_u_bounds()[1]
    u2_min = curve2.get_u_bounds()[0]
    curve1_end = curve1.evaluate(u1_max)
    curve2_begin = curve2.evaluate(u2_min)
    tangent1_end = k1 * curve1.get_end_tangent()
    tangent2_begin = k2 * curve2.get_start_tangent()

    if smooth == SMOOTH_POSITION:
        return SvLine.from_two_points(curve1_end, curve2_begin)
    elif smooth == SMOOTH_TANGENT:
        tangent1 = tangent1_end # / np.linalg.norm(tangent1_end)
        tangent2 = tangent2_begin # / np.linalg.norm(tangent2_begin)
        tangent1 = bulge_factor * tangent1
        tangent2 = bulge_factor * tangent2
        return SvCubicBezierCurve(
                    curve1_end,
                    curve1_end + tangent1 / 3.0,
                    curve2_begin - tangent2 / 3.0,
                    curve2_begin
                )
    elif smooth == SMOOTH_BIARC:
        return SvBiArc.calc(
                curve1_end, curve2_begin,
                tangent1_end, tangent2_begin,
                biarc_parameter,
                planar_tolerance = planar_tolerance)
    elif smooth == SMOOTH_NORMAL:
        second_1_end = k1**2 * curve1.second_derivative(u1_max)
        second_2_begin = k2**2 * curve2.second_derivative(u2_min)
        return SvBezierCurve.blend_second_derivatives(
                        curve1_end, tangent1_end, second_1_end,
                        curve2_begin, tangent2_begin, second_2_begin)
    elif smooth == SMOOTH_CURVATURE:
        second_1_end = k1**2 * curve1.second_derivative(u1_max)
        second_2_begin = k2**2 * curve2.second_derivative(u2_min)
        third_1_end = k1**3 * curve1.third_derivative_array(np.array([u1_max]))[0]
        third_2_begin = k2**3 * curve2.third_derivative_array(np.array([u2_min]))[0]

        return SvBezierCurve.blend_third_derivatives(
                        curve1_end, tangent1_end, second_1_end, third_1_end,
                        curve2_begin, tangent2_begin, second_2_begin, third_2_begin)
    elif smooth == 'G2':
        normal_1_end = curve1.main_normal(u1_max)
        normal_2_begin = curve2.main_normal(u2_min)
        curvature_1_end = curve1.curvature(u1_max)
        curvature_2_begin = curve2.curvature(u2_min)
        
        return SvBezierCurve.from_tangents_normals_curvatures(
                        curve1_end, curve2_begin,
                        tangent1_end, tangent2_begin,
                        normal_1_end, normal_2_begin,
                        curvature_1_end, curvature_2_begin)
    else:
        raise Exception(f"Unsupported smooth level: {smooth}")

def cut_ends(curve, cut_offset, cut_start=True, cut_end=True):
    u_min, u_max = curve.get_u_bounds()
    p1, p2 = curve.get_end_points()
    l = np.linalg.norm(p1 - p2)
    dt = cut_offset * (u_max - u_min)
    if cut_start:
        u1 = u_min + dt
    else:
        u1 = u_min
    if cut_end:
        u2 = u_max - dt
    else:
        u2 = u_max
    du = u2 - u1
    #print(f"cut: {u_min} - {u_max} * cut_offset => {u1} - {u2}")
    return du, curve.cut_segment(u1, u2)

def limit_filet_radiuses(vertices, radiuses, cyclic=False):
    factor = 0.999
    if cyclic:
        vertices = [vertices[-1]] + vertices + [vertices[0]]
    vertices = [Vector(v) for v in vertices]
    limit_radiuses = []
    for n in range(len(vertices)-2):
        v1,v2,v3,r = vertices[n],vertices[n+1],vertices[n+2],radiuses[n]
        vector1,vector2 = v1-v2,v3-v2
        d1,d2 = vector1.length,vector2.length
        min_length1 = d1 if d1<d2 else d2

        v_2,v_3,v_4 = v2,v3, v3 if v3 is vertices[-1] else vertices[n+3]
        vector_1 ,vector_2 = vector2*-1,v_4-v_3
        d_1,d_2 = d2 , vector_2.length
        min_length2 = d_1 if d_1<d_2 else d_2

        if d2 - min_length1 >= min_length2 :
            if cyclic and n==0:
                min_length1 = min_length1/2
                vertices[-1] = (v1+v2)/2

            angle = vector1.angle(vector2,0)
            max_r = math.tan(angle/2)*min_length1
        else:
            vec2 = vector2.copy()
            vec2.normalize()
            vec_1 = vector_1.copy()
            vec_1.normalize()
            f_vector1 = vec2*min_length1
            f_vector2 = vec_1*(d2-min_length2)

            mid_vector = (f_vector1 + -f_vector2)/2
            mid_vertex = v2 + mid_vector
            vertices[n+1] = mid_vertex
            min_length = mid_vector.length

            if cyclic and n==0:
                vertices[-1] = v2 + vector1*(min_length/d1)
            
            angle = vector1.angle(vector2,0)
            max_r = math.tan(angle/2)*min_length
        r = max_r*factor if r>max_r else r
        limit_radiuses.append(r)
    return limit_radiuses

def fillet_nurbs_curve(curve, smooth, cut_offset,
        bulge_factor = 0.5,
        biarc_parameter = 1.0,
        planar_tolerance = 1e-6,
        tangent_tolerance = 1e-6):

    cyclic = curve.is_closed()
    segments = curve.split_at_fracture_points(tangent_tolerance = tangent_tolerance)
    n = len(segments)
    cuts = [cut_ends(s, cut_offset, cut_start = (i > 0 or cyclic), cut_end = (i < n-1 or cyclic)) for i, s in enumerate(segments)]
    fillets = [calc_single_fillet(smooth, s1, s2, dt1, dt2, bulge_factor, biarc_parameter, planar_tolerance) for (dt1,s1), (dt2,s2) in zip(cuts, cuts[1:])]
    if cyclic:
        dt1, s1 = cuts[-1]
        dt2, s2 = cuts[0]
        fillet = calc_single_fillet(smooth, s1, s2, dt1, dt2, bulge_factor, biarc_parameter, planar_tolerance)
        fillets.append(fillet)
    segments = [cut[1] for cut in cuts]
    new_segments = [[segment, fillet] for segment, fillet in zip(segments, fillets)]
    if not cyclic:
        new_segments.append([segments[-1]])
    new_segments = sum(new_segments, [])
    return concatenate_curves(new_segments)

def fillet_polyline_from_vertices(vertices, radiuses,
            cyclic=False,
            concat=True,
            clamp=True,
            arc_mode = FILLET_ARC,
            scale_to_unit=False,
            make_nurbs=True):

    if len(radiuses) != len(vertices):
        raise Exception(f"Number of radiuses provided ({len(radiuses)}) must be equal to number of vertices ({len(vertices)})")

    if clamp:
        radiuses = limit_filet_radiuses(vertices, radiuses, cyclic=cyclic)

    if cyclic:
        if radiuses[-1] == 0 :
            last_fillet = None
        else:
            last_fillet = calc_fillet(vertices[-2], vertices[-1], vertices[0], radiuses[-1])
        vertices = [vertices[-1]] + vertices + [vertices[0]] 
        prev_edge_start = vertices[0] if last_fillet is None else last_fillet.p2
        corners = list(zip(vertices, vertices[1:], vertices[2:], radiuses))
    else:
        prev_edge_start = vertices[0]
        corners = zip(vertices, vertices[1:], vertices[2:], radiuses)

    curves = []
    centers = []
    for v1, v2, v3, radius in corners:
        if radius == 0 :
            fillet = None
        else:
            fillet = calc_fillet(v1, v2, v3, radius)
        if fillet is not None :
            edge_direction = np.array(fillet.p1) - np.array(prev_edge_start)
            edge_len = np.linalg.norm(edge_direction)
            if edge_len != 0 :
                edge = SvLine(prev_edge_start, edge_direction / edge_len)
                edge.u_bounds = (0.0, edge_len)
                curves.append(edge)
            if arc_mode == FILLET_ARC:
                arc = fillet.get_circular_arc()
            elif arc_mode == FILLET_BEZIER:
                arc = fillet.get_bezier_arc()
            elif arc_mode == FILLET_BEVEL:
                arc = fillet.get_bevel()
            else:
                raise Exception(f"Unsupported arc mode: {arc_mode}")
            prev_edge_start = fillet.p2
            curves.append(arc)
            centers.append(fillet.matrix)
        else:
            edge = SvLine.from_two_points(prev_edge_start, v2)
            prev_edge_start = v2
            curves.append(edge)

    if not cyclic:
        edge_direction = np.array(vertices[-1]) - np.array(prev_edge_start)
        edge_len = np.linalg.norm(edge_direction)
        if edge_len != 0 :
            edge = SvLine(prev_edge_start, edge_direction / edge_len)
            edge.u_bounds = (0.0, edge_len)
            curves.append(edge)

    if make_nurbs:
        if concat:
            curves = [curve.to_nurbs().elevate_degree(target=2) for curve in curves]
        else:
            curves = [curve.to_nurbs() for curve in curves]
    if concat:
        concat = concatenate_curves(curves, scale_to_unit = scale_to_unit)
        return concat, centers, radiuses
    else:
        return curves, centers, radiuses

def fillet_polyline_from_curve(curve, radiuses,
            smooth = SMOOTH_ARC,
            concat = True,
            clamp = True,
            scale_to_unit = False,
            make_nurbs = True):

    if not curve.is_polyline():
        raise Exception("Curve is not a polyline")
    vertices = curve.get_polyline_vertices().tolist()
    cyclic = curve.is_closed()

    if isinstance(radiuses, (int,float)):
        radiuses = [radiuses]
    if cyclic:
        vertices = vertices[:-1]
    n = len(vertices)
    radiuses = repeat_last_for_length(radiuses, n)

    if smooth == SMOOTH_POSITION:
        arc_mode = FILLET_BEVEL
    elif smooth == SMOOTH_TANGENT:
        arc_mode = FILLET_BEZIER
    elif smooth == SMOOTH_ARC:
        arc_mode = FILLET_ARC
    elif smooth == SMOOTH_QUAD:
        arc_mode = FILLET_BEZIER
    else:
        raise Exception(f"Unsupported smooth level: {smooth}")

    return fillet_polyline_from_vertices(vertices, radiuses,
                cyclic = cyclic,
                concat = concat,
                clamp = clamp,
                arc_mode = arc_mode,
                scale_to_unit = scale_to_unit,
                make_nurbs = make_nurbs)

