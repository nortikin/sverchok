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

import os
import glob
import json
from collections import OrderedDict
from pprint import pprint

from math import sin, cos, pi, sqrt, radians
from random import random
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.ui.sv_icons import custom_icon

DEBUG = False

directionItems = [
    ("EAST_NORTH", "East-North", "", custom_icon("SV_DIRECTION_EN"), 0),
    ("EAST_SOUTH", "East-South", "", custom_icon("SV_DIRECTION_ES"), 1),
    ("WEST_NORTH", "West-North", "", custom_icon("SV_DIRECTION_WN"), 2),
    ("WEST_SOUTH", "West-South", "", custom_icon("SV_DIRECTION_WS"), 3),
    ("NORTH_EAST", "North-East", "", custom_icon("SV_DIRECTION_NE"), 4),
    ("NORTH_WEST", "North-West", "", custom_icon("SV_DIRECTION_NW"), 5),
    ("SOUTH_EAST", "South-East", "", custom_icon("SV_DIRECTION_SE"), 6),
    ("SOUTH_WEST", "South-West", "", custom_icon("SV_DIRECTION_SW"), 7)]

# used for finding objects (empties) with icon name pattern: SV_ICON_NAME
def returnObjectByName(name=""):
    r = None
    obs = bpy.data.objects
    for ob in obs:
        if ob.name == name:
            r = ob
    return r


def read_icons_info(n=3):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, "../../iconList.json")
    print(os.getcwd())

    with open(file_path, encoding='utf-8') as data_file:
        data = json.load(data_file, object_pairs_hook=OrderedDict)

    numCategories = len(data.keys())
    numIconsInCategories = [len(x) for x in data.values()]

    print("There are %d categories: %s" % (numCategories, list(data.keys())))
    print("There are these number of icons in categories: ", numIconsInCategories)

    iconLocations = OrderedDict()

    y = 1
    nc = 0
    for category, nodes in data.items():
        nc = nc + 1
        # print("CATEGORY#%d: <%s> has %d nodes" % (nc, category, len(nodes.keys())))
        # print(type(nodes))
        # print("nodes: ", nodes)
        x = 0
        nn = 0
        for node, info in nodes.items():
            nn = nn + 1

            # print("xy: %d x %d" % (x+1, y+1))
            # print("NODE#%d: <%s> has icon ID: %s and rank: %d x %d - xy: %d x
            # %d" %  (nn, node, info, nc, nn, x+1, y+1))

            if x == n:
                x = 1
                y = y + 1
            else:
                x = x + 1

            iconLocations[info] = [x - 1, y - 1]

        print("")
        y = y + 1

    # pprint(iconLocations, indent=2)
    categories = list(data.keys())
    iconNames = list(iconLocations.keys())
    gridLocations = list(iconLocations.values())

    return categories, iconNames, gridLocations


