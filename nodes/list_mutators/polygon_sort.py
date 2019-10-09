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
from bpy.props import BoolProperty, EnumProperty, FloatVectorProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams
from mathutils import Vector
from math import acos, pi, sqrt

modeItems = [
    ("P", "Point", "Sort by distance to a point", 0),
    ("D", "Direction", "Sort by projection along a direction", 1),
    ("A", "Area", "Sort by surface area", 2),
    ("NP", "Normal Angle Point", "Sort by normal angle to point", 3),
    ("ND", "Normal Angle Direction", "Sort by normal angle to direction", 4)]

directions = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}

socket_names = {"P": "Point", "D": "Direction", "A": "Area", "NP": "Normal", "ND": "Normal"}
socket_props = {"P": "point_P", "D": "point_D", "A": "point_D", "NP": "point_P", "ND": "point_D"}

quantity_names = {"P": "Distances", "D": "Distances", "A": "Areas", "NP": "Angles", "ND": "Angles"}


def polygon_normal(verts, poly):
    ''' The normal of the given polygon '''
    v1 = Vector(verts[poly[0]])
    v2 = Vector(verts[poly[1]])
    v3 = Vector(verts[poly[2]])
    v12 = v2 - v1
    v23 = v3 - v2
    normal = v12.cross(v23)
    normal.normalize()

    return list(normal)


def polygon_area(verts, poly):
    ''' The area of the given polygon '''
    if len(poly) < 3:  # not a plane - no area
        return 0

    total = Vector([0, 0, 0])
    N = len(poly)
    for i in range(N):
        vi1 = Vector(verts[poly[i]])
        vi2 = Vector(verts[poly[(i + 1) % N]])
        prod = vi1.cross(vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]

    normal = Vector(polygon_normal(verts, poly))
    area = abs(total.dot(normal)) / 2

    return area


def polygon_center(verts, poly):
    ''' The center of the given polygon '''
    vx = 0
    vy = 0
    vz = 0
    for v in poly:
        vx = vx + verts[v][0]
        vy = vy + verts[v][1]
        vz = vz + verts[v][2]
    n = len(poly)
    vx = vx / n
    vy = vy / n
    vz = vz / n

    return [vx, vy, vz]


def polygon_distance_P(verts, poly, P):
    ''' The distance from the center of the polygon to the given point '''
    C = polygon_center(verts, poly)
    CP = [C[0] - P[0], C[1] - P[1], C[2] - P[2]]
    distance = sqrt(CP[0] * CP[0] + CP[1] * CP[1] + CP[2] * CP[2])

    return distance


def polygon_distance_D(verts, poly, D):
    ''' The projection of the polygon center vector along the given direction '''
    C = polygon_center(verts, poly)
    distance = C[0] * D[0] + C[1] * D[1] + C[2] * D[2]

    return distance


def polygon_normal_angle_P(verts, poly, P):
    ''' The angle between the polygon normal and the vector from polygon center to given point '''
    N = polygon_normal(verts, poly)
    C = polygon_center(verts, poly)
    V = [P[0] - C[0], P[1] - C[1], P[2] - C[2]]
    v1 = Vector(N)
    v2 = Vector(V)
    v1.normalize()
    v2.normalize()
    angle = acos(v1.dot(v2)) # the angle in radians

    return angle


def polygon_normal_angle_D(verts, poly, D):
    ''' The angle between the polygon normal and the given direction '''
    N = polygon_normal(verts, poly)
    v1 = Vector(N)
    v2 = Vector(D)
    v1.normalize()
    v2.normalize()
    angle = acos(v1.dot(v2)) # the angle in radians

    return angle


class SvPolygonSortNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Polygon, Sorting
    Tooltip: Sort the polygons by various criteria: distance, angle, area.
    """
    bl_idname = 'SvPolygonSortNode'
    bl_label = 'Polygon Sort'

    def sort_polygons(self, verts, polys, V):
        ''' Sort polygons and return sorted polygons indices, poly & quantities '''

        if self.mode == "D":
            quantities = [polygon_distance_D(verts, poly, V) for poly in polys]
        elif self.mode == "P":
            quantities = [polygon_distance_P(verts, poly, V) for poly in polys]
        elif self.mode == "A":
            quantities = [polygon_area(verts, poly) for poly in polys]
        elif self.mode == "NP":
            quantities = [polygon_normal_angle_P(verts, poly, V) for poly in polys]
        elif self.mode == "ND":
            quantities = [polygon_normal_angle_D(verts, poly, V) for poly in polys]

        IQ = [(i, q) for i, q in enumerate(quantities)]
        sortedIQs = sorted(IQ, key=lambda kv: kv[1], reverse=self.descending)

        sortedIndices = [IQ[0] for IQ in sortedIQs]
        sortedQuantities = [IQ[1] for IQ in sortedIQs]
        sortedPolys = [polys[i] for i in sortedIndices]

        return sortedIndices, sortedPolys, sortedQuantities

    def update_sockets(self, context):
        ''' Swap sorting vector input socket to P/D based on selected mode '''

        s = self.inputs[-1]
        s.name = socket_names[self.mode]
        s.prop_name = socket_props[self.mode]

        # keep the P/D props values synced when changing mode
        if self.mode == "P":
            self.point_P = self.point_D
        else:  # self.mode == "D"
            self.point_D = self.point_P

        # update output "Quantities" socket with proper name for the mode
        o = self.outputs[-1]
        o.name = quantity_names[self.mode]

    def set_direction(self, operator):
        self.direction = operator.direction
        self.mode = "D"
        return {'FINISHED'}

    def update_xyz_direction(self, context):
        self.point_D = directions[self.direction]

    def update_mode(self, context):
        if self.mode == self.last_mode:
            return

        self.last_mode = self.mode
        self.update_sockets(context)
        updateNode(self, context)

    direction : StringProperty(
        name="Direction", default="X", update=update_xyz_direction)

    mode : EnumProperty(
        name="Mode", items=modeItems, default="D", update=update_mode)

    last_mode : EnumProperty(
        name="Last Mode", items=modeItems, default="D")

    point_P : FloatVectorProperty(
        name="Point P", description="Reference point for distance and angle calculation",
        size=3, default=(1, 0, 0), update=updateNode)

    point_D : FloatVectorProperty(
        name="Direction", description="Reference direction for projection and angle calculation",
        size=3, default=(1, 0, 0), update=updateNode)

    descending : BoolProperty(
        name="Descending", description="Sort in the descending order",
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Verts")
        self.inputs.new('SvStringsSocket', "Polys")
        self.inputs.new('SvVerticesSocket', "Direction").prop_name = "point_D"
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")
        self.outputs.new('SvStringsSocket', "Indices")
        self.outputs.new('SvStringsSocket', "Distances")

    def draw_buttons(self, context, layout):
        col = layout.column(align=False)

        if not self.inputs[-1].is_linked:
            row = col.row(align=True)
            for direction in "XYZ":
                op = row.operator("node.set_sort_direction", text=direction)
                op.direction = direction

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=False, text="")
        layout.prop(self, "descending")

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs
        input_v = inputs["Verts"].sv_get()
        input_p = inputs["Polys"].sv_get()
        input_r = inputs[-1].sv_get()[0]  # reference: direction or point

        params = match_long_repeat([input_v, input_p, input_r])

        iList, vList, pList, qList = [], [], [], []
        for v, p, r in zip(*params):
            indices, polys, quantities = self.sort_polygons(v, p, r)
            iList.append(indices)
            vList.append(v)
            pList.append(polys)
            qList.append(quantities)

        if self.outputs['Vertices'].is_linked:
            self.outputs['Vertices'].sv_set(vList)
        if self.outputs['Polygons'].is_linked:
            self.outputs['Polygons'].sv_set(pList)
        if self.outputs['Indices'].is_linked:
            self.outputs['Indices'].sv_set(iList)
        if self.outputs[-1].is_linked:
            self.outputs[-1].sv_set(qList) # sorting quantities


class SvSetSortDirection(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_label = "Set sort direction"
    bl_idname = "node.set_sort_direction"
    bl_description = "Set the sorting direction along X, Y or Z"

    direction : StringProperty(default="X")
    fn_name : StringProperty(default="set_direction")


def register():
    bpy.utils.register_class(SvSetSortDirection)
    bpy.utils.register_class(SvPolygonSortNode)


def unregister():
    bpy.utils.unregister_class(SvPolygonSortNode)
    bpy.utils.unregister_class(SvSetSortDirection)
