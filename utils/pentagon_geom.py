# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import sin, cos, tan, pi, atan2, sqrt

from sverchok.utils.modules.polygon_utils import pols_to_edges
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.sv_bmesh_utils import remove_doubles
class SvPentagon_1_1:

    input_sockets = "ABabcd"

    @staticmethod
    def layout(cols, rows, numy):
        tile_rotated = 0
        offset_x = [l  for l in range(numy)]
        offset_y = [l  for l in range(cols)]
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = c * sin(A)
        dx = a + d - b * cos(B) + a - d - c * cos(A)
        off_base_y = b * sin(B) - dy
        off_base_x = -a + d + c * cos(A)
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        Cp = (a + c * cos(pi - A), c * sin(pi - A))
        if a < d:
            tile_verts = [
                [0, 0, 0],
                [a, 0, 0],
                [Cp[0], Cp[1], 0],
                [Cp[0] - d + a, Cp[1], 0],
                [Cp[0] -d, Cp[1], 0],
                [b * cos(B), b * sin(B), 0],
                [d, 0, 0],
                [a + d, 0, 0],
                [Cp[0] + a + b * cos(B - pi), Cp[1] + b * sin(B - pi), 0],
                [Cp[0] + a, Cp[1], 0]
                ]
            tile_pols = [
                [0, 1, 2, 3, 4, 5],
                [1, 6, 7, 8, 9, 2]
                ]
        else:
            tile_verts = [
                [0, 0, 0],
                [d, 0, 0],
                [a, 0, 0],
                [Cp[0], Cp[1], 0],
                [Cp[0] - d, Cp[1], 0],
                [b * cos(B), b * sin(B), 0],
                [a + d, 0, 0],
                [Cp[0] + a + b * cos(B - pi), Cp[1] + b * sin(B - pi), 0],
                [Cp[0] + a, Cp[1], 0],
                [Cp[0] - d + a, Cp[1], 0]
                ]
            tile_pols = [
                [0, 1, 2, 3, 4, 5],
                [2, 6, 7, 8, 9, 3]
                ]
        return tile_verts, tile_pols


