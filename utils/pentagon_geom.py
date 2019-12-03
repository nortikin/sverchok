# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from math import sin, cos, tan, pi, atan2

from sverchok.utils.modules.polygon_utils import pols_to_edges
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles

def rect_layout(pol_type, numx, numy):
    '''Define rectangular layout'''

    cols = numx
    rows = [numy] * numx
    tile_rotated = 0
    if pol_type == 'PENTAGON1':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]

    elif pol_type == 'PENTAGON2':
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]

    elif pol_type == 'PENTAGON3':
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]

    elif pol_type == 'PENTAGON4':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]

    elif pol_type == 'PENTAGON5':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]

    return cols, rows, offset_y, offset_x, tile_rotated


def generate_penta_grid(pol_type, align, settings):
    ang = settings[0]   # angle
    numx = settings[1]
    numy = settings[2]
    A, B, C, D = settings[3:7]
    a, b, c, d = settings[7:]
    if pol_type == 'PENTAGON1':

        dy = c * sin(A)
        dx = a + d - b * cos(B) +a - d - c * cos(A)
        off_base_y = b * sin(B) - dy
        off_base_x = -a + d + c * cos(A)

    elif pol_type == 'PENTAGON2':

        dy = b
        dx = 2 * a * cos(A - pi/2) + d * cos(C + A -3*pi/2)
        off_base_y = -b + 2 * a * sin(A - pi/2) - d * sin(-C - A -pi/2)
        off_base_x = 0
    elif pol_type == 'PENTAGON3':
        dy = b
        dx = 2 * a * cos(A - pi/2) + (b/2) / tan(D/2)
        off_base_y = b/2
        off_base_x = 0
    elif pol_type == 'PENTAGON4':
        dy = c + b * sin(B - pi/2) + c * sin(B - C - 3*pi/2) + b * sin(-pi/2 - C)
        dx = b * cos(B - pi/2) + b * cos(-C + pi/2) + c * cos(B - C -3*pi/2)
        off_base_y = c - b * sin(-C + pi/2) - c * sin(B - C - 3*pi/2) - b*sin(B - pi/2)
        off_base_x = -b * cos(B - pi/2) - c*cos(B - C - 3*pi/2) - b*cos(-pi/2 - C)

    elif pol_type == 'PENTAGON5':
        dy = b + d * sin(- C - pi) + d * sin(-pi/2 - C)
        dx = b + d * cos(-C + pi/2) + d * cos(-C - pi)
        off_base_y = b -d * sin(-C + pi/2) - d * sin(-C - pi)
        off_base_x = -b - d * cos(- C -pi) - d * cos(-pi/2 - C)
    '''
    cols : number of points along x
    rows : number of points along Y for each x location
    offset_y : offset of the points in each column
    tile_rotated:  offset in x for each tile
    '''

    cols, rows, offset_y, offset_x, tile_rotated = rect_layout(pol_type, numx, numy)

    if pol_type in ['PENTAGON2', 'PENTAGON3'] or align == 'P':
        ang_base = 0
    elif align == 'X':
        ang_base = -atan2(-off_base_y, dx)
    elif align == 'Y':
        ang_base = pi/2- atan2(dy, -off_base_x)
    else:
        ang_base = 0

    if pol_type in ['PENTAGON2']:
        grid = [(x * dx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y, tile_rotated[x][y] + ang_base) for x in range(cols) for y in range(rows[x])]

    else:
        grid = [(x * dx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y, ang_base) for x in range(cols) for y in range(rows[x])]

    angle = ang + ang_base
    cosa = cos(angle)
    sina = sin(angle)

    rotated_grid = [(x * cosa - y * sina, x * sina + y * cosa, rot) for x, y, rot in grid]

    return rotated_grid

