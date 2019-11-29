# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from math import sqrt, sin, cos, tan, radians,pi, atan2

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.geom import circle
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles
from mathutils import Vector
from mathutils.geometry import intersect_sphere_sphere_2d

grid_type_items = [
    ("PENTAGON1", "Pentagon 1", "", custom_icon("SV_HEXAGON"), 4),
    ("PENTAGON2", "Pentagon 2", "", custom_icon("SV_HEXAGON"), 5),
    ("PENTAGON3", "Pentagon 3", "", custom_icon("SV_HEXAGON"), 6),
    ("PENTAGON4", "Pentagon 4", "", custom_icon("SV_HEXAGON"), 7),
    ("PENTAGON5", "Pentagon 5", "", custom_icon("SV_HEXAGON"), 8)]
size_mode_items = [
    ("RADIUS", "Radius", "Define polygon by its radius", custom_icon("SV_RAD"), 0),
    ("SIDE", "Side", "Define polygon by its side", custom_icon("SV_SIDE"), 1)]
align_items = [
    ("X", "X", "Define polygon by its radius", custom_icon("SV_RAD"), 0),
    ("Y", "Y", "Define polygon by its side", custom_icon("SV_SIDE"), 1),
    ("P", "P", "Define polygon by its side", custom_icon("SV_SIDE"), 2)
]
pentagon_sockets= {
    "PENTAGON1": "ABabcd",
    "PENTAGON2": "ACabd",
    "PENTAGON3": "ADab",
    "PENTAGON4": "BCbc",
    "PENTAGON5": "Cbd",

}

def rect_layout(pol_type, numx, numy):
    '''Define rectangular layout'''
    #_, _, numx, numy,_,_ = settings

    cols = numx
    rows = [numy] * numx
    tile_rotated = 0
    offset_x = [0  for l in range(numy)]
    if pol_type == 'PENTAGON1':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]
    elif pol_type == 'PENTAGON2':
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]
        grid_center = [(numx - 1) / 2, numy/2]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]
    elif pol_type == 'PENTAGON3':
        offset_y = [l%2  for l in range(cols)]
        offset_x = [l%2  for l in range(numy)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]
    elif pol_type == 'PENTAGON4':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]
    elif pol_type == 'PENTAGON5':
        offset_y = [l  for l in range(cols)]
        offset_x = [l  for l in range(numy)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]
        tile_rotated = [[(x) % 2 for y in range(rows[x])] for x in range(cols)]

    return cols, rows, offset_y, offset_x, grid_center, tile_rotated


def generate_grid(center, pol_type, align, settings):
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
        dx = 2*a*cos(A-pi/2)+cos(D/2)*(b/2)/sin(D/2)
        off_base_y = b/2
        off_base_x = 0
    elif pol_type == 'PENTAGON4':

        dy = c + b * sin(B - pi/2) + c * sin(B - C - 3*pi/2) + b*sin(-pi/2 - C)
        dx = b * cos(B - pi/2)+ b * cos(-C + pi/2) + c*cos(B - C -3*pi/2)
        off_base_y = c - b * sin(-C + pi/2) - c*sin(B - C - 3*pi/2) - b*sin(B - pi/2)
        off_base_x = -b * cos(B - pi/2) - c*cos(B - C - 3*pi/2) - b*cos(-pi/2 - C)
    elif pol_type == 'PENTAGON5':

        dy = b + d*sin(- C - pi) + d*sin(-pi/2 - C)
        dx = b + d * cos(-C+pi/2) + d*cos(-C - pi)
        off_base_y = b -d * sin(-C + pi/2) - d*sin(-C - pi)
        off_base_x = -b - d*cos(- C -pi) - d*cos(-pi/2 - C)
    '''
    cols : number of points along x
    rows : number of points along Y for each x location
    offset_y : offset of the points in each column
    tile_rotated:  offset in x for each tile
    grid_center : center of the grid
    '''

    cols, rows, offset_y, offset_x, grid_center, tile_rotated = rect_layout(pol_type, numx, numy)

    cx = grid_center[0] * dx if center else 0
    cy = grid_center[1] * dy if center else 0
    if pol_type in ['PENTAGON2', 'PENTAGON3'] or align == 'P':
        ang_vertical = 0
    elif align == 'X':
        ang_vertical =  - atan2(-off_base_y, dx)
    elif align == 'Y':
        ang_vertical =  pi/2- atan2(dy, -off_base_x)
    else:
        ang_vertical = 0

    if pol_type in ['PENTAGON2']:
        grid = [(x * dx - cx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y - cy, tile_rotated[x][y]+ang_vertical) for x in range(cols) for y in range(rows[x])]

    else:
        grid = [(x * dx - cx - offset_x[y]* off_base_x, y * dy - offset_y[x] * off_base_y - cy, ang_vertical) for x in range(cols) for y in range(rows[x])]

    angle = radians(ang) +ang_vertical
    cosa = cos(angle)
    sina = sin(angle)

    rotated_grid = [(x * cosa - y * sina, x * sina + y * cosa, rot) for x, y, rot in grid]

    return rotated_grid

