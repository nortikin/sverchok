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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty, StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat, update_edge_cache, get_edge_list
from sverchok.utils.sv_operator_mixins import SvGenericCallbackWithParams
from math import sqrt

modeItems = [
    ("AB",  "AB",  "Point A to Point B", 0),
    ("OD",  "OD",  "Origin O in direction D", 1)]

directions = {"X": [1, 0, 0], "Y": [0, 1, 0], "Z": [0, 0, 1]}

socket_names = {"A": "Point A", "B": "Point B", "O": "Origin", "D": "Distance"}


def get_vector_interpolator(ox, oy, oz, nx, ny, nz):
    ''' Get the optimal vector interpolator to speed up the line generation '''
    if nx == 0:
        if ny == 0:
            if nz == 0:
                return lambda l: (ox, oy, oz)
            else:
                return lambda l: (ox, oy, oz + l * nz)
        else:  # ny != 0
            if nz == 0:
                return lambda l: (ox, oy + l * ny, oz)
            else:
                return lambda l: (ox, oy + l * ny, oz + l * nz)
    else:  # nx != 0
        if ny == 0:
            if nz == 0:
                return lambda l: (ox + l * nx, oy, oz)
            else:
                return lambda l: (ox + l * nx, oy, oz + l * nz)
        else:  # ny != 0
            if nz == 0:
                return lambda l: (ox + l * nx, oy + l * ny, oz)
            else:
                return lambda l: (ox + l * nx, oy + l * ny, oz + l * nz)


def make_line(steps, size, v1, v2, center, normalize, mode):
    # get the scaled direction (based on mode, size & normalize)
    if mode == "AB":
        nx, ny, nz = [v2[0] - v1[0],  v2[1] - v1[1], v2[2] - v1[2]]
    else:  # mode == "OD":
        nx, ny, nz = v2

    stepsLength = sum(steps)  # length of the non-normalized steps

    if normalize:
        nn = sqrt(nx * nx + ny * ny + nz * nz)
        scale = 1 if nn == 0 else (1 / nn / stepsLength * size)  # scale to given size
    else:  # not normalized
        if mode == "AB":
            scale = 1 / stepsLength  # scale to AB vector size
        else:  # mode == "OD":
            nn = sqrt(nx * nx + ny * ny + nz * nz)
            scale = 1 if nn == 0 else (1 / nn)  # scale to steps size

    nx, ny, nz = [nx * scale, ny * scale, nz * scale]

    vec = get_vector_interpolator(v1[0], v1[1], v1[2], nx, ny, nz)

    verts = []
    add_vert = verts.append
    l = -stepsLength / 2 if center else 0
    for s in [0.0] + steps:
        l = l + s
        add_vert(vec(l))
    edges = get_edge_list(len(steps))

    return verts, edges


