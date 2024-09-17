# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from mathutils import Vector, Matrix
from sverchok.utils.geom import linear_approximation, CircleEquation3D, is_convex_2d
from sverchok.utils.math import np_multiply_matrices_vectors, np_dot
from sverchok.dependencies import scipy
if scipy is not None:
    from scipy.optimize import linprog

RETURN_NONE = 'RETURN_NONE'
ERROR = 'ERROR'
ASIS = 'ASIS'

def calc_inscribed_circle(verts, on_concave=ERROR):
    """
    Calculate the biggest circle which can be inscribed into a polygon
    (i.e. a circle which is inside the polygon, and touches some of polygon's edges).

    Only convex polygons are supported.

    Requires scipy.

    Theory:
    If each edge of polygon (in 2D XOY plane) is represented by a unit vector (a, b),
    which starts at polygon's vertex, then distance from this edge to arbitrary point (x,y)
    inside polygon can be calculated as

    rho(edge, (x,y)) = a x + b y - d

    where d = a x0 + b y0, and (x0, y0) are coordinates of corresponding polygon vertex.

    Based on this formula, it is possible to state a linear programming problem. We
    search for a point (x, y, Z), which satisfies constraints

    Z <= rho(edge_i, (x,y)) for i in 1 .. N,

    i.e.

    Z <= a_i x + b_i y - d_i

    or

    -a_i x -b_i y + Z <= -d_i

    with additional conditions:

    x >= 0, y >= 0, Z >= 0

    and provides maximum for the goal function F(x, y, Z) = Z.
    x and y will give us coordinates of circle's center.

    Also refer to: https://arxiv.org/pdf/1212.3193 .

    Arguments:
    * verts - np.array (or list) of shape (n, 3), representing vertices of the polygon.

    Returns: an instance of CircleEquation3D.
    """
    n = len(verts)
    verts = np.array(verts)

    e1 = verts[1] - verts[0]
    e2 = verts[2] - verts[1]
    n1 = np.cross(e1, e2)

    approx = linear_approximation(verts)
    plane = approx.most_similar_plane()
    plane_matrix = plane.get_matrix()

    # Flip plane matrix, in case approximation gave us a plane
    # with normal pointing in direction opposite to polygon normal.
    plane_normal = np.array(plane.normal)
    if np.dot(n1, plane_normal) < 0:
        plane_matrix = Matrix.Diagonal(Vector([-1,-1,-1])) @ plane_matrix
        verts = verts[::-1]
        plane_normal = - plane_normal

    # Project all vertices to 2D space
    inv = np.linalg.inv(plane_matrix.to_3x3())
    pt0 = np.array(approx.center)
    verts2d = np_multiply_matrices_vectors(inv, verts - pt0)

    if on_concave != ASIS:
        if not is_convex_2d(verts2d):
            if on_concave == ERROR:
                raise Exception("Polygon is not convex")
            else:
                return None

    # we will need only 2 coordinates
    verts2d = verts2d[:,0:2]
    # linprog method automatically assumes that all variables are non-negative.
    # So move all vertices to first quadrant.
    origin = verts2d.min(axis=0)
    verts2d -= origin[:2]

    edges2d = np.roll(verts2d, -1, axis=0) - verts2d # (n, 2)
    edges2d_normalized = edges2d / np.linalg.norm(edges2d, axis=1, keepdims=True)

    # edges line equations matrix
    edges_eq = np.zeros((n+1, 3))
    edges_eq[:n,0] = edges2d_normalized[:,1]
    edges_eq[:n,1] = -edges2d_normalized[:,0]
    edges_eq[:n,2] = 1
    edges_eq[n,:] = np.array([0, 0, -1]) # -Z <= 0

    # right-hand side of edges line equations
    D = np_dot(-edges_eq[:n,:2], verts2d)
    D = np.append(D, 0)

    # function to be minimized: it's -Z (we need to maximize Z).
    c = np.array([0.0, 0.0, -1.0])

    res = linprog(c, A_ub = edges_eq, b_ub = -D, method='highs')
    center2d = res.x
    if center2d is None:
        return None
    center2d[2] = 0

    distances = np_dot(-edges_eq[:n,:2], center2d[:2]) - D[:n]
    rho = abs(distances).min()
    o = np.zeros((3,))
    o[:2] = origin
    # Return to 3D space
    center = plane_matrix @ (Vector(center2d) + Vector(o)) + Vector(pt0)
    return CircleEquation3D.from_center_radius_normal(center, rho, plane_normal)