def get_icon_grid_data(n, direction, scale, center):
    categories, names, locations = read_icons_info(n)

    # create a list of objects in the scene with names matching the icon names
    objects = []
    objLocs = []
    for name, location in zip(names, locations):
        obj = returnObjectByName(name)
        if obj:
            objects.append(obj)
            objLocs.append(location)

    # print(type(names))
    # print(type(xy))
    # print(categories)
    # print(names)
    # print(locations)
    maxX = max(x for x, y in locations) + 1
    maxY = max(y for x, y in locations) + 1
    # print("max x: ", maxX)
    # print("max y: ", maxY)

    gridLocs = [[x, y] for x in range(maxX) for y in range(maxY)]

    cellVecs = [(x * scale, y * scale, 0) for x, y in locations]
    gridVecs = [(x * scale, y * scale, 0) for x, y in gridLocs]
    objVecs = [(x * scale, y * scale, 0) for x, y in objLocs]

    # center the cells around origin
    if center:
        cx = 0.5 * (maxX-1) * scale
        cy = 0.5 * (maxY-1) * scale
        cellVecs = [(x-cx, y-cy, z) for x, y, z in cellVecs]
        gridVecs = [(x-cx, y-cy, z) for x, y, z in gridVecs]
        objVecs = [(x-cx, y-cy, z) for x, y, z in objVecs]

    # orient the cells based on given direction
    if direction == 0:  # east north (x, y)
        cellVecs = [(x, y, z) for x, y, z in cellVecs]
        gridVecs = [(x, y, z) for x, y, z in gridVecs]
        objVecs = [(x, y, z) for x, y, z in objVecs]

    if direction == 1:  # east south (x, -y)
        cellVecs = [(x, -y, z) for x, y, z in cellVecs]
        gridVecs = [(x, -y, z) for x, y, z in gridVecs]
        objVecs = [(x, -y, z) for x, y, z in objVecs]

    if direction == 2:  # west north (-x, y)
        cellVecs = [(-x, y, z) for x, y, z in cellVecs]
        gridVecs = [(-x, y, z) for x, y, z in gridVecs]
        objVecs = [(-x, y, z) for x, y, z in objVecs]

    if direction == 3:  # west south (-x, -y)
        cellVecs = [(-x, -y, z) for x, y, z in cellVecs]
        gridVecs = [(-x, -y, z) for x, y, z in gridVecs]
        objVecs = [(-x, -y, z) for x, y, z in objVecs]

    if direction == 4:  # north east (y, x)
        cellVecs = [(y, x, z) for x, y, z in cellVecs]
        gridVecs = [(y, x, z) for x, y, z in gridVecs]
        objVecs = [(y, x, z) for x, y, z in objVecs]

    if direction == 5:  # north west (-y, x)
        cellVecs = [(-y, x, z) for x, y, z in cellVecs]
        gridVecs = [(-y, x, z) for x, y, z in gridVecs]
        objVecs = [(-y, x, z) for x, y, z in objVecs]

    if direction == 6:  # south east (y, -x)
        cellVecs = [(y, -x, z) for x, y, z in cellVecs]
        gridVecs = [(y, -x, z) for x, y, z in gridVecs]
        objVecs = [(y, -x, z) for x, y, z in objVecs]

    if direction == 7:  # south west (-y, -x)
        cellVecs = [(-y, -x, z) for x, y, z in cellVecs]
        gridVecs = [(-y, -x, z) for x, y, z in gridVecs]
        objVecs = [(-y, -x, z) for x, y, z in objVecs]

    return categories, names, locations, gridLocs, cellVecs, gridVecs, objects, objVecs


class SvIconGridNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Icon Grid '''
    bl_idname = 'SvIconGridNode'
    bl_label = 'Icon Grid'
    sv_icon = 'SV_ICON_GRID'

    def update_direction(self, context):
        print(self.direction)
        updateNode(self, context)

    direction = EnumProperty(
        name="Direction",
        default="EAST_NORTH", items=directionItems,
        update=update_direction)

    wrap = IntProperty(
        name="Wrap",
        default=9,
        min=1, soft_min=1,
        description="Max number of cells before wrapping",
        update=updateNode)

    scale = FloatProperty(
        name="Scale Grid",
        default=2.0,
        min=1.0, soft_min=1.0,
        description="Spread the icon grid apart",
        update=updateNode)

    center = BoolProperty(
        name="Center",
        default=False,
        description="Center icon grid around origin",
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "Wrap").prop_name = 'wrap'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'

        self.outputs.new('StringsSocket', "Categories")
        self.outputs.new('StringsSocket', "Names")
        self.outputs.new('StringsSocket', "Cell Index")
        self.outputs.new('StringsSocket', "Grid Index")
        self.outputs.new('VerticesSocket', "Grid Vecs")
        self.outputs.new('VerticesSocket', "Cell Vecs")
        self.outputs.new('VerticesSocket', "Obj Vecs")
        self.outputs.new('StringsSocket', "Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction', expand=False)
        layout.prop(self, 'center')

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        direction = next(x[-1]
                         for x in directionItems if x[0] == self.direction)
        print("direction: ", direction)

        # input values lists
        input_wrap = self.inputs["Wrap"].sv_get()[0][0]
        input_scale = self.inputs["Scale"].sv_get()[0][0]

        # sanitize the input values
        input_wrap = max(input_wrap, 1)
        input_scale = max(input_scale, 1.0)

        categories, names, cellLocs, gridLocs, cellVecs, gridVecs, objects, objVecs = get_icon_grid_data(
            input_wrap, direction, input_scale, self.center)

        self.outputs['Categories'].sv_set(categories)
        self.outputs['Names'].sv_set([names])
        self.outputs['Cell Index'].sv_set(cellLocs)
        self.outputs['Grid Index'].sv_set(gridLocs)
        self.outputs['Cell Vecs'].sv_set([cellVecs])
        self.outputs['Grid Vecs'].sv_set([gridVecs])
        self.outputs['Obj Vecs'].sv_set([objVecs])
        self.outputs['Objects'].sv_set(objects)


def register():
    bpy.utils.register_class(SvIconGridNode)


def unregister():
    bpy.utils.unregister_class(SvIconGridNode)

if __name__ == '__main__':
    register()
