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

from math import sqrt, radians

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, updateNode, match_long_repeat
from sverchok.nodes.transforms.rotation import euler_rotation
from mathutils import Vector
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.geom import circle
from sverchok.utils.sv_mesh_utils import mesh_join

DEBUG = False

gridTypeItems = [
    ("RECTANGLE", "Rectangle", "", custom_icon("SV_HEXA_GRID_RECTANGLE"), 0),
    ("TRIANGLE", "Triangle", "", custom_icon("SV_HEXA_GRID_TRIANGLE"), 1),
    ("DIAMOND", "Diamond", "", custom_icon("SV_HEXA_GRID_DIAMOND"), 2),
    ("HEXAGON", "Hexagon", "", custom_icon("SV_HEXA_GRID_HEXAGON"), 3)]


def get_hexagon_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    num = level - 1
    numX = 2 * num + 1
    numY = list(map(lambda x: 2 * num - abs(num - x) + 1, range(numX)))

    cx = num * dx if center else 0
    cy = num * dy / 2 if center else 0

    grid_values = []
    grid_x = 0.0
    grid_y = 0.0

    for i in range(numX):
        grid_y = - (numY[i] - numY[0]) * dy / 2
        for j in range(numY[i]):
            grid_values.append((grid_x - cx, grid_y - cy, 0.0))
            grid_y += dy

        grid_x += dx

    return grid_values


def get_diamond_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    num = level - 1
    numX = 2 * num + 1
    numY = list(map(lambda x: num - abs(num - x) + 1, range(numX)))

    cx = num * dx if center else 0
    cy = 0.0

    grid_values = []
    grid_x = 0.0
    grid_y = 0.0

    for i in range(numX):
        grid_y = - (numY[i] - 1) * dy / 2
        for j in range(numY[i]):
            grid_values.append((grid_x - cx, grid_y - cy, 0.0))
            grid_y += dy

        grid_x += dx

    return grid_values


def get_triangle_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    num = level

    cx = (num - 1) * r if center else 0
    cy = 0.0

    grid_values = []
    grid_x = 0.0
    grid_y = 0.0

    for i in range(num):
        grid_y = -int((i + 1) / 2) * dy
        grid_y += dy / 2 if (i % 2 != 0) else 0
        for j in range(i + 1):
            grid_values.append((grid_x - cx, grid_y - cy, 0.0))
            grid_y += dy

        grid_x += dx

    return grid_values


