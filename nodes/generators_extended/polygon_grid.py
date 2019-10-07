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

from math import sqrt, sin, cos, radians

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.geom import circle
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.nodes.modifier_change.remove_doubles import remove_doubles

grid_layout_items = [
    ("RECTANGLE", "Rectangle", "", custom_icon("SV_HEXA_GRID_RECTANGLE"), 0),
    ("TRIANGLE", "Triangle", "", custom_icon("SV_HEXA_GRID_TRIANGLE"), 1),
    ("DIAMOND", "Diamond", "", custom_icon("SV_HEXA_GRID_DIAMOND"), 2),
    ("HEXAGON", "Hexagon", "", custom_icon("SV_HEXA_GRID_HEXAGON"), 3)]
grid_type_items = [
    ("TRIANGLE", "Triangle", "", custom_icon("SV_TRIANGLE"), 0),
    ("SQUARE", "Square", "", custom_icon("SV_SQUARE"), 1),
    ("HEXAGON", "Hexagon", "", custom_icon("SV_HEXAGON"), 2)]
size_mode_items = [
    ("RADIUS", "Radius", "Define polygon by its radius", custom_icon("SV_RAD"), 0),
    ("SIDE", "Side", "Define polygon by its side", custom_icon("SV_SIDE"), 1)]


def triang_layout(settings, pol_type):
    '''Define triangular layout'''
    _, _, level = settings
    cols = level
    if pol_type == 'HEXAGON':
        rows = range(1, cols + 1)
        offset_y = range(cols)
        grid_center = [(level - 1) * 2 / 3, 0.0]
        tile_rotated = 0

    elif pol_type == 'TRIANGLE':
        rows = range(1, 2 * cols + 1, 2)
        offset_y = range(cols)
        grid_center = [(level - 1) * 2 / 3, 0.0]
        tile_rotated = [[(y) % 2 for y in range(rows[x])] for x in range(cols)]

    else: # pol_type == 'SQUARE':
        rows = range(1, 2 * cols + 2, 2)
        offset_y = range(0, 2 * cols, 2)
        grid_center = [(level - 1) / 2, 0.0]
        tile_rotated = 0
    return cols, rows, offset_y, grid_center, tile_rotated


def hexa_layout(settings, pol_type):
    '''Define hexagonal layout'''
    _, _, level = settings
    tile_rotated = 0
    if pol_type == 'HEXAGON':
        cols = 2 * level - 1
        rows = [cols - abs(level - 1 - l) for l in range(cols)]
        offset_y = [level - 1 - abs(level - 1 - l) for l in range(cols)]
        grid_center = [level - 1, (level - 1) / 2]

    elif pol_type == 'TRIANGLE':
        cols = 2 * level
        rows = [4 * level - abs(2*level - 1 - 2 * l) for l in range(cols)]
        offset_y = [2 * level - 0.5 - abs(level - 0.5 - l) for l in range(cols)]
        tile_rotated = [[(y + int(x / level)) % 2 for y in range(rows[x])] for x in range(cols)]
        grid_center = [level - 2 / 3, 0.0]

    else: # pol_type == 'SQUARE':
        cols = 2 * level
        rows = [3 * level - 1 - abs(2 * level - 1 - 2 * l) for l in range(cols)]
        offset_y = [2 * level - 1 - abs(2 * level - 1 - 2 * l) for l in range(cols)]
        grid_center = [level - 0.5, (level - 1) / 2]

    return cols, rows, offset_y, grid_center, tile_rotated


def diamond_layout(settings, pol_type):
    '''Define diamond layout'''
    _, _, level = settings
    tile_rotated = 0
    if pol_type == 'HEXAGON':
        cols = 2 * level - 1
        rows = [level - abs(level - 1 - l) for l in range(cols)]
        offset_y = [level - 1 - abs(level - 1 - l) for l in range(cols)]
        grid_center = [level - 1, 0.0]

    elif pol_type == 'TRIANGLE':
        cols = 2 * level
        rows = [cols - abs(2 * level - 1 - 2 * l) for l in range(cols)]
        offset_y = [level - 0.5 - abs(level - 0.5 - l) for l in range(cols)]
        tile_rotated = [[(y + int(x / level)) % 2 for y in range(rows[x])] for x in range(cols)]
        grid_center = [(level - 1) + 1/3.0, 0.0]

    else: # pol_type == 'SQUARE':
        cols = 2 * level - 1
        rows = [2 * level - 1 - abs(2 * level - 2 - 2 * l) for l in range(cols)]
        offset_y = [2 * level - 1 - abs(2 * level - 2 - 2 * l) for l in range(cols)]
        grid_center = [level - 1, 0.0]

    return cols, rows, offset_y, grid_center, tile_rotated


