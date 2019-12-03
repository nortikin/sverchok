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
from math import sin, cos, tan, radians, pi, atan2
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, list_match_modes, sv_zip
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.geom import circle
from sverchok.utils.modules.vertex_utils import center
from sverchok.utils.modules.polygon_utils import pols_to_edges
from sverchok.utils.listutils import lists_flat

from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles

GRID_TYPE_ITEMS = [
    ("PENTAGON1", "Pentagon 1", "", custom_icon("SV_PENTAGON_1"), 4),
    ("PENTAGON2", "Pentagon 2", "", custom_icon("SV_PENTAGON_2"), 5),
    ("PENTAGON3", "Pentagon 3", "", custom_icon("SV_PENTAGON_3"), 6),
    ("PENTAGON4", "Pentagon 4", "", custom_icon("SV_PENTAGON_4"), 7),
    ("PENTAGON5", "Pentagon 5", "", custom_icon("SV_PENTAGON_5"), 8)]

ALIGN_ITEMS = [
    ("X", "X", "Align tile primitives to X axis", custom_icon("SV_PENTAGON_X_ROT"), 0),
    ("Y", "Y", "Align tile primitives to Y axis", custom_icon("SV_PENTAGON_Y_ROT"), 1),
    ("P", "Pentagon", "Align tile primitives to pentagon", custom_icon("SV_PENTAGON_P_ROT"), 2)
]
ANGLE_UNITS_ITEMS = [
    ("RAD", "Radians", "Define angles in radians", 0),
    ("DEG", "Degrees", "Define angles in degrees", 1),
]
PENTAGON_SOCKETS = {
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


def generate_grid(pol_type, align, settings):
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

def generate_tiles(tile_settings, grid, separate, pentagon_type):

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
    sv_icon = 'SV_PENTAGON_5'

    def update_layout(self, context):
        self.update_sockets()
        updateNode(self, context)

    grid_type: EnumProperty(
        name="Type",
        description="Polygon Type",
        default="PENTAGON2", items=GRID_TYPE_ITEMS,
        update=update_layout)

    numx: IntProperty(
        name="NumX", description="Number of tile primitives along X",
        default=7, min=1, update=updateNode)

    numy: IntProperty(
        name="NumY", description="Number of tile primitives along Y",
        default=6, min=1, update=updateNode)

    angle: FloatProperty(
        name="Angle", description="Angle to rotate the grid and tiles",
        default=0.0, update=updateNode)
    angle_mode: EnumProperty(
        name="Angle", description="Angle units",
        default="DEG", items=ANGLE_UNITS_ITEMS,
        update=updateNode)
    center: BoolProperty(
        name="Center", description="Center grid around origin",
        default=True, update=updateNode)

    align: EnumProperty(
        name="Rotation", description="Base angle mode",
        default="P", items=ALIGN_ITEMS,
        update=updateNode)
    separate: BoolProperty(
        name="Separate", description="Separate tiles primitives",
        default=False, update=updateNode)
    angle_a: FloatProperty(
        name="A", description="Scale of the polygon tile",
        default=80.0, min=0.0, update=updateNode)
    angle_b: FloatProperty(
        name="B", description="Scale of the polygon tile",
        default=100.0, min=0.0, update=updateNode)
    angle_c: FloatProperty(
        name="C", description="Scale of the polygon tile",
        default=135.0, min=0.0, update=updateNode)
    angle_d: FloatProperty(
        name="D", description="Scale of the polygon tile",
        default=100.0, min=0.0, update=updateNode)

    side_a: FloatProperty(
        name="a", description="Scale of the polygon tile",
        default=1.0, min=0.0, update=updateNode)
    side_b: FloatProperty(
        name="b", description="Scale of the polygon tile",
        default=2.0, min=0.0, update=updateNode)
    side_c: FloatProperty(
        name="c", description="Scale of the polygon tile",
        default=2.5, min=0.0, update=updateNode)
    side_d: FloatProperty(
        name="d", description="Scale of the polygon tile",
        default=0.5, min=0.0, update=updateNode)

    list_match_global: EnumProperty(
        name="Match Global",
        description="Behavior on different list lengths, multiple objects level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)
    list_match_local: EnumProperty(
        name="Match Local",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)

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

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

        self.update_layout(context)

    def update_sockets(self):
        inputs = self.inputs

        inputs_n = 'ABCDabcd'
        for socket in inputs_n:
            if socket in PENTAGON_SOCKETS[self.grid_type]:
                if inputs[socket].hide_safe:
                    inputs[socket].hide_safe = False
            else:
                inputs[socket].hide_safe = True

    def draw_buttons(self, context, layout):
        layout.prop(self, 'grid_type', expand=False)
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop(self, 'align', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'grid_type', expand=False)
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop(self, 'align', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.separator()
        layout.label(text="List Match:")
        layout.prop(self, "list_match_global", text="Global Match", expand=False)
        layout.prop(self, "list_match_local", text="Local Match", expand=False)

    def rclick_menu(self, context, layout):
        '''right click sv_menu items'''
        layout.prop_menu_enum(self, "grid_type", text="Mode")
        if not self.grid_type in ['PENTAGON2', 'PENTAGON3']:
            layout.prop_menu_enum(self, 'align')
        layout.prop_menu_enum(self, "angle_mode", text="Angle Units")
        layout.prop(self, "flat_output", text="Flat Output", expand=False)
        layout.prop_menu_enum(self, "list_match_global", text="List Match Global")
        layout.prop_menu_enum(self, "list_match_local", text="List Match Local")

    def pentagon_tiler(self, params):
        params[1:3] = [list(map(lambda x: max(1, x), num)) for num in  params[1:3]]
        if self.angle_mode == 'DEG':
            params[0] = list(map(lambda x: radians(x), params[0]))
            params[3:7] = [list(map(lambda x: radians(x), ang)) for ang in params[3:7]]
        params = list_match_func[self.list_match_local](params)

        vert_list, edge_list, poly_list = [[], [], []]
        for par in zip(*params):
            grid = generate_grid(self.grid_type, self.align, par)
            verts, edges, polys = generate_tiles(par, grid, self.separate, self.grid_type)

            vert_list.extend(verts)
            edge_list.extend(edges)
            poly_list.extend(polys)

        # vert_list = center(vert_list)

        if self.separate:
            vert_list, edge_list, poly_list = lists_flat([vert_list, edge_list, poly_list])

        return vert_list, edge_list, poly_list

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return
        # input values lists
        inputs = self.inputs
        params = [s.sv_get() for s in inputs]
        params = list_match_func[self.list_match_global](params)
        vert_list, edge_list, poly_list = [], [], []
        v_add, e_add, p_add = vert_list.append, edge_list.append, poly_list.append
        if  self.flat_output:
            v_add, e_add, p_add = vert_list.extend, edge_list.extend, poly_list.extend
        else:
            v_add, e_add, p_add = vert_list.append, edge_list.append, poly_list.append

        for par in sv_zip(*params):
            verts, edges, polys = self.pentagon_tiler(par)
            v_add(verts)
            e_add(edges)
            p_add(polys)
        self.outputs['Vertices'].sv_set(vert_list)
        self.outputs['Edges'].sv_set(edge_list)
        self.outputs['Polygons'].sv_set(poly_list)


def register():
    bpy.utils.register_class(SvPentagonTilerNode)


def unregister():
    bpy.utils.unregister_class(SvPentagonTilerNode)