def pentagon(angles, sides_data, pentagon_type):
    A, B, C, D = angles
    a, b, c, d = sides_data
    A = pi - A
    if pentagon_type == 'PENTAGON0':
        a2 = a/3
        tile = [[[0, 0, 0],[a2, a2, 0],[a2,a,0],[-a2,a,0],[-a2,a2,0],[-a,a2,0],[-a,-a2,0],[-a2,-a2,0],[-a2,-a,0], [a2, -a, 0], [a2,-a2, 0],[a, -a2, 0],[a,a2,0]],
            [(0,1),(1,2),(2,3),(3,4),(4,0)],
            [[0,1,2,3,4],[4,5,6,7,0], [7,8,9,10,0],[10,11,12,1,0]]
            ]

    elif pentagon_type == 'PENTAGON1':
        A,B,C,D = angles
        a,b,c,d = sides_data
        A = pi - A
        Cp =(a + c * cos(A), c * sin(A))
        if a < d:
            tile = [[
                [0, 0, 0],
                [a, 0, 0],
                [Cp[0], Cp[1], 0],
                [Cp[0] - d + a, Cp[1], 0],
                [Cp[0] -d, Cp[1], 0],
                [b * cos(B), b * sin(B), 0],
                [d, 0, 0],
                [a + d, 0, 0],
                [Cp[0] + a + b * cos(B-pi), Cp[1] + b * sin(B-pi), 0],
                [Cp[0] + a, Cp[1], 0]],
                [(0,1),(1,2),(2,3),(3,4),(4,0)],
                [[0, 1, 2, 3, 4, 5], [1, 6, 7, 8, 9, 2]]
                ]
        else:
            tile = [[
                [0, 0, 0],
                [d, 0, 0],
                [a, 0, 0],
                [Cp[0], Cp[1], 0],
                [Cp[0] - d, Cp[1], 0],
                [b * cos(B), b *sin(B), 0],
                [a + d, 0, 0],
                [Cp[0] + a + b * cos(B - pi), Cp[1] + b * sin(B - pi), 0],
                [Cp[0] + a, Cp[1], 0],
                [Cp[0] - d + a, Cp[1],0]
                ],
                [(0,1),(1,2),(2,3),(3,4),(4,0)],
                [[0, 1, 2, 3, 4, 5], [2, 6, 7, 8, 9, 3]]
                ]
    elif pentagon_type == 'PENTAGON2':
        tile = [[
            [0, 0, 0],
            [0,b,0],
            [a*cos(A-pi/2), b+a*sin(A-pi/2), 0],
            [a*cos(A-pi/2)+d*cos(-C+A-pi/2-pi), a*sin(A-pi/2)+d*sin(-C+A-pi/2-pi), 0],
            [a*cos(A-pi/2), a*sin(A-pi/2), 0],

            [-a*cos(A-pi/2), b+a*sin(A-pi/2), 0],
            [-(a*cos(A-pi/2)+d*cos(-C+A-pi/2-pi)), a*sin(A-pi/2)+d*sin(-C+A-pi/2-pi), 0],
            [-a*cos(A-pi/2), a*sin(A-pi/2), 0],
            ],
            [(0,1),(1,2),(2,3),(3,4),(4,0)],
            [[0,1,2,3,4], [0,1,5,6,7]
            ]
            ]
    elif pentagon_type == 'PENTAGON3':
        tile = [[
            [0, 0, 0],
            [0,b,0],
            [a*cos(A-pi/2), b+a*sin(A-pi/2), 0],
            [a*cos(A-pi/2)+(b/2)*cos(D/2)/sin(D/2), b/2+a*sin(A-pi/2), 0],
            [a*cos(A-pi/2), a*sin(A-pi/2), 0],

            [-a*cos(A-pi/2), b+a*sin(A-pi/2), 0],
            [-(a*cos(A-pi/2)+cos(D/2)*(b/2)/sin(D/2)), b/2+a*sin(A-pi/2), 0],
            [-a*cos(A-pi/2), a*sin(A-pi/2), 0],
            ],
            [(0,1),(1,2),(2,3),(3,4),(4,0)],
            [[0,1,2,3,4], [0,1,5,6,7]
            ]
            ]
    elif pentagon_type == 'PENTAGON4':
        Ap = (b*cos(B - pi/2), b * sin(B - pi/2))
        Cp = (0, -c)
        Dp = (Cp[0] + b * cos(-C + pi/2), Cp[1]+ b * sin(-C + pi/2))
        Ep = (Dp[0] + c*cos(-C+ pi/2 + B), Dp[1] + c*sin(-C + pi/2 + B) )
        B2p = (Ap[0] + c*cos(B - C - 3*pi/2), Ap[1] + c*sin(B - C - 3*pi/2))
        C3p = (b * cos(B + pi/2), b * sin(B + pi/2), 0)
        B3p = (C3p[0] + c*cos(B - C + 3*pi/2), C3p[1]+c*sin(B - C +3*pi/2))
        D4p = (b * cos(-C - pi/2), c + b * sin(-C - pi/2), 0)
        tile = [[
            [0, 0, 0],
            [b*cos(B - pi/2), b * sin(B- pi/2), 0],
            [Ep[0], Ep[1], 0],
            [Dp[0], Dp[1] , 0],
            [0, -c, 0],

            [B2p[0], B2p[1], 0],
            [B2p[0] + b*cos(- pi/2 - C), B2p[1]+ b*sin(- pi/2 - C), 0],
            [0, c, 0],

            [C3p[0], C3p[1], 0],
            [B3p[0], B3p[1], 0],
            [B3p[0] + b*cos(pi/2 - C), B3p[1]+ b*sin(pi/2 - C), 0],

            [D4p[0], D4p[1], 0],
            [D4p[0] + c * cos(-C- pi/2 + B), D4p[1] + c * sin(-C-pi/2 + B),0],
            ],
            [(0,1),(1,2),(2,3),(3,4),(4,0)],
            [[0,1,2,3,4], [0,1,5,6,7],[0,4,10,9,8], [0,8,12,11,7]
            ]
            ]
    elif pentagon_type == 'PENTAGON5':
        Ap = (b, 0)
        Cp = (0, -b)
        Dp = (Cp[0] + d * cos(-C + pi/2), Cp[1]+ d * sin(-C + pi/2))
        Ep = (Dp[0] + d*cos(-C+ pi/2 + pi/2), Dp[1] + d*sin(-C + pi/2 + pi/2) )
        B2p = (Ap[0] + d*cos(pi/2 - C - 3*pi/2), Ap[1] + d*sin(pi/2 - C - 3*pi/2))
        C3p = (b * cos(pi/2 + pi/2), b * sin(pi/2 + pi/2), 0)
        B3p = (C3p[0] + d * cos(pi/2 - C + 3*pi/2), C3p[1] + d * sin(pi/2 - C +3*pi/2))
        D4p = (d * cos(-C - pi/2), b + d * sin(-C - pi/2), 0)
        tile = [[
            [0, 0, 0],
            [b, 0, 0],
            [Ep[0], Ep[1], 0],
            [Dp[0], Dp[1] , 0],
            [0, -b, 0],

            [B2p[0], B2p[1], 0],
            [B2p[0] + d*cos(pi/2 - C - 3*pi/2 + pi/2), B2p[1]+ d*sin(pi/2 - C - 3*pi/2 + pi/2), 0],
            [0, b, 0],

            [C3p[0], C3p[1], 0],
            [B3p[0], B3p[1], 0],
            [B3p[0] + d*cos(pi/2 - C), B3p[1]+ d*sin(pi/2 - C), 0],

            [D4p[0], D4p[1], 0],
            [D4p[0] + d * cos(-C- pi/2 + pi/2), D4p[1] + d * sin(-C-pi/2 + pi/2), 0],
            ],
            [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (1, 5), (5, 6), (6, 7),(7, 0)],
            [[0, 1, 2, 3, 4], [0, 1, 5, 6, 7], [0, 4, 10, 9, 8], [0, 8, 12, 11, 7]
            ]
            ]
    return tile