class SvPentagon_1_2:

    input_sockets = "ABab"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [2*l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = b*sin(A)
        dx = 2*(2 * a + (dy/2) / tan(B/2))
        off_base_y = 0
        off_base_x = 0
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        h = b*sin(A)
        Cp = (a, h, 0)
        B1p = (-b*cos(A)/2, h,0)
        B1ph = (b*cos(A)/2, h,0)
        B2p = (b*cos(A)/2, 0,0)
        B2ph = (-b*cos(A)/2, 0,0)
        Dp = (Cp[0] + (h/2) / tan(B/2), Cp[1] - h/2)
        tile_verts = [
            B1p, B1ph, B2p, B2ph,
            [Cp[0], Cp[1], 0],
            [Dp[0], Dp[1], 0],
            [Cp[0], Cp[1] - h, 0],

            [-Cp[0], Cp[1], 0],
            [-Dp[0], Dp[1], 0],
            [-Cp[0], Cp[1] - h, 0],
            ]
        dy = b*sin(A)
        dx = 2 * a + (dy/2) / tan(B/2)
        off_base_y = dy/2

        t_d = [[v[0]+ dx, v[1]+off_base_y, [2]] for v in tile_verts]
        tile_verts += t_d
        tile_pols_a = [[2, 6, 5, 4, 1, 0], [7, 8, 9, 3, 2, 0]]
        tile_pols_b = [[2, 3, 6, 5, 4, 0], [1, 7, 8, 9, 2, 0]]
        if cos(A) > 0:
            tile_pols = tile_pols_a + [[c+10 for c in p] for p in tile_pols_a]

            tile_pols = tile_pols_a + [[13, 16, 15, 14, 10, 11], [11, 17, 18, 19, 12, 13]]

        else:
            tile_pols = tile_pols_b + [[c+10 for c in p] for p in tile_pols_a]
            tile_pols = tile_pols_b + [[13, 16, 15, 14, 10, 11], [11, 17, 18, 19, 12, 13]]
        return tile_verts, tile_pols

class SvPentagon_1_3:

    input_sockets = "ABabc"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = b
        dx = 2 * a * cos(A - pi/2) + c * cos(B + A -3*pi/2)
        off_base_y = -b + 2 * a * sin(A - pi/2) - c * sin(-B - A -pi/2)
        off_base_x = 0
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        Ep = (a * cos(pi/2 - A), a * sin(pi/2 - A))
        Dp = (Ep[0] + c * cos(-B - A - pi/2), Ep[1] + c*sin(-B - A - pi/2))
        tile_verts = [
            [0, 0, 0],
            [0, b, 0],
            [Ep[0], Ep[1] + b, 0],
            [Dp[0], Dp[1], 0],
            [Ep[0], Ep[1], 0],

            [-Ep[0], Ep[1] + b, 0],
            [-Dp[0], Dp[1], 0],
            [-Ep[0], Ep[1], 0],
            ]
        tile_pols = [
            [4, 3, 2, 1, 0],
            [0, 1, 5, 6, 7]
            ]

        return tile_verts, tile_pols


class SvPentagon_1_4:

    input_sockets = "ABab"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = b
        dx = 2 * a * cos(A - pi/2) + (b/2) / tan(B/2)
        off_base_y = b/2
        off_base_x = 0
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        Cp = (a * cos(pi/2 - A), b + a * sin(pi/2 - A))
        Dp = (Cp[0] + (b/2) / tan(B/2), Cp[1] - b/2)
        tile_verts = [
            [0, 0, 0],
            [0, b, 0],
            [Cp[0], Cp[1], 0],
            [Dp[0], Dp[1], 0],
            [Cp[0], Cp[1] - b, 0],

            [-Cp[0], Cp[1], 0],
            [-Dp[0], Dp[1], 0],
            [-Cp[0], Cp[1] - b, 0],
            ]
        tile_pols = [
            [4, 3, 2, 1, 0],
            [0, 1, 5, 6, 7]
            ]

        return tile_verts, tile_pols


class SvPentagon_2:

    input_sockets = "ABabc"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = c*sin(pi-B) +a * sin(-B - A) +c* sin(pi-A)
        dx = 0*(a+b)/2 +c*cos(pi-B) -b * cos(-B - A) +c*cos(-A) +0*(a+b)/2 +b
        off_base_y = -(c*sin(pi-B) -b * sin(-B - A) -c* sin(pi-A))
        off_base_x = -((a+b)/2 + c*cos(pi-B) +a * cos(-B - A) +c*cos(pi-A)-(a+b)/2 +a)

        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data

        A1p = [-(a+b)/2, 0, 0]
        A2p = [(a+b)/2, 0, 0]
        Bp = [-(a+b)/2 + a, 0, 0]
        B2p = [(a+b)/2 - a, 0, 0]
        Cp = [Bp[0] + c * cos(pi-A), Bp[1] + c * sin(pi- A), 0]
        B3p = [Cp[0] + b * cos(-B-A), Cp[1]+ b* sin(-B-A), 0]
        B31p = [Cp[0]+a*cos(-B-A),Cp[1]+a*sin(-B-A), 0]
        Ep = [B3p[0] + c * cos(-B), B3p[1] + c*sin(-B), 0]
        B4p = [A2p[0] + c * cos(pi-B), A2p[1] + c * sin(pi-B) , 0]
        A31p = [B4p[0] + (a-b) * cos(-B - A), B4p[1] + (a-b) * sin(-B - A) , 0]
        A3p = [B4p[0] + a * cos(-B - A),B4p[1] + a * sin(-B - A) , 0]
        C3p = [B2p[0] + c * cos(-A), B2p[1] + c * sin(-A) , 0]
        D1p = [C3p[0] + a * cos(-A - B + pi), C3p[1] + a * sin(-A - B + pi) , 0]
        Dp = [C3p[0] + b * cos(-A - B + pi), C3p[1] + b * sin( -A -B + pi) , 0]
        E2p = [Dp[0] + c * cos(- B - pi), Dp[1] + c * sin(-B-pi) , 0]
        B5p = [A1p[0] + c * cos(-B), A1p[1] + c * sin(-B) , 0]
        A41p = [B5p[0] + (a-b) * cos(-B -A + pi), B5p[1] + (a-b) * sin(-B -A + pi) , 0]
        A4p = [B5p[0] + a * cos(-B -A + pi), B5p[1] + a * sin(-B -A + pi) , 0]


        if a > b:
            tile_verts = [A1p, A2p,  Bp, B2p, Cp, B3p, Ep, B4p, A31p, A3p, C3p, Dp, E2p, B5p, A41p, A4p]
            tile_pols = [[0, 3, 2, 4, 5, 6], [2, 1, 7, 8, 9, 4], [3, 10, 11, 12, 1, 2], [0, 3, 10, 15, 14, 13]]
        else:
            tile_verts = [A1p, A2p,  Bp, B2p, Cp, B31p, B3p, Ep, B4p, A3p, C3p, D1p, Dp, E2p, B5p, A4p]
            tile_pols = [[0, 2, 4, 5, 6,7], [2, 3, 1, 8, 9, 4], [3, 10, 11, 12, 13, 1], [0, 2, 3, 10, 15, 14]]


        return tile_verts, tile_pols


class SvPentagon_3:

    input_sockets = "Aa"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = 2*a*sin(A)
        dx = a*sin(A)/sin(pi/3) * 3 / 2
        off_base_y = dy/2
        off_base_x = 0
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        rad_s = a*sin(A)
        rad_g = rad_s/sin(pi/3)

        tile_verts = [[0, 0, 0]]
        tile_pols = [[0, 11, 1, 10, 2, 7], [0, 7, 3, 12, 4, 9], [0, 9, 5, 8, 6, 11]]
        for i in range(6):
            ang = i*pi/3
            tile_verts.append([rad_g*cos(ang), rad_g*sin(ang), 0])
        for i in range(3):
            ang = i*2*pi/3
            tile_verts.append([a*cos(A+ang), a*sin(A + ang), 0])
            tile_verts.append([a*cos(-A+ang), a*sin(-A + ang), 0])

        return tile_verts, tile_pols


class SvPentagon_4:
    input_sockets = "Aab"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        dy = a + b * sin(- A - pi) + b * sin(-pi/2 - A)
        dx = a + b * cos(-A + pi/2) + b * cos(-A - pi)
        off_base_y = a - b * sin(-A + pi/2) - b * sin(-A - pi)
        off_base_x = -a - b * cos(- A -pi) - b * cos(-pi/2 - A)
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        Ap = (a, 0)
        Cp = (0, -a)
        Dp = (Cp[0] + b * cos(-A + pi/2), Cp[1] + b * sin(-A + pi/2))
        Ep = (Dp[0] + b * cos(-A + pi), Dp[1] + b * sin(-A + pi))
        B2p = (Ap[0] + b * cos(-A - pi), Ap[1] + b * sin(-A - pi))
        C3p = (-a, 0, 0)
        B3p = (C3p[0] + b * cos(-A), C3p[1] + b * sin(-A))
        D4p = (b * cos(-A - pi/2), a + b * sin(-A - pi/2), 0)
        tile_verts = [
            [0, 0, 0],
            [a, 0, 0],
            [Ep[0], Ep[1], 0],
            [Dp[0], Dp[1], 0],
            [0, -a, 0],

            [B2p[0], B2p[1], 0],
            [B2p[0] + D4p[0], B2p[1]+ b * sin(-A - pi/2), 0],
            [0, a, 0],

            [C3p[0], C3p[1], 0],
            [B3p[0], B3p[1], 0],
            [B3p[0] + b * cos(pi/2 - A), B3p[1]+ b * sin(pi/2 - A), 0],

            [D4p[0], D4p[1], 0],
            [D4p[0] + b * cos(-A), D4p[1] + b * sin(-A), 0]
            ]
        tile_pols = [
            [4, 3, 2, 1, 0],
            [0, 1, 5, 6, 7],
            [8, 9, 10, 4, 0],
            [7, 11, 12, 8, 0]]

        return tile_verts, tile_pols


class SvPentagon_5:

    input_sockets = "Aab"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        A, B = angles
        a, b = sides_data[:2]
        dy = 2*a  * sin(pi/3) + b * sin(A + 5*pi/3) + b * sin(A + 4*pi/3)
        dx = (a * cos(pi/3) + b * cos(A + 4*pi/3) + b * cos(A + pi)) + a
        off_base_y = -(a * sin(pi/3) + b * sin(A + 4*pi/3) + b *sin(A + pi))
        off_base_x = -b * cos(A + 5*pi/3) - b * cos(-A + 2*pi/3)
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        tile_verts = [[0, 0, 0]]
        tile_pols = []
        for i in range(6):
            ang_tt = i*pi/3
            Ap = (a * cos(ang_tt), a * sin(ang_tt))
            Cp = (a * cos(pi/3 + ang_tt), a * sin(pi/3 + ang_tt ))
            ang_temp = pi/3 -pi + ang_tt
            Dp = (Cp[0] + b * cos(A + ang_temp), Cp[1] + b * sin(A + ang_temp))
            ang_temp += A
            Ep = (Dp[0] + b * cos(-pi/3 + ang_temp), Dp[1] + b * sin(-pi/3 + ang_temp))
            tile_verts.append([Cp[0], Cp[1], 0])
            tile_verts.append([Dp[0], Dp[1], 0])
            tile_verts.append([Ep[0], Ep[1], 0])
            tile_pols.append([0,3*i+1, 3*i+2,  3*i+3, (3*i-2+18)%18])

        return tile_verts, tile_pols


class SvPentagon_14:
    input_sockets = "a"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):

        a = sides_data[0]
        s = sqrt(57)
        y1 = (s - 3) / 8 # sin (C/2)
        y2 = (3*s - 17) / 16 # cos C
        x1 = sqrt(6*s - 2) / 8 # cos (C/2)
        x2 = sqrt(102*s - 546) / 16 # sin(C)
        dx = a*(3*x1 + 3*x2)
        dy = 0*(-y1 + 2 + y2) + a*(2 + 6*y1 - y2)
        off_base_y = -(-y1 + 2 + y2)* a
        off_base_x = -(x2)* a
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):
        A, B = angles
        a, b, c, d = sides_data
        s = sqrt(57)
        y1 = (s - 3) / 8 # sin (C/2)
        y2 = (3*s - 17) / 16 # cos C
        x1 = sqrt(6*s - 2) / 8 # cos (C/2)
        x2 = sqrt(102*s - 546) / 16 # sin(C)

        A1 = [          0,      0]
        B1 = [2*x2 +   x1,      0]
        C1 = [2*x2 + 2*x1,    -y1]
        D1 = [2*x2       ,  -3*y1]
        E1 = [          0,     -1]

        C2 = [C1[0], -C1[1]]
        D2 = [D1[0], -D1[1]]
        E2 = [E1[0], -E1[1]]

        X1 = 4*x2 + 3*x1
        A3 = [X1 - A1[0], -y1 + A1[1]]
        C3 = [X1 - C1[0], -y1 + C1[1]]
        D3 = [X1 - D1[0], -y1 + D1[1]]
        E3 = [X1 - E1[0], -y1 + E1[1]]

        D4 = [D3[0], -y1 + D2[1]]
        E4 = [E3[0], -y1 + E2[1]]

        A5 = [D4[0],      D4[1]]


        D5 = [D2[0],      D2[1] + 2]
        E5 = [D5[0] + x2, D5[1] - y2]

        B6 = [A5[0],       A5[1]]
        C6 = [B6[0] + x2,  B6[1] - y2]
        D6 = [C6[0],       C6[1] + 2]
        E6 = [D6[0] -2*x1, D6[1] + 2*y1]
        D1E1 =[(D1[0]+E1[0])/2, (D1[1]+E1[1])/2]
        C6D6 = [(C6[0] + D6[0]) / 2, (C6[1] + D6[1]) / 2]
        D2D5 = [(D2[0] + D5[0]) / 2, (D2[1] + D5[1]) / 2]
        tile_verts_2D = [
            A1, B1, C1, D1, E1,
            C2, D2, E2,
            A3, C3, D3, E3,
            D4, E4,
            D5, E5,
            C6, D6, E6,
            D1E1, C6D6, D2D5]
        tile_verts = [[v[0]*a, v[1]*a, 0] for v in tile_verts_2D]
        tile_pols = [
            [0, 4, 19, 3, 9, 2, 1],
            [0, 1, 5, 6, 7],
            [8, 2 , 9, 10, 11],
            [8, 13, 16, 12, 5, 1, 2],
            [12, 15, 14, 21, 6, 5],
            [17, 18, 15, 12, 16, 20]]

        return tile_verts, tile_pols