def pentagon(angles, sides_data, pentagon_type):
    A, B, C, D = angles
    a, b, c, d = sides_data


    if pentagon_type == 'PENTAGON1':
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

    elif pentagon_type == 'PENTAGON2':
        Ep = (a * cos(pi/2 - A), a * sin(pi/2 - A))
        Dp = (Ep[0] + d * cos(-C - A - pi/2), Ep[1] + d*sin(-C - A - pi/2))
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
            [0, 1, 2, 3, 4],
            [0, 1, 5, 6, 7]
            ]

    elif pentagon_type == 'PENTAGON3':
        Cp = (a * cos(pi/2 - A), b + a * sin(pi/2 - A))
        Dp = (Cp[0] + (b/2) / tan(D/2), Cp[1] - b/2)
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
            [0, 1, 2, 3, 4],
            [0, 1, 5, 6, 7]
            ]

    elif pentagon_type == 'PENTAGON4':
        Ap = (b * cos(B - pi/2), b * sin(B - pi/2))
        Cp = (0, -c)
        Dp = (Cp[0] + b * cos(-C + pi/2), Cp[1] + b * sin(-C + pi/2))
        Ep = (Dp[0] + c * cos(B - C + pi/2), Dp[1] + c * sin(B -C + pi/2))
        B2p = (Ap[0] + c * cos(B - C - 3*pi/2), Ap[1] + c * sin(B - C - 3*pi/2))
        C3p = (b * cos(B + pi/2), b * sin(B + pi/2), 0)
        B3p = (C3p[0] + c * cos(B - C + 3*pi/2), C3p[1] + c * sin(B - C + 3*pi/2))
        D4p = (b * cos(-C - pi/2), c + b * sin(-C - pi/2), 0)
        tile_verts = [
            [0, 0, 0],
            [Ap[0], Ap[1], 0],
            [Ep[0], Ep[1], 0],
            [Dp[0], Dp[1], 0],
            [0, -c, 0],

            [B2p[0], B2p[1], 0],
            [B2p[0] + D4p[0], B2p[1] + b * sin(- pi/2 - C), 0],
            [0, c, 0],

            [C3p[0], C3p[1], 0],
            [B3p[0], B3p[1], 0],
            [B3p[0] + b * cos(pi/2 - C), B3p[1] + b * sin(pi/2 - C), 0],

            [D4p[0], D4p[1], 0],
            [D4p[0] + c * cos(-C - pi/2 + B), D4p[1] + c * sin(-C -pi/2 + B), 0],
            ]
        tile_pols = [
            [0, 1, 2, 3, 4],
            [0, 1, 5, 6, 7],
            [0, 4, 10, 9, 8],
            [0, 8, 12, 11, 7]
            ]

    elif pentagon_type == 'PENTAGON5':
        Ap = (b, 0)
        Cp = (0, -b)
        Dp = (Cp[0] + d * cos(-C + pi/2), Cp[1]+ d * sin(-C + pi/2))
        Ep = (Dp[0] + d * cos(-C + pi), Dp[1] + d * sin(-C + pi))
        B2p = (Ap[0] + d * cos(-C - pi), Ap[1] + d * sin(-C - pi))
        C3p = (-b, 0, 0)
        B3p = (C3p[0] + d * cos(-C), C3p[1] + d * sin(-C))
        D4p = (d * cos(-C - pi/2), b + d * sin(-C - pi/2), 0)
        tile_verts = [
            [0, 0, 0],
            [b, 0, 0],
            [Ep[0], Ep[1], 0],
            [Dp[0], Dp[1], 0],
            [0, -b, 0],

            [B2p[0], B2p[1], 0],
            [B2p[0] + D4p[0], B2p[1]+ d * sin(-C - pi/2), 0],
            [0, b, 0],

            [C3p[0], C3p[1], 0],
            [B3p[0], B3p[1], 0],
            [B3p[0] + d * cos(pi/2 - C), B3p[1]+ d * sin(pi/2 - C), 0],

            [D4p[0], D4p[1], 0],
            [D4p[0] + d * cos(-C), D4p[1] + d * sin(-C), 0]
            ]
        tile_pols = [
            [0, 1, 2, 3, 4],
            [0, 1, 5, 6, 7],
            [0, 4, 10, 9, 8],
            [0, 8, 12, 11, 7]]


    tile_edges = pols_to_edges([tile_pols], unique_edges=True)[0]
    return [tile_verts, tile_edges, tile_pols]

def generate_penta_tiles(tile_settings, grid, separate, pentagon_type):

    angle, _, _, A, B, C, D, a, b, c, d = tile_settings
    vert_grid_list, edge_grid_list, poly_grid_list = [[], [], []]

    tile = pentagon([A, B, C, D], [a, b, c, d], pentagon_type)
    print(grid[0][2])
    angle2 = angle + grid[0][2]
    cosa = cos(angle2)
    sina = sin(angle2)
    tile[0] = [[v[0] * cosa - v[1] * sina, v[0] * sina + v[1] * cosa, 0] for v in tile[0]]

    vert_list, edge_list, poly_list = [[], [], []]

    if pentagon_type == 'PENTAGON2':
        tiles_alterned(vert_list, edge_list, poly_list, tile, grid)
    else:
        tiles(vert_list, edge_list, poly_list, tile, grid)

    if not separate:
        vert_list, edge_list, poly_list = mesh_join(vert_list, edge_list, poly_list)
        vert_list, edge_list, poly_list, _ = remove_doubles(vert_list, poly_list, 1e-5, False)

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