def generate_tiles(tile_settings, separate, pentagon_type):

    angle, grid, A, B, C, D, a, b, c, d = tile_settings
    vert_grid_list, edge_grid_list, poly_grid_list = [[], [], []]

    tile = pentagon([A, B, C, D], [a, b, c, d], pentagon_type)
    print(grid[0][2])
    angle2 = radians(angle)+grid[0][2]
    cosa = cos(angle2)
    sina = sin(angle2)
    tile[0] = [[v[0] * cosa - v[1] * sina, v[0] * sina + v[1] * cosa, 0] for v in tile[0]]

    vert_list, edge_list, poly_list = [[], [], []]

    if pentagon_type == 'PENTAGON2':
        tiles_triangular(vert_list, edge_list, poly_list, tile, grid)
    else:
        tiles(vert_list, edge_list, poly_list, tile, grid)

    if not separate:
        vert_list, edge_list, poly_list = mesh_join(vert_list, edge_list, poly_list)
        # if scale == 1.0:
        vert_list, edge_list, poly_list, _ = remove_doubles(vert_list, poly_list, 0.01, False)

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


def tiles_triangular(vert_list, edge_list, poly_list, tile, grid):
    verts, edges, polys = tile
    for cx, cy, rot in grid:
        inv = -1 if rot else 1
        verts2 = [(inv * x + cx, inv * y + cy, 0.0) for x, y, _ in verts]

        vert_list.append(verts2)
        edge_list.append(edges)
        poly_list.append(polys)


class SvPentagonTilerNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Hexagonal, Triangular, Ortogonal,
    Tooltip: Create polygon array assambled to fill the plane. Triangles, Hexagons and Squares
    """
    bl_idname = 'SvPentagonTilerNode'
    bl_label = 'Pentagon Tiler'
    sv_icon = 'SV_GRID'

    def update_layout(self, context):
        self.update_sockets()
        updateNode(self, context)

    grid_type: EnumProperty(
        name="Type",
        description="Polygon Type",
        default="PENTAGON2", items=grid_type_items,
        update=update_layout)

    numx: IntProperty(
        name="NumX", description="Number of points along X",
        default=7, min=1, update=updateNode)

    numy: IntProperty(
        name="NumY", description="Number of points along Y",
        default=6, min=1, update=updateNode)

    angle: FloatProperty(
        name="Angle", description="Angle to rotate the grid and tiles",
        default=0.0, update=updateNode)

    center: BoolProperty(
        name="Center", description="Center grid around origin",
        default=True, update=updateNode)

    align: EnumProperty(
        name="Align", description="Center grid around origin",
        default="P", items=align_items,
        update=updateNode)
    separate: BoolProperty(
        name="Separate", description="Separate tiles",
        default=False, update=updateNode)
    angle_a: FloatProperty(
        name="A", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    angle_b: FloatProperty(
        name="B", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    angle_c: FloatProperty(
        name="C", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    angle_d: FloatProperty(
        name="D", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)

    side_a: FloatProperty(
        name="a", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    side_b: FloatProperty(
        name="b", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    side_c: FloatProperty(
        name="c", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)
    side_d: FloatProperty(
        name="d", description="Scale of the polygon tile",
        default=0.0, min=0.0, update=updateNode)


    def sv_init(self, context):
        self.width = 170

        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.inputs.new('SvStringsSocket', "NumX").prop_name = 'numx'
        self.inputs.new('SvStringsSocket', "NumY").prop_name = 'numy'
        self.inputs.new('SvStringsSocket', "A").prop_name = 'angle_a'
        self.inputs.new('SvStringsSocket', "B").prop_name = 'angle_b'
        self.inputs.new('SvStringsSocket', "C").prop_name = 'angle_c'
        self.inputs.new('SvStringsSocket', "D").prop_name = 'angle_d'
        self.inputs.new('SvStringsSocket', "a").prop_name = 'side_a'
        self.inputs.new('SvStringsSocket', "b").prop_name = 'side_b'
        self.inputs.new('SvStringsSocket', "c").prop_name = 'side_c'
        self.inputs.new('SvStringsSocket', "d").prop_name = 'side_d'

        self.outputs.new('SvVerticesSocket', "Centers")
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

        self.update_layout(context)

    def update_sockets(self):
        inputs = self.inputs

        inputs_n = 'ABCDabcd'
        for s in inputs_n:
            if s in pentagon_sockets[self.grid_type]:
                if inputs[s].hide_safe:
                    inputs[s].hide_safe = False
            else:
                inputs[s].hide_safe = True

    def draw_buttons(self, context, layout):
        layout.prop(self, 'grid_type', expand=False)
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop(self, 'align', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists
        inputs = self.inputs
        input_numx = inputs["NumX"].sv_get()[0]
        input_numy = inputs["NumY"].sv_get()[0]
        input_angle = inputs["Angle"].sv_get()[0]
        input_angle_a = inputs["A"].sv_get()[0]
        input_angle_b = inputs["B"].sv_get()[0]
        input_angle_c = inputs["C"].sv_get()[0]
        input_angle_d = inputs["D"].sv_get()[0]
        side_a = inputs["a"].sv_get()[0]
        side_b = inputs["b"].sv_get()[0]
        side_c = inputs["c"].sv_get()[0]
        side_d = inputs["d"].sv_get()[0]
        angles = [input_angle_a, input_angle_b, input_angle_c, input_angle_d]
        sides_data = [side_a, side_b, side_c, side_d]
        # sanitize the input values
        input_numx = list(map(lambda x: max(1, x), input_numx))
        input_numy = list(map(lambda x: max(1, x), input_numy))

        # generate the vectorized grids
        param_list = []
        param_list.extend([input_angle, input_numx, input_numy])
        param_list += angles
        param_list += sides_data

        params = match_long_repeat(param_list)
        grid_list = [generate_grid(self.center, self.grid_type, self.align, args) for args in zip(*params)]
        self.outputs['Centers'].sv_set([[(x, y, 0.0) for x, y, _ in grid_list[0]]])

        # generate the vectorized tiles only if any of VEP outputs are linked
        _, V, E, P = self.outputs[:]
        if not any(s.is_linked for s in [V, E, P]):
            return
        params = [input_angle, grid_list]
        params += angles
        params += sides_data
        params = match_long_repeat(params)

        vert_list, edge_list, poly_list = [[], [], []]
        for p in zip(*params):

            verts, edges, polys = generate_tiles(p, self.separate, self.grid_type)
            vert_list.extend(verts)
            edge_list.extend(edges)
            poly_list.extend(polys)

        if self.separate and len(vert_list) < 2:
            vert_list = vert_list[0]
            edge_list = edge_list[0]
            poly_list = poly_list[0]

        self.outputs['Vertices'].sv_set(vert_list)
        self.outputs['Edges'].sv_set(edge_list)
        self.outputs['Polygons'].sv_set(poly_list)


def register():
    bpy.utils.register_class(SvPentagonTilerNode)


def unregister():
    bpy.utils.unregister_class(SvPentagonTilerNode)