def get_rectangle_grid(r, numx, numy, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    cx = (numx - 1) * dx / 2 if center else 0
    cy = (numy - 1.0 + 0.5 * (numx > 1)) * dy / 2 if center else 0

    grid_values = []
    grid_x = 0.0
    grid_y = 0.0

    for i in range(numx):
        grid_y = dy / 2 if (i % 2 != 0) else 0
        for j in range(numy):
            grid_values.append((grid_x - cx, grid_y - cy, 0.0))
            grid_y += dy

        grid_x += dx

    return grid_values


def generate_tiles(radius, angle, join, gridList):
    verts, edges, polys = circle(radius, radians(angle), 6, None, 'pydata')

    # print("tiles gridList:", gridList)
    vertList2 = []
    edgeList2 = []
    polyList2 = []
    for grid in gridList:
        # print("next grid:", grid)
        vertList = []
        edgeList = []
        polyList = []
        for cx, cy, _ in grid:
            # print("coords cx,cy = ", cx, cy)
            verts2 = [(x + cx, y + cy, 0.0) for x, y, _ in verts]
            vertList.append(verts2)
            edgeList.append(edges)
            polyList.append(polys)
        if join:
            vertList, edgeList, polyList = mesh_join(vertList, edgeList, polyList)
        vertList2.append(vertList)
        edgeList2.append(edgeList)
        polyList2.append(polyList)
        # vertList, edgeList, polyList = [vertList], [edgeList], [polyList]

    # if join:
    #     vertList, edgeList, polyList = mesh_join(vertList, edgeList, polyList)
    #     vertList, edgeList, polyList = [vertList], [edgeList], [polyList]

    return vertList2, edgeList2, polyList2


class SvHexaGridNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Hexa Grid '''
    bl_idname = 'SvHexaGridNode'
    bl_label = 'Hexa Grid'
    sv_icon = 'SV_HEXA_GRID'

    def update_type(self, context):
        self.update_sockets()
        updateNode(self, context)

    gridType = EnumProperty(
        name="Type",
        default="RECTANGLE", items=gridTypeItems,
        update=update_type)

    level = IntProperty(
        name="Level", description="Number of levels in non rectangular patterns",
        default=3, min=1, soft_min=1,
        update=updateNode)

    numx = IntProperty(
        name="NumX", description="Number of points along X",
        default=7, min=1, soft_min=1,
        update=updateNode)

    numy = IntProperty(
        name="NumY", description="Number of points along Y",
        default=6, min=1, soft_min=1,
        update=updateNode)

    radius = FloatProperty(
        name="Radius", description="Radius of the grid tile",
        default=1.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle = FloatProperty(
        name="Angle", description="Angle to rotate the grid and tiles",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    scale = FloatProperty(
        name="Scale", description="Scale of the polygon tile",
        default=1.0, min=0.0, soft_min=0.0,
        update=updateNode)

    center = BoolProperty(
        name="Center", description="Center grid around origin",
        default=True,
        update=updateNode)

    join = BoolProperty(
        name="Join", description="Join meshes into one",
        default=False,
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "Level").prop_name = 'level'
        self.inputs.new('StringsSocket', "NumX").prop_name = 'numx'
        self.inputs.new('StringsSocket', "NumY").prop_name = 'numy'
        self.inputs.new('StringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('StringsSocket', "Angle").prop_name = 'angle'

        self.outputs.new('VerticesSocket', "Centers")
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")

        self.update_type(context)

    def update_sockets(self):
        inputs = self.inputs
        named_sockets = ['NumX', 'NumY']

        if self.gridType == "RECTANGLE":
            if "Level" in inputs:
                inputs.remove(inputs["Level"])
            if not "NumX" in inputs:
                inputs.new("StringsSocket", "NumX").prop_name = "numx"
            if not "NumY" in inputs:
                inputs.new("StringsSocket", "NumY").prop_name = "numy"

        elif self.gridType in {"TRIANGLE", "DIAMOND", "HEXAGON"}:
            if not "Level" in inputs:
                inputs.new("StringsSocket", "Level").prop_name = "level"
            for socket_name in named_sockets:
                if socket_name in inputs:
                    inputs.remove(inputs[socket_name])

    def draw_buttons(self, context, layout):
        layout.prop(self, 'gridType', expand=False)
        row = layout.row(align=True)
        row.prop(self, 'join')
        row.prop(self, 'center')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists
        inputs = self.inputs
        input_level = inputs["Level"].sv_get()[0] if "Level" in inputs else [0]
        input_numx = inputs["NumX"].sv_get()[0] if "NumX" in inputs else [1]
        input_numy = inputs["NumY"].sv_get()[0] if "NumY" in inputs else [1]
        input_radius = inputs["Radius"].sv_get()[0]
        input_scale = inputs["Scale"].sv_get()[0]

        # sanitize the input values
        input_level = list(map(lambda x: max(1, x), input_level))
        input_numx = list(map(lambda x: max(1, x), input_numx))
        input_numy = list(map(lambda x: max(1, x), input_numy))
        input_radius = list(map(lambda x: max(0, x), input_radius))
        input_scale = list(map(lambda x: max(0, x), input_scale))

        gridList = []

        if self.gridType == "RECTANGLE":
            parameters = match_long_repeat([input_numx, input_numy, input_radius])
            for nx, ny, r in zip(*parameters):
                grid = get_rectangle_grid(r, nx, ny, self.center)
                gridList.append(grid)

        elif self.gridType == "TRIANGLE":
            parameters = match_long_repeat([input_level, input_radius])
            for n, r in zip(*parameters):
                grid = get_triangle_grid(r, n, self.center)
                gridList.append(grid)

        if self.gridType == "DIAMOND":
            parameters = match_long_repeat([input_level, input_radius])
            print("diamond params: ", *parameters)
            for n, r in zip(*parameters):
                grid = get_diamond_grid(r, n, self.center)
                gridList.append(grid)

        elif self.gridType == "HEXAGON":
            parameters = match_long_repeat([input_level, input_radius])
            for n, r in zip(*parameters):
                grid = get_hexagon_grid(r, n, self.center)
                gridList.append(grid)

        self.outputs['Centers'].sv_set(gridList)

        # print("Levels: ", input_level)
        # print("gridList: ", gridList)
        radius = self.radius * self.scale
        verts = []
        edges = []
        polys = []
        if self.outputs['Vertices'].is_linked or self.outputs['Edges'].is_linked or self.outputs['Polygons'].is_linked:
            # print("grid list len ", len(gridList))
            vertList = []
            edgeList = []
            polyList = []
            param2 = match_long_repeat([input_radius, input_scale, gridList])
            for r, s, grid in zip(*param2):
                # print("vectorized grid: ", grid)
                radius = r * s
                verts, edges, polys = generate_tiles(radius, self.angle, self.join, [grid])
                vertList.append(verts)
                edgeList.append(edges)
                polyList.append(polys)
            verts = vertList
            edges = edgeList
            polys = polyList

        self.outputs['Vertices'].sv_set(verts)
        self.outputs['Edges'].sv_set(edges)
        self.outputs['Polygons'].sv_set(polys)


def register():
    bpy.utils.register_class(SvHexaGridNode)


def unregister():
    bpy.utils.unregister_class(SvHexaGridNode)

if __name__ == '__main__':
    register()
