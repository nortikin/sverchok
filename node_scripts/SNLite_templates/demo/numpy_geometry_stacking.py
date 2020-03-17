"""
in p1 s d=0.3 n=2
in p2 s d=0.7 n=2
in vdivs s d=20 n=2
in points s d=200 n=2
out verts_out v
"""

from numpy import vstack, arange, cos, sin, pi, tile

r2 = 20 * p1
r1 = 10 * p2
theta = 1 / points
vtheta = 1 / vdivs
theta_2_PI = 2 * pi * theta

V = arange(vdivs)
I = arange(points)
T = theta_2_PI * I

Tx = tile(T, V.size)
Vx = V.repeat(T.size)
P = pi * ((vtheta * Vx) - 0.5)

X = (r1 * cos(Tx) * cos(P)) + (r2 * cos(Tx))
Y = (r1 * sin(Tx) * cos(P)) + (r2 * sin(Tx))
Z = r1 * sin(P)

v_points = vstack([X, Y, Z]).T.tolist()
verts_out.append(v_points)