class SvLineNodeMK4(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Line, segment.
    Tooltip: Generate line between two points or from a point in a direction.
    """
    bl_idname = 'SvLineNodeMK4'
    bl_label = 'Line'
    bl_icon = 'GRIP'

    def update_sockets(self, context):
        ''' Swap V1/V2 input sockets to AB/OD based on selected mode '''
        for s, v in zip(self.inputs[-2:], self.mode):
            s.name = socket_names[v]
            s.prop_name = "point_" + v

        # keep the AB / OB props values synced when changing mode
        if self.mode == "AB":
            self.point_A = self.point_O
            self.point_B = self.point_D
        else:
            self.point_O = self.point_A
            self.point_D = self.point_B

    def set_direction(self, operator):
        self.direction = operator.direction
        self.mode = "OD"
        return {'FINISHED'}

    def update_normalize(self, context):
        self.inputs["Size"].hide_safe = not self.normalize
        updateNode(self, context)

    def update_xyz_direction(self, context):
        self.point_O = [0, 0, 0]
        self.point_D = directions[self.direction]

    def update_mode(self, context):
        if self.mode == self.last_mode:
            return

        self.last_mode = self.mode
        self.update_sockets(context)
        updateNode(self, context)

    direction = StringProperty(
        name="Direction", default="X", update=update_xyz_direction)

    mode = EnumProperty(
        name="Mode", items=modeItems, default="OD", update=update_mode)

    last_mode = EnumProperty(
        name="Last Mode", items=modeItems, default="OD")

    num = IntProperty(
        name="Num Verts", description="Number of Vertices",
        default=2, min=2, update=updateNode)

    step = FloatProperty(
        name="Step", description="Step length",
        default=1.0, update=updateNode)

    center = BoolProperty(
        name="Center", description="Center the line",
        default=False, update=updateNode)

    normalize = BoolProperty(
        name="Normalize", description="Normalize line to size",
        default=False, update=update_normalize)

    size = FloatProperty(
        name="Size", description="Size of the normalized line",
        default=10.0, update=updateNode)

    point_A = FloatVectorProperty(
        name="Point A", description="Line's starting point",
        size=3, default=(0, 0, 0), update=updateNode)

    point_B = FloatVectorProperty(
        name="Point B", description="Line's ending point",
        size=3, default=(1, 0, 0), update=updateNode)

    point_O = FloatVectorProperty(
        name="Origin", description="Line's origin",
        size=3, default=(0, 0, 0), update=updateNode)

    point_D = FloatVectorProperty(
        name="Direction", description="Line's direction",
        size=3, default=(1, 0, 0), update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Num").prop_name = 'num'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step'
        size_socket = self.inputs.new('StringsSocket', "Size")
        size_socket.prop_name = 'size'
        size_socket.hide_safe = True
        self.inputs.new('VerticesSocket', "Origin").prop_name = "point_O"
        self.inputs.new('VerticesSocket', "Direction").prop_name = "point_D"
        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")

    def draw_buttons(self, context, layout):
        col = layout.column(align=False)

        if not self.inputs[-1].is_linked:
            row = col.row(align=True)
            for direction in "XYZ":
                op = row.operator("node.set_line_direction", text=direction)
                op.direction = direction

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "mode", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        inputs = self.inputs
        input_num = inputs["Num"].sv_get()
        input_step = inputs["Step"].sv_get()
        input_size = inputs["Size"].sv_get()[0]
        input_V1 = inputs[-2].sv_get()[0]
        input_V2 = inputs[-1].sv_get()[0]

        maxNum = 0
        params = match_long_repeat([input_num, input_step])
        stepsList = []
        for num, steps in zip(*params):
            for nn in num:
                nn = max(2, nn)
                maxNum = max(nn, maxNum)
                steps = steps[:nn - 1]  # shorten step list if needed
                fullList(steps, nn - 1)  # extend step list if needed
                stepsList.append(steps)

        update_edge_cache(maxNum)  # help the edge generator get faster

        c, n, m = [self.center, self.normalize, self.mode]
        params = match_long_repeat([stepsList, input_size, input_V1, input_V2])
        vertList, edgeList = [], []
        for steps, size, v1, v2 in zip(*params):
            verts, edges = make_line(steps, size, v1, v2, c, n, m)
            vertList.append(verts)
            edgeList.append(edges)

        if self.outputs['Verts'].is_linked:
            self.outputs['Verts'].sv_set(vertList)
        if self.outputs['Edges'].is_linked:
            self.outputs['Edges'].sv_set(edgeList)


class SvSetLineDirection(bpy.types.Operator, SvGenericCallbackWithParams):
    bl_label = "Set line direction"
    bl_idname = "node.set_line_direction"   # dont use sv.
    bl_description = "Set the direction of the line along X, Y or Z"

    direction = StringProperty(default="X")
    fn_name = StringProperty(default="set_direction")


def register():
    bpy.utils.register_class(SvSetLineDirection)
    bpy.utils.register_class(SvLineNodeMK4)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK4)
    bpy.utils.unregister_class(SvSetLineDirection)
