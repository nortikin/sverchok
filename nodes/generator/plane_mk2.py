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
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
import time

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat

from mathutils import Vector

directionItems = [("XY", "XY", ""), ("YZ", "YZ", ""), ("ZX", "ZX", "")]


def make_plane2(stepsx, stepsy, center, direction, separate):
    startTime = time.time()
    if direction == "XY":
        v = lambda l, k: (l, k, 0.0)
    elif direction == "YZ":
        v = lambda l, k: (0.0, l, k)
    elif direction == "ZX":
        v = lambda l, k: (k, 0.0, l)

    cx = - sum(stepsx) / 2 if center else 0
    cy = - sum(stepsy) / 2 if center else 0
    verts = []
    addVert = verts.append
    y = cy
    for sy in [0.0] + stepsy:
        y = y + sy
        x = cx
        for sx in [0.0] + stepsx:
            x = x + sx
            addVert(v(x, y))

    endTime1 = time.time()
    print("Plane MK2 make_plane vertgen: ", endTime1 - startTime)



    edges = []
    addEdge = edges.append
    nx = len(stepsx) + 1
    ny = len(stepsy) + 1
    for j in range(ny):
        for i in range(nx - 1):
            i1 = i + j * nx
            i2 = i + j * nx + 1
            addEdge([i1, i2])

    for i in range(nx):
        for j in range(ny - 1):
            i1 = i + j * nx
            i2 = i + (j + 1) * nx
            addEdge([i1, i2])

    endTime2 = time.time()
    print("Plane MK2 make_plane edgegen: ", endTime2 - endTime1)

    polys = []
    addPoly = polys.append
    for i in range(nx - 1):
        for j in range(ny - 1):
            i1 = i + j * nx
            i2 = i + j * nx + 1
            i3 = i + (j + 1) * nx + 1
            i4 = i + (j + 1) * nx
            addPoly([i1, i2, i3, i4])

    return verts, edges, polys


def make_plane(int_x, int_y, step_x, step_y, separate, center):
    vertices = [(0.0, 0.0, 0.0)]
    vertices_S = []
    int_x = [int(int_x) if type(int_x) is not list else int(int_x[0])]
    int_y = [int(int_y) if type(int_y) is not list else int(int_y[0])]

    # center the grid: offset the starting point of the grid by half its size
    if center:
        Nnx = int_x[0] - 1   # number of steps based on the number of X vertices
        Nsx = len(step_x)  # number of steps given by the X step list

        Nny = int_y[0] - 1   # number of steps based on the number of Y vertices
        Nsy = len(step_y)  # number of steps given by the Y step list

        # grid size along X (step list & repeated last step if any)
        sizeX1 = sum(step_x[:min(Nnx, Nsx)])          # step list size
        sizeX2 = max(0, (Nnx - Nsx)) * step_x[Nsx - 1]  # repeated last step size
        sizeX = sizeX1 + sizeX2                       # total size

        # grid size along Y (step list & repeated last step if any)
        sizeY1 = sum(step_y[:min(Nny, Nsy)])          # step list size
        sizeY2 = max(0, (Nny - Nsy)) * step_y[Nsy - 1]  # repeated last step size
        sizeY = sizeY1 + sizeY2                       # total size

        # starting point of the grid offset by half its size in both directions
        vertices = [(-0.5 * sizeX, -0.5 * sizeY, 0.0)]

    if type(step_x) is not list:
        step_x = [step_x]
    if type(step_y) is not list:
        step_y = [step_y]
    fullList(step_x, int_x[0])
    fullList(step_y, int_y[0])

    for i in range(int_x[0] - 1):
        v = Vector(vertices[i]) + Vector((step_x[i], 0.0, 0.0))
        vertices.append(v[:])

    a = [int_y[0] if separate else int_y[0] - 1]
    for i in range(a[0]):
        out = []
        for j in range(int_x[0]):
            out.append(vertices[j + int_x[0] * i])
        for j in out:
            v = Vector(j) + Vector((0.0, step_y[i], 0.0))
            vertices.append(v[:])
        if separate:
            vertices_S.append(out)

    edges = []
    edges_S = []
    for i in range(int_y[0]):
        for j in range(int_x[0] - 1):
            edges.append((int_x[0] * i + j, int_x[0] * i + j + 1))

    if separate:
        out = []
        for i in range(int_x[0] - 1):
            out.append(edges[i])
        edges_S.append(out)
        for i in range(int_y[0] - 1):
            edges_S.append(edges_S[0])
    else:
        for i in range(int_x[0]):
            for j in range(int_y[0] - 1):
                edges.append((int_x[0] * j + i, int_x[0] * j + i + int_x[0]))

    polygons = []
    for i in range(int_x[0] - 1):
        for j in range(int_y[0] - 1):
            polygons.append((int_x[0] * j + i, int_x[0] * j + i + 1, int_x[0] *
                             j + i + int_x[0] + 1, int_x[0] * j + i + int_x[0]))

    if separate:
        return vertices_S, edges_S, []
    else:
        return vertices, edges, polygons


class SvPlaneNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Plane MK2 '''
    bl_idname = 'SvPlaneNodeMK2'
    bl_label = 'Plane MK2'
    bl_icon = 'MESH_PLANE'

    direction = EnumProperty(name="Direction",
                             default="XY", items=directionItems,
                             update=updateNode)

    numx = IntProperty(name='N Vert X', description='Nº Vertices X',
                       default=2, min=2, update=updateNode)

    numy = IntProperty(name='N Vert Y', description='Nº Vertices Y',
                       default=2, min=2, update=updateNode)

    stepx = FloatProperty(name='Step X', description='Step length X',
                          default=1.0, update=updateNode)

    stepy = FloatProperty(name='Step Y', description='Step length Y',
                          default=1.0, update=updateNode)

    separate = BoolProperty(name='Separate', description='Separate UV coords',
                            default=False, update=updateNode)

    center = BoolProperty(name='Center', description='Center the grid',
                          default=False, update=updateNode)

    normalize = BoolProperty(name='Normalize', description='Normalize',
                             default=False, update=updateNode)

    sizex = FloatProperty(name='Size X', description='Size of plane along X',
                          default=10.0, update=updateNode)

    sizey = FloatProperty(name='Size Y', description='Size of plane along Y',
                          default=10.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Num X").prop_name = 'numx'
        self.inputs.new('StringsSocket', "Num Y").prop_name = 'numy'
        self.inputs.new('StringsSocket', "Step X").prop_name = 'stepx'
        self.inputs.new('StringsSocket', "Step Y").prop_name = 'stepy'

        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")

    def draw_buttons(self, context, layout):
        layout.prop(self, "separate")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)
        if self.normalize:
            row = col.row(align=True)
            row.prop(self, "sizex")
            row.prop(self, "sizey")

    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        startTime = time.time()

        inputs = self.inputs
        outputs = self.outputs

        input_numx = inputs["Num X"].sv_get()
        input_numy = inputs["Num Y"].sv_get()
        input_stepx = inputs["Step X"].sv_get()
        input_stepy = inputs["Step Y"].sv_get()

        params = match_long_repeat([input_numx, input_numy, input_stepx, input_stepy])

        endTime1 = time.time()
        print("Plane MK2 paramgen: ", endTime1 - startTime)

        stepListx, stepListy = [[], []]
        for nx, ny, sx, sy in zip(*params):
            numx, numy = [max(2, nx[0]), max(2, ny[0])]  # sanitize the input
            # adjust the step list based on number of verts and steps
            stepsx, stepsy = [sx[:(numx - 1)], sy[:(numy - 1)]]  # shorten if needed
            fullList(stepsx, numx - 1)  # extend if needed
            fullList(stepsy, numy - 1)  # extend if needed
            if self.normalize:
                sizex, sizey = [self.sizex / sum(stepsx), self.sizey / sum(stepsy)]
                stepsx = [sx * sizex for sx in stepsx]
                stepsy = [sy * sizey for sy in stepsy]
            stepListx.append(stepsx)
            stepListy.append(stepsy)

        endTime2 = time.time()
        print("Plane MK2 stepgen: ", endTime2 - endTime1)

        c, d, s = self.center, self.direction, self.separate
        planes = [make_plane2(sx, sy, c, d, s) for sx, sy in zip(stepListx, stepListy)]
        verts, edges, polys = [vep for vep in zip(*planes)]

        endTime3 = time.time()
        print("Plane MK2 meshgen: ", endTime3 - endTime2)

        # outputs
        if outputs['Vertices'].is_linked:
            outputs['Vertices'].sv_set(verts)

        if outputs['Edges'].is_linked:
            outputs['Edges'].sv_set(edges)

        if outputs['Polygons'].is_linked:
            outputs['Polygons'].sv_set(polys)

        endTime = time.time()
        print("Plane MK2 Computing Time: ", endTime - startTime)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvPlaneNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvPlaneNodeMK2)