class SvPentagon_15:
    input_sockets = "a"

    @staticmethod
    def layout(cols, rows, numy):
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = 0
        return offset_x, offset_y, tile_rotated

    @staticmethod
    def grid_params(angles, sides_data):
        a = sides_data[0]
        dy = a*sqrt(2)/2
        dx = a*8.175695419311523
        off_base_y = -a*9.400442123413086
        off_base_x = a*((sqrt(2)/(sqrt(3)-1))+sqrt(2)/2)
        return dx, dy, off_base_y, off_base_x

    @staticmethod
    def create_tile(angles, sides_data):

        a = sides_data[0]
        #the pentagon was generated matematicly but the tesselation was done in regular blender...
        pentagon15_v = [[0.0, 0.0, 0.0], [-0.7071067690849304, 0.7071067690849304, 0.0], [0.258819043636322, 0.9659258127212524, 0.0], [1.2247449159622192, 1.2247449159622192, 0.0], [1.9318516254425049, 0.0, 0.0], [2.1906707286834717, 0.9659258127212524, 0.0], [-0.70710688829422, 0.7071068286895752, 0.0], [0.0, 0.0, 0.0], [-0.9659259915351868, -0.25881898403167725, 0.0], [-1.931852102279663, -0.5176379680633545, 0.0], [-2.638958692550659, 0.7071070671081543, 0.0], [-2.897777795791626, -0.2588188052177429, 0.0], [2.1906707286834717, 0.9659258127212524, 0.0], [1.2247449159622192, 1.2247447967529297, 0.0], [1.9318517446517944, 1.9318516254425049, 0.0], [2.63895845413208, 2.63895845413208, 0.0], [3.8637032508850098, 1.9318516254425049, 0.0], [3.604884624481201, 2.897777557373047, 0.0], [2.1906704902648926, 0.9659256935119629, 2.262667386787598e-08], [1.9318516254425049, 0.0, 0.0], [2.8977773189544678, 0.258819043636322, -6.181724643283815e-08], [3.863703489303589, 0.517638087272644, -1.2363447865482158e-07], [3.8637025356292725, 1.9318512678146362, -6.181724643283815e-08], [4.570810317993164, 1.2247449159622192, -1.4626115785176808e-07], [4.311991214752197, 3.6048851013183594, 2.2626659657021264e-08], [3.3460655212402344, 3.863703727722168, -1.2434497875801753e-14], [3.604884624481201, 2.897778034210205, -6.18172535382655e-08], [3.863703727722168, 1.9318519830703735, -1.2363447865482158e-07], [5.27791690826416, 1.93185293674469, -6.18172535382655e-08], [4.570810317993164, 1.2247449159622192, -1.4626115785176808e-07], [4.311990737915039, 3.6048855781555176, -6.18172535382655e-08], [4.570810317993164, 4.570812225341797, -6.18172535382655e-08], [5.27791690826416, 3.8637051582336426, -6.18172535382655e-08], [5.985023498535156, 3.1565980911254883, -6.18172535382655e-08], [5.27791690826416, 1.93185293674469, -6.18172535382655e-08], [6.243843078613281, 2.190671920776367, -6.18172535382655e-08], [2.8977763652801514, 5.536737442016602, 1.0707057640502171e-07], [1.9318510293960571, 5.277918815612793, 8.444390431350257e-08], [2.6389575004577637, 4.570812225341797, 2.2626657880664425e-08], [3.346064567565918, 3.8637046813964844, -3.9190574341319007e-08], [4.570808410644531, 4.570812225341797, 2.2626657880664425e-08], [4.311990737915039, 3.6048855781555176, -6.18172535382655e-08], [-2.897778272628784, -0.25881892442703247, 0.0], [-1.931852102279663, -0.5176379680633545, 0.0], [-2.6389591693878174, -1.2247447967529297, 0.0], [-3.3460657596588135, -1.9318511486053467, 0.0], [-4.570810317993164, -1.2247445583343506, 0.0], [-4.3119916915893555, -2.1906700134277344, 0.0], [-2.897777795791626, -0.2588188052177429, 2.262667209151914e-08], [-2.638958692550659, 0.7071070075035095, 0.0], [-3.6048848628997803, 0.4482880234718323, -6.181724643283815e-08], [-4.5708112716674805, 0.18946903944015503, -1.2363447865482158e-07], [-4.570810317993164, -1.2247440814971924, -6.181724643283815e-08], [-5.277917861938477, -0.5176377892494202, -1.4626115785176808e-07], [-5.019098281860352, -2.897777557373047, 2.2626657880664425e-08], [-4.053173065185547, -3.1565961837768555, -1.4210854715202004e-14], [-4.3119916915893555, -2.1906704902648926, -6.18172535382655e-08], [-4.5708112716674805, -1.2247450351715088, -1.2363447865482158e-07], [-5.985024452209473, -1.224745750427246, -6.18172535382655e-08], [-5.277917861938477, -0.5176377892494202, -1.4626115785176808e-07], [-5.019098281860352, -2.897778034210205, -6.18172535382655e-08], [-5.277917861938477, -3.8637046813964844, -6.18172535382655e-08], [-5.985024452209473, -3.15659761428833, -6.18172535382655e-08], [-6.692131042480469, -2.449490547180176, -6.18172535382655e-08], [-5.985024452209473, -1.224745750427246, -6.18172535382655e-08], [-6.950950622558594, -1.4835646152496338, -6.18172535382655e-08], [-3.604884386062622, -4.829629898071289, 1.0707057640502171e-07], [-2.638958692550659, -4.5708112716674805, 8.444391141892993e-08], [-3.3460652828216553, -3.8637046813964844, 2.2626657880664425e-08], [-4.0531721115112305, -3.156597137451172, -3.9190574341319007e-08], [-5.277915954589844, -3.8637046813964844, 2.2626657880664425e-08], [-5.019098281860352, -2.897778034210205, -6.18172535382655e-08]]
        tile_pols = [[0, 1, 2, 3, 5, 4], [6, 7, 8, 9, 11, 10], [12, 13, 14, 15, 17, 16], [18, 19, 20, 21, 23, 22], [24, 25, 26, 27, 29, 28], [30, 31, 32, 33, 35, 34], [36, 37, 38, 39, 41, 40], [42, 43, 44, 45, 47, 46], [48, 49, 50, 51, 53, 52], [54, 55, 56, 57, 59, 58], [60, 61, 62, 63, 65, 64], [66, 67, 68, 69, 71, 70]]

        tile_verts = [[a*s for s in v] for v in pentagon15_v]

        return tile_verts, tile_pols

