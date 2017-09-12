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
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
import itertools

# dictionary to store once the unit/untransformed hypercube verts, edges & polys
_hypercube = {}

angleTypes = [
    ("RAD", "Radians", "", 0),
    ("DEG", "Degrees", "", 1),
    ("NORM", "Normalized", "", 2)]


def flip(n, v):
    return [(v[i]+1)%2 if i==n else v[i] for i in range(len(v))]

def flipper(v):
    links = []
    for n in range(len(v)):
        links.append(flip(n, v))
    return links

def edges(v):
    return list(itertools.product([v], flipper(v)))

def edgesIDs(v):
    es = edges(v)
    return [ [cube.index(v1), cube.index(v2)] for v1, v2 in es ]


def create_cells():
    cells = []
    indices = []
    for i in [0, 1]:
        cell = [ [i, j, k, l] for j in [0,1] for k in [0,1] for l in [0,1] ]
        cells.append(cell)
        index = [ (i<<3) + (j<<2) + (k<<1) + l for j in [0,1] for k in [0,1] for l in [0,1] ]
        indices.append(index)
    for j in [0, 1]:
        cell = [ [i, j, k, l] for i in [0,1] for k in [0,1] for l in [0,1] ]
        cells.append(cell)
        index = [ (i<<3) + (j<<2) + (k<<1) + l for i in [0,1] for k in [0,1] for l in [0,1] ]
        indices.append(index)
    for k in [0, 1]:
        cell = [ [i, j, k, l] for i in [0,1] for j in [0,1] for l in [0,1] ]
        cells.append(cell)
        index = [ (i<<3) + (j<<2) + (k<<1) + l for i in [0,1] for j in [0,1] for l in [0,1] ]
        indices.append(index)
    for l in [0, 1]:
        cell = [ [i, j, k, l] for i in [0,1] for j in [0,1] for k in [0,1] ]
        cells.append(cell)
        index = [ (i<<3) + (j<<2) + (k<<1) + l for i in [0,1] for j in [0,1] for k in [0,1] ]
        indices.append(index)

    return cells, indices

def project(vert4D, d):
    '''
        Project a 4D vector onto 3D space.
    '''
    cx, cy, cz = [0.0, 0.0, 0.0]  # center
    # cx, cy, cz = [0.5, 0.5, 0.5]  # center
    x, y, z, t = vert4D
    return [x + (cx - x)*t/d, y + (cy - y)*t/d, z + (cz - z)*t/d]


def project_hypercube(verts4D, d):
    '''
        Project the hypercube verts onto 3D space given the projection distance.
    '''
    verts = [project(verts4D[i], d) for i in range(len(verts4D))]
    return verts


def rotation4D(a1=0, a2=0, a3=0, a4=0, a5=0, a6=0):
    '''
        Return the 4D rotation matrix given the 6 rotation angles.
    '''
    rotXY = Matrix(((cos(a1), sin(a1), 0, 0),
                    (-sin(a1), cos(a1), 0, 0),
                    (0, 0, 1, 0),
                    (0, 0, 0, 1)))

    rotYZ = Matrix(((1, 0, 0, 0),
                    (0, cos(a2), sin(a2), 0),
                    (0, -sin(a2), cos(a2), 0),
                    (0, 0, 0, 1)))

    rotZX = Matrix(((cos(a3), 0, -sin(a3), 0),
                    (0, 1, 0, 0),
                    (sin(a3), 0, cos(a3), 0),
                    (0, 0, 0, 1)))

    rotXW = Matrix(((cos(a4), 0, 0, sin(a4)),
                    (0, 1, 0, 0),
                    (0, 0, 1, 0),
                    (-sin(a4), 0, 0, cos(a4))))

    rotYW = Matrix(((1, 0, 0, 0),
                    (0, cos(a5), 0, -sin(a5)),
                    (0, 0, 1, 0),
                    (0, sin(a5), 0, cos(a5))))

    rotZW = Matrix(((1, 0, 0, 0),
                    (0, 1, 0, 0),
                    (0, 0, cos(a6), -sin(a6)),
                    (0, 0, sin(a6), cos(a6))))

    rotation = rotXY * rotYZ * rotZX * rotXW * rotYW * rotZW

    return rotation


def rotate_hypercube(verts4D, a1, a2, a3, a4, a5, a6):
    '''
        Rotate the hypercube verts by the given rotation angles.
    '''
    rotation = rotation4D(a1, a2, a3, a4, a5, a6)  # 4D matrix
    verts = [rotation * verts4D[i] for i in range(len(verts4D))]
    return verts


def transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d):
    '''
        Transform the hypercube verts (4D rotation + 3D projection).
    '''
    newVerts4D = rotate_hypercube(verts4D, a1, a2, a3, a4, a5, a6)
    verts3D = project_hypercube(newVerts4D, d)
    return verts3D


