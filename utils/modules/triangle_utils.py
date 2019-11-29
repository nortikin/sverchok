# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import sin, cos, pi, tan, atan2, sqrt, asin

def triang_A_c_Alpha_Beta(A, c, alpha, beta):
    # https://math.stackexchange.com/a/1081735
    c = c
    beta = beta
    j = -tan(beta) * c / (-tan(alpha) - tan(beta))
    k = tan(alpha) * j
    return [A, [c + A[0], A[1], A[2]], [j + A[0], k + A[1], A[2]]]

def triang_A_B_Alpha_Beta(A, B, alpha, beta):
    # https://math.stackexchange.com/a/145299
    ang = atan2(B[1] - A[1], B[0] - A[0])
    alpha = alpha + ang
    beta = 2 * pi - beta + ang
    x = (tan(alpha) * A[0] - tan(beta) * B[0] + B[1] - A[1]) / (tan(alpha) - tan(beta))
    y = tan(alpha) * x + A[1] - tan(alpha) * A[0]
    return [A, B, [x, y, 0]]

def triang_A_B_b_Alpha(A, B, b, alpha):
    # B =[A[0] + a, A[1], A[2]]
    ang = atan2(B[1] - A[1], B[0] - A[0])
    C = [A[0] + b*cos(alpha + ang), A[1]+ b*sin(alpha + ang), A[2]]
    return [A, B, C]

def triang_A_b_c_Alpha(A, b, c, alpha):
    B = [A[0] + c, A[1], A[2]]
    C = [A[0] + b *cos(alpha), A[1]+ b * sin(alpha), A[2]]
    return [A, B, C]

def triang_A_a_b_c(A, a, b, c):
    B = [A[0] + c, A[1], A[2]]
    return triang_A_B_a_b(A, B, a, b)

def triang_A_B_a_b(A, B, a, b):
    '''Two verts and the length of the other two sides'''
    # Adapted from circle interections function in Contour2D node
    ang_base = atan2(B[1] - A[1], B[0] - A[0])
    dist = sqrt((B[0] - A[0]) * (B[0] - A[0]) + (B[1] - A[1]) * (B[1] - A[1]))
    mask = (a + b) > dist
    mask *= abs(a - b) < dist
    mask *= dist > 0
    if mask:
        k = a * a - b * b + dist * dist
        k /= 2 * dist
        h = sqrt(a * a - k * k)
        ang_local = asin(h / a)
        ang_f = ang_base - ang_local - pi
        x = B[0] + a * cos(ang_f)
        y = B[1] + a * sin(ang_f)
    else:
        x = A[0] + (B[0] - A[0]) * a/b
        y = A[1] + (B[1] - A[1]) * a/b

    return [A, B, [x, y, A[2]]]