pentagon_dict = {
    'PENTAGON1': SvPentagon_1_1,
    'TYPE_1_4': SvPentagon_1_2,
    'PENTAGON2': SvPentagon_1_3,
    'PENTAGON3': SvPentagon_1_4,
    'TYPE_2_1': SvPentagon_2,
    'PENTAGON_TYPE_3': SvPentagon_3,
    'PENTAGON_TYPE_4': SvPentagon_4,
    'PENTAGON_TYPE_5': SvPentagon_5,
    'PENTAGON14': SvPentagon_14,
    'PENTAGON15': SvPentagon_15,
    }

def penta_layout(pol_type, numx, numy):
    '''Define rectangular layout'''

    cols = numx
    rows = [numy] * numx
    pentagon_c = pentagon_dict[pol_type]
    offset_x, offset_y, tile_rotated = pentagon_c.layout(cols, rows, numy)
    return cols, rows, offset_y, offset_x, tile_rotated


def generate_penta_grid(pol_type, align, settings):
    ang = settings[0]   # angle
    numx = settings[1]
    numy = settings[2]
    angles = settings[3:5]
    sides_data = settings[5:]
    pentagon_c = pentagon_dict[pol_type]
    dx, dy, off_base_y, off_base_x = pentagon_c.grid_params(angles, sides_data)

    '''
    cols : number of points along x
    rows : number of points along Y for each x location
    offset_y : offset of the points in each column
    tile_rotated:  offset in x for each tile
    '''
    cols = numx
    rows = [numy] * numx
    offset_x, offset_y, tile_rotated = pentagon_c.layout(cols, rows, numy)

    if pol_type in ['PENTAGON2', 'PENTAGON3'] or align == 'P':
        ang_base = 0
    elif align == 'X':
        ang_base = -atan2(-off_base_y, dx)
    elif align == 'Y':
        ang_base = pi/2 - atan2(dy, -off_base_x)
    else:
        ang_base = 0

    if pol_type in ['PENTAGON2']:
        grid = [(x * dx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y, tile_rotated[x][y] ) for x in range(cols) for y in range(rows[x])]
    else:
        grid = [(x * dx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y, ang_base) for x in range(cols) for y in range(rows[x])]

    angle = ang + ang_base
    cosa = cos(angle)
    sina = sin(angle)

    rotated_grid = [(x * cosa - y * sina, x * sina + y * cosa, rot) for x, y, rot in grid]

    return rotated_grid