def generate_hypercube():
    '''
        Generate the unit hypercube verts, edges & polys once
    '''
    if _hypercube:
        return

    cube = [[i, j, k] for i in [0, 1] for j in [0, 1] for k in [0, 1]]

    hypercube = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for k in [0, 1] for l in [0, 1]]

    # TODO: find a better (and working) way to do this
    edges = []
    faces = []
    for k in [0, 1]:  # tries (and fails) to create the faces with normals pointing to the outside
        for l in [0, 1]:
            faces.append(list(map(hypercube.index, [[i ^ j, j, k, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
            faces.append(list(map(hypercube.index, [[i ^ j, k, j, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
            faces.append(list(map(hypercube.index, [[i ^ j, k, l, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
            faces.append(list(map(hypercube.index, [[k, i ^ j, j, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
            faces.append(list(map(hypercube.index, [[k, i ^ j, l, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
            faces.append(list(map(hypercube.index, [[k, l, i ^ j, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))

    # center the verts around origin
    # verts = [Vector([x, y, z, w]) for x, y, z, w in hypercube]
    verts = [Vector([2*x-1, 2*y-1, 2*z-1, 2*w-1]) for x, y, z, w in hypercube]

    # store hypercube's verts, edges & polys in a global dictionary
    _hypercube["verts"] = verts
    _hypercube["edges"] = edges
    _hypercube["faces"] = faces


def get_hypercube():
    '''
        Get the unit hypercube's verts, edges and polys (generate one if needed)
    '''
    if not _hypercube:
        generate_hypercube()

    return _hypercube["verts"], _hypercube["edges"], _hypercube["faces"]


class SvHyperCubeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' HyperCube '''
    bl_idname = 'SvHyperCubeNode'
    bl_label = 'Hypercube'

    angleType = EnumProperty(
        name="Angle Type", description="Angle units",
        default="DEG", items=angleTypes, update=updateNode)

    angle_a1 = FloatProperty(
        name="XY", description="Angle 1",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle_a2 = FloatProperty(
        name="YZ", description="Angle 2",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle_a3 = FloatProperty(
        name="ZX", description="Angle 3",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle_a4 = FloatProperty(
        name="XW", description="Angle 4",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle_a5 = FloatProperty(
        name="YW", description="Angle 5",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    angle_a6 = FloatProperty(
        name="ZW", description="Angle 6",
        default=0.0, min=0.0, soft_min=0.0,
        update=updateNode)

    distance = FloatProperty(
        name="D", description="Projection Distance",
        default=2.0, min=0.0, soft_min=0.0,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "A1").prop_name = 'angle_a1'
        self.inputs.new('StringsSocket', "A2").prop_name = 'angle_a2'
        self.inputs.new('StringsSocket', "A3").prop_name = 'angle_a3'
        self.inputs.new('StringsSocket', "A4").prop_name = 'angle_a4'
        self.inputs.new('StringsSocket', "A5").prop_name = 'angle_a5'
        self.inputs.new('StringsSocket', "A6").prop_name = 'angle_a6'
        self.inputs.new('StringsSocket', "D").prop_name = 'distance'

        self.outputs.new('StringsSocket', "Verts4D")
        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket',  "Edges")
        self.outputs.new('StringsSocket',  "Polys")
        self.outputs.new('StringsSocket',  "Cells")
        self.outputs.new('StringsSocket',  "Indices")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'angleType', expand=True)


    def process(self):
        # return if no outputs are connected
        if not any(s.is_linked for s in self.outputs):
            return

        # input values lists
        inputs = self.inputs
        input_a1 = inputs["A1"].sv_get()[0]
        input_a2 = inputs["A2"].sv_get()[0]
        input_a3 = inputs["A3"].sv_get()[0]
        input_a4 = inputs["A4"].sv_get()[0]
        input_a5 = inputs["A5"].sv_get()[0]
        input_a6 = inputs["A6"].sv_get()[0]
        input_d = inputs["D"].sv_get()[0]

        # sanitize the input
        # input_a1 = list(map(lambda f: min(1, max(0, f)), input_a1))
        # input_a2 = list(map(lambda f: min(1, max(0, f)), input_a2))
        # input_a3 = list(map(lambda f: min(1, max(0, f)), input_a3))
        # input_a4 = list(map(lambda f: min(1, max(0, f)), input_a4))
        # input_a5 = list(map(lambda f: min(1, max(0, f)), input_a5))
        # input_a6 = list(map(lambda f: min(1, max(0, f)), input_a6))
        # convert everything to radians
        if self.angleType == "DEG":
            # print("Degree")
            aU = pi/360
        elif self.angleType == "RAD":
            # print("Radians")
            aU = 1
        else:
            # print("Normalized")
            aU = pi

        params = match_long_repeat([input_a1, input_a2, input_a3, input_a4, input_a5, input_a6, input_d])

        verts4D, edges, polys = get_hypercube()

        vertList = []
        edgeList = []
        polyList = []
        for a1, a2, a3, a4, a5, a6, d in zip(*params):
            a1 *= aU
            a2 *= aU
            a3 *= aU
            a4 *= aU
            a5 *= aU
            a6 *= aU
            # print(a1)
            verts = transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d)
            vertList.append(verts)
            edgeList.append(edges)
            polyList.append(polys)

        cells, indices = create_cells()

        self.outputs['Verts4D'].sv_set([verts4D])
        self.outputs['Verts'].sv_set(vertList)
        self.outputs['Edges'].sv_set(edgeList)
        self.outputs['Polys'].sv_set(polyList)
        self.outputs['Cells'].sv_set(cells)
        self.outputs['Indices'].sv_set(indices)


def register():
    bpy.utils.register_class(SvHyperCubeNode)


def unregister():
    bpy.utils.unregister_class(SvHyperCubeNode)

if __name__ == '__main__':
    register()
