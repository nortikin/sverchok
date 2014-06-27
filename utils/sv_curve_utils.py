import bpy
import mathutils
from mathutils import Vector
from mathutils.geometry import interpolate_bezier


def get_points(spline, clean=True):
    '''
    usage:
    spline = bpy.data.curves[0].splines[0]
    points = get_points(spline)
    '''

    knots = spline.bezier_points
    if len(knots) < 2:
        return

    # verts per segment
    r = spline.resolution_u + 1

    # segments in spline
    segments = len(knots)

    if not spline.use_cyclic_u:
        segments -= 1

    master_point_list = []
    for i in range(segments):
        inext = (i + 1) % len(knots)

        knot1 = knots[i].co
        handle1 = knots[i].handle_right
        handle2 = knots[inext].handle_left
        knot2 = knots[inext].co

        bezier = knot1, handle1, handle2, knot2, r
        points = interpolate_bezier(*bezier)
        master_point_list.extend(points)

    # some clean up to remove consecutive doubles, this could be smarter...
    if clean:
        old = master_point_list
        good = [v for i, v in enumerate(old[:-1]) if not old[i] == old[i + 1]]
        good.append(old[-1])
        return good

    # makes edge keys, ensure cyclic
    Edges = [[i, i + 1] for i in range(n_verts - 1)]
    if spline.use_cyclic_u:
        Edges.append([i, 0])

    return master_point_list, Edges