def pentagon(angles, sides_data, pentagon_type):
    pentagon_c = pentagon_dict[pentagon_type]
    tile_verts, tile_pols = pentagon_c.create_tile(angles, sides_data)

    tile_edges = pols_to_edges([tile_pols], unique_edges=True)[0]
    return [tile_verts, tile_edges, tile_pols]

def generate_penta_tiles(tile_settings, grid, separate, pentagon_type):

    angle, _, _, A, B, a, b, c, d = tile_settings
    vert_grid_list, edge_grid_list, poly_grid_list = [[], [], []]

    tile = pentagon([A, B], [a, b, c, d], pentagon_type)
    angle2 = angle + grid[0][2]
    cosa = cos(angle2)
    sina = sin(angle2)
    tile[0] = [[v[0] * cosa - v[1] * sina, v[0] * sina + v[1] * cosa, 0] for v in tile[0]]

    vert_list, edge_list, poly_list = [[], [], []]

    if pentagon_type in ['PENTAGON2']:
        tiles_alterned(vert_list, edge_list, poly_list, tile, grid)
    else:
        tiles(vert_list, edge_list, poly_list, tile, grid)

    if not separate:
        vert_list, edge_list, poly_list = mesh_join(vert_list, edge_list, poly_list)
        vert_list, edge_list, poly_list = remove_doubles(vert_list, edge_list, poly_list, 1e-5)

    vert_grid_list.append(vert_list)
    edge_grid_list.append(edge_list)
    poly_grid_list.append(poly_list)

    return vert_grid_list, edge_grid_list, poly_grid_list


def tiles(vert_list, edge_list, poly_list, tile, grid):
    verts, edges, polys = tile
    for cx, cy, _ in grid:
        verts2 = [(x + cx, y + cy, 0.0) for x, y, _ in verts]

        vert_list.append(verts2)
        edge_list.append(edges)
        poly_list.append(polys)


def tiles_alterned(vert_list, edge_list, poly_list, tile, grid):
    verts, edges, polys = tile
    for cx, cy, rot in grid:
        inv = -1 if rot else 1
        verts2 = [(inv * x + cx, inv * y + cy, 0.0) for x, y, _ in verts]

        vert_list.append(verts2)
        edge_list.append(edges)
        poly_list.append(polys)
