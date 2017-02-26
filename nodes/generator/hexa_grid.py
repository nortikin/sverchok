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

from math import sin, cos, pi, sqrt, radians
from random import random
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.ui.sv_icons import custom_icon

DEBUG = False

gridTypeItems = [
    ("RECTANGLE", "Rectangle", "", custom_icon("SV_HEXA_GRID_RECTANGLE"), 0),
    ("DIAMOND", "Diamond", "", custom_icon("SV_HEXA_GRID_DIAMOND"), 1),
    ("TRIANGLE", "Triangle", "", custom_icon("SV_HEXA_GRID_TRIANGLE"), 2),
    ("HEXAGON", "Hexagon", "", custom_icon("SV_HEXA_GRID_HEXAGON"), 3)]


def get_hexagon_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    grid_values = []
    grid_x = 0
    grid_y = 0

    # 0 1 2 3 4 3 2 1 0
    num = level - 1
    numX = 2 * num + 1
    numY = list(map(lambda x: 2*num - abs(num - x) + 1, range(numX)))

    print(numX)
    print(numY)

    cx = level * r if center else 0
    # cy = level * dy if center else 0
    cy = 0

    for i in range(numX):
        grid_y = - (numY[i] - 1) * dy / 2
        for j in range(numY[i]):
            grid_values.append([grid_x - cx, grid_y - cy, 0])
            grid_y += dy

        grid_x += dx

    return grid_values


def get_diamond_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    grid_values = []
    grid_x = 0
    grid_y = 0

    # 0 1 2 3 4 3 2 1 0
    num = level - 1
    numX = 2 * num + 1
    numY = list(map(lambda x: num - abs(num - x) + 1, range(numX)))

    print(numX)
    print(numY)

    cx = num * dx if center else 0
    # cy = (numy - 1) * r  if center else 0
    cy = 0

    for i in range(numX):
        grid_y = - (numY[i] - 1) * dy / 2
        for j in range(numY[i]):
            grid_values.append([grid_x - cx, grid_y - cy, 0])
            grid_y += dy

        grid_x += dx

    return grid_values


def get_triangle_grid(r, level, center):
    dx = r * 3 / 2
    dy = r * sqrt(3)

    num = level
    cx = (num - 1) * r if center else 0
    # cy = (numy - 1) * r  if center else 0
    cy = 0

    grid_values = []
    grid_x = 0
    grid_y = 0

    for i in range(num):
        grid_y = -int((i + 1) / 2) * dy
        if (i % 2 != 0):
            grid_y += dy / 2
        for j in range(i + 1):
            grid_values.append([grid_x - cx, grid_y - cy, 0])
            grid_y += dy

        grid_x += dx

    return grid_values


def get_rectangle_grid(r, numx, numy, center):

    dx = r * 3 / 2
    dy = r * sqrt(3)

    cx = (numx - 1) * dx / 2 if center else 0
    cy = (numy - 1) * dy / 2 if center else 0

    grid_values = []
    grid_x = 0
    grid_y = 0

    for i in range(numx):
        if (i % 2 != 0):
            grid_y += dy / 2
        for j in range(numy):
            grid_values.append([grid_x - cx, grid_y - cy, 0])
            grid_y += dy

        grid_x += dx
        grid_y = 0

    return grid_values


class SvHexaGridNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Hexa Grid '''
    bl_idname = 'SvHexaGridNode'
    bl_label = 'Hexa Grid'
    sv_icon = 'SV_HEXA_GRID'

    def update_type(self, context):
        if self.gridType == "RECTANGLE":
            self.inputs["Level"].hide = True
            self.inputs["NumX"].hide = False
            self.inputs["NumY"].hide = False
        elif self.gridType == "TRIANGLE":
            self.inputs["Level"].hide = False
            self.inputs["NumX"].hide = True
            self.inputs["NumY"].hide = True
        elif self.gridType == "DIAMOND":
            self.inputs["Level"].hide = False
            self.inputs["NumX"].hide = True
            self.inputs["NumY"].hide = True
        elif self.gridType == "HEXAGON":
            self.inputs["Level"].hide = False
            self.inputs["NumX"].hide = True
            self.inputs["NumY"].hide = True

        updateNode(self, context)

    gridType = EnumProperty(
        name="Type",
        default="RECTANGLE", items=gridTypeItems,
        update=update_type)

    level = IntProperty(
        name="Level",
        default=3, min=1, soft_min=1,
        description="Number of levels",
        update=updateNode)

    numx = IntProperty(
        name="NumX",
        default=7, min=1, soft_min=1,
        description="Number of points along X",
        update=updateNode)

    numy = IntProperty(
        name="NumY",
        default=6, min=1, soft_min=1,
        description="Number of points along Y",
        update=updateNode)

    radius = FloatProperty(
        name="Radius",
        default=1.0, min=0.0, soft_min=0.0,
        description="Radius of the grid",
        update=updateNode)

    center = BoolProperty(
        name="Center",
        default=False,
        description="Center grid around origin",
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "Level").prop_name = 'level'
        self.inputs.new('StringsSocket', "NumX").prop_name = 'numx'
        self.inputs.new('StringsSocket', "NumY").prop_name = 'numy'
        self.inputs.new('StringsSocket', "Radius").prop_name = 'radius'

        self.outputs.new('VerticesSocket', "Grid")

        self.update_type(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'gridType', expand=False)
        layout.prop(self, 'center')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        gridType = next(x[-1] for x in gridTypeItems if x[0] == self.gridType)
        print("type: ", gridType)

        # input values lists
        input_level = self.inputs["Level"].sv_get()[0]
        input_numx = self.inputs["NumX"].sv_get()[0]
        input_numy = self.inputs["NumY"].sv_get()[0]
        input_radius = self.inputs["Radius"].sv_get()[0]

        # sanitize the input values
        input_level = list(map(lambda x: max(1, x), input_level))
        input_numx = list(map(lambda x: max(1, x), input_numx))
        input_numy = list(map(lambda x: max(1, x), input_numy))
        input_radius = list(map(lambda x: max(0, x), input_radius))

        if self.outputs['Grid'].is_linked:
            gridList = []

            if self.gridType == "DIAMOND":
                parameters = match_long_repeat([input_level, input_radius])
                for n, r in zip(*parameters):
                    grid = get_diamond_grid(r, n, self.center)
                    gridList.append(grid)

            elif self.gridType == "RECTANGLE":
                parameters = match_long_repeat(
                    [input_numx, input_numy, input_radius])
                for nx, ny, r in zip(*parameters):
                    grid = get_rectangle_grid(r, nx, ny, self.center)
                    gridList.append(grid)

            elif self.gridType == "TRIANGLE":
                parameters = match_long_repeat([input_level, input_radius])
                for n, r in zip(*parameters):
                    grid = get_triangle_grid(r, n, self.center)
                    gridList.append(grid)

            elif self.gridType == "HEXAGON":
                parameters = match_long_repeat([input_level, input_radius])
                for n, r in zip(*parameters):
                    grid = get_hexagon_grid(r, n, self.center)
                    gridList.append(grid)

            self.outputs['Grid'].sv_set(gridList)


def register():
    bpy.utils.register_class(SvHexaGridNode)


def unregister():
    bpy.utils.unregister_class(SvHexaGridNode)

if __name__ == '__main__':
    register()