def rect_layout(settings, pol_type):
    '''Define rectangular layout'''
    _, _, numx, numy = settings
    cols = numx
    rows = [numy] * numx
    tile_rotated = 0
    if pol_type == 'HEXAGON':
        offset_y = [l % 2 for l in range(cols)]
        grid_center = [(numx - 1) / 2, (numy - 1.0 + 0.5 * (numx > 1)) / 2]

    elif pol_type == 'TRIANGLE':
        offset_y = [0 for l in range(cols)]
        grid_center = [(numx) / 2 - 2/3.0, (numy-1) / 2]
        tile_rotated = [[(x + y) % 2 for y in range(rows[x])] for x in range(cols)]

    else: # pol_type == 'SQUARE':
        offset_y = [0 for l in range(cols)]
        grid_center = [(numx-1) / 2, (numy-1) / 2]

    return cols, rows, offset_y, grid_center, tile_rotated


def generate_grid(center, layout, pol_type, settings):
    r = settings[0]   # radius
    a = settings[1]   # angle

    if pol_type == 'HEXAGON':
        dx = r * 3 / 2    # distance between two consecutive points along X
        dy = r * sqrt(3)  # distance between two consecutive points along Y
        off_base = dy / 2
    if pol_type == 'TRIANGLE':
        dx = r * 3 / 2
        dy = r * sqrt(3)/2
        off_base = dy
    elif pol_type == 'SQUARE':
        dx = r * sqrt(2)
        dy = r * sqrt(2)
        off_base = dy / 2

    '''
    cols : number of points along x
    rows : number of points along Y for each x location
    offset_y : offset of the points in each column
    tile_rotated:  offset in x for each tile
    grid_center : center of the grid
    '''

    if layout == "TRIANGLE":
        cols, rows, offset_y, grid_center, tile_rotated = triang_layout(settings, pol_type)

    elif layout == "HEXAGON":
        cols, rows, offset_y, grid_center, tile_rotated = hexa_layout(settings, pol_type)

    elif layout == "DIAMOND":
        cols, rows, offset_y, grid_center, tile_rotated = diamond_layout(settings, pol_type)

    elif layout == "RECTANGLE":
        cols, rows, offset_y, grid_center, tile_rotated = rect_layout(settings, pol_type)

    cx = grid_center[0] * dx if center else (-dx/2 if pol_type == 'SQUARE' else -dx*2/3)
    cy = grid_center[1] * dy if center else 0

    if pol_type == 'TRIANGLE':
        sin_base = sin(radians(30))
        x_offset = r * sin_base
        grid = [(x * dx - cx - x_offset * tile_rotated[x][y], y * dy - offset_y[x] * off_base - cy, tile_rotated[x][y]) for x in range(cols) for y in range(rows[x])]
    else:
        grid = [(x * dx - cx, y * dy - offset_y[x] * off_base - cy, 0) for x in range(cols) for y in range(rows[x])]

    angle = radians(a)
    cosa = cos(angle)
    sina = sin(angle)

    rotated_grid = [(x * cosa - y * sina, x * sina + y * cosa, rot) for x, y, rot in grid]

    return rotated_grid


def generate_tiles(tile_settings):

    radius, angle, scale, separate, grid_list, sides = tile_settings
    vert_grid_list, edge_grid_list, poly_grid_list = [[], [], []]

    local_angle = 45 if sides == 4 else 30

    tile = circle(radius*scale, radians(local_angle - angle), sides, None, 'pydata')

    for grid in grid_list:
        vert_list, edge_list, poly_list = [[], [], []]

        if sides == 3:
            tiles_triangular(vert_list, edge_list, poly_list, tile, grid)
        else:
            tiles(vert_list, edge_list, poly_list, tile, grid)

        if not separate:
            vert_list, edge_list, poly_list = mesh_join(vert_list, edge_list, poly_list)
            if scale == 1.0:
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


class SvPolygonGridNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Hexagonal, Triangular, Ortogonal,
    Tooltip: Create polygon array assambled to fill the plane. Triangles, Hexagons and Squares
    """
    bl_idname = 'SvPolygonGridNode'
    bl_label = 'Polygon Grid'
    sv_icon = 'SV_GRID'

    def update_layout(self, context):
        self.update_sockets()
        updateNode(self, context)

    gridType = EnumProperty(
        name="Type",
        description="Polygon Type",
        default="HEXAGON", items=grid_type_items,
        update=update_layout)

    gridLayout = EnumProperty(
        name="Layout",
        description="Polygon Layout",
        default="RECTANGLE", items=grid_layout_items,
        update=update_layout)

    sizeMode = EnumProperty(
        name="size_mode",
        description="Define tiles by",
        default="RADIUS", items=size_mode_items,
        update=update_layout)

    level = IntProperty(
        name="Level", description="Number of levels in non rectangular layouts",
        default=3, min=1, update=updateNode)

    numx = IntProperty(
        name="NumX", description="Number of points along X",
        default=7, min=1, update=updateNode)

    numy = IntProperty(
        name="NumY", description="Number of points along Y",
        default=6, min=1, update=updateNode)

    radius = FloatProperty(
        name="Size", description="Radius / Side of the grid tile",
        default=1.0, min=0.0, update=updateNode)

    angle = FloatProperty(
        name="Angle", description="Angle to rotate the grid and tiles",
        default=0.0, update=updateNode)

    scale = FloatProperty(
        name="Scale", description="Scale of the polygon tile",
        default=1.0, min=0.0, update=updateNode)

    center = BoolProperty(
        name="Center", description="Center grid around origin",
        default=True, update=updateNode)

    separate = BoolProperty(
        name="Separate", description="Separate tiles",
        default=False, update=updateNode)

    distanceName = "Radius"

    def sv_init(self, context):
        self.width = 170
        self.inputs.new('StringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('StringsSocket', "Angle").prop_name = 'angle'
        self.inputs.new('StringsSocket', "Level").prop_name = 'level'
        self.inputs.new('StringsSocket', "NumX").prop_name = 'numx'
        self.inputs.new('StringsSocket', "NumY").prop_name = 'numy'

        self.outputs.new('VerticesSocket', "Centers")
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")

        self.update_layout(context)

    def update_sockets(self):
        inputs = self.inputs
        named_sockets = ['NumX', 'NumY']


        if self.gridLayout == "RECTANGLE":
            if "Level" in inputs:
                inputs.remove(inputs["Level"])
            if "NumX" not in inputs:
                inputs.new("StringsSocket", "NumX").prop_name = "numx"
            if "NumY" not in inputs:
                inputs.new("StringsSocket", "NumY").prop_name = "numy"

        elif self.gridLayout in {"TRIANGLE", "DIAMOND", "HEXAGON"}:
            if "Level" not in inputs:
                inputs.new("StringsSocket", "Level").prop_name = "level"
            for socket_name in named_sockets:
                if socket_name in inputs:
                    inputs.remove(inputs[socket_name])

    def draw_buttons(self, context, layout):
        layout.prop(self, 'gridType', expand=False)
        layout.prop(self, 'gridLayout', expand=False)
        if self.gridType != "HEXAGON":
            layout.prop(self, 'sizeMode', expand=True)
        row = layout.row(align=True)
        row.prop(self, 'separate', toggle=True)
        row.prop(self, 'center', toggle=True)

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        if self.gridType == 'HEXAGON':
            sides = 6
        elif self.gridType == 'TRIANGLE':
            sides = 3
        elif self.gridType == 'SQUARE':
            sides = 4

        radius_factor = 2 * sin(radians(180/sides)) if self.gridType != 'HEXAGON' and self.sizeMode == 'SIDE' else 1

        # input values lists
        inputs = self.inputs
        input_level = inputs["Level"].sv_get()[0] if "Level" in inputs else [0]
        input_numx = inputs["NumX"].sv_get()[0] if "NumX" in inputs else [1]
        input_numy = inputs["NumY"].sv_get()[0] if "NumY" in inputs else [1]
        input_radius = inputs["Radius"].sv_get()[0]
        input_angle = inputs["Angle"].sv_get()[0]
        input_scale = inputs["Scale"].sv_get()[0]

        # sanitize the input values
        input_level = list(map(lambda x: max(1, x), input_level))
        input_numx = list(map(lambda x: max(1, x), input_numx))
        input_numy = list(map(lambda x: max(1, x), input_numy))
        input_radius = list(map(lambda x: max(0, x / radius_factor), input_radius))
        input_scale = list(map(lambda x: max(0, x), input_scale))

        # generate the vectorized grids
        param_list = []
        if self.gridLayout == 'RECTANGLE':
            param_list.extend([input_radius, input_angle, input_numx, input_numy])
        else:  # TRIANGLE, DIAMOND HEXAGON layouts
            param_list.extend([input_radius, input_angle, input_level])
        params = match_long_repeat(param_list)
        grid_list = [generate_grid(self.center, self.gridLayout, self.gridType, args) for args in zip(*params)]
        self.outputs['Centers'].sv_set([[(x, y, 0.0) for x, y, _ in grid_list[0]]])

        # generate the vectorized tiles only if any of VEP outputs are linked
        _, V, E, P = self.outputs[:]
        if not any(s.is_linked for s in [V, E, P]):
            return

        params = match_long_repeat([input_radius, input_angle, input_scale, grid_list])

        vert_list, edge_list, poly_list = [[], [], []]
        for r, a, s, grid in zip(*params):
            tile_settings = [r, a, s, self.separate, [grid], sides]

            verts, edges, polys = generate_tiles(tile_settings)
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
    bpy.utils.register_class(SvPolygonGridNode)


def unregister():
    bpy.utils.unregister_class(SvPolygonGridNode)
