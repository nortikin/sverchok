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
    ("RAD", "Rad", "", 0),
    ("DEG", "Deg", "", 1),
    ("NORM", "Norm", "", 2)]


def flip(n, v):
    '''
        Flips the N-th coordinate of the binary N dimensional vector between 0 and 1.

        e.g. for v = [1, 0, 0, 1], flip(1, v) = [1, 1, 0, 1]
    '''
    return [(v[i] + 1) % 2 if i == n else v[i] for i in range(len(v))]


def flipper(v):
    '''
        Flips all dimensions of the binary N dimensional vector between 0 and 1
        returning the list of all flips reachable from the given binary vector.

        Note: In essense this is equivalent to generating all vertices in a N
        dimensional hypercube touching a given ND vertex along all dimenions.

        e.g. v = [1, 0, 1] => flipper(v) = [[0, 0, 1], [1, 1, 1], [1, 0, 0]]
    '''
    links = []
    for n in range(len(v)):
        links.append(flip(n, v))
    return links


def edges(v):
    '''
        Returns the list of edges connecting the binary N dimensional vertex
        of a N dimensional hypercube to all the adjacent N dimensional vertices
        along all dimensions.

        e.g. v = [1, 0, 1] =>
        edges(v) = [([1, 0, 1], [0, 0, 1]), ([1, 0, 1], [1, 1, 1]), ([1, 0, 1], [1, 0, 0])]
    '''
    # return list(itertools.product([v], flipper(v)))
    return [list(tup) for tup in itertools.product([v], flipper(v))]


def index(v):
    a = 0
    N = len(v)
    for i in range(N):
        a += v[i] << (N-1-i)
    return a

def edgesIDs(v):
    '''
    '''
    es = edges(v)
    return [[index(v1), index(v2)] for v1, v2 in es]


def create_cells():
    '''
        Create the Hypercube faces (cells) and indices forming each face

        A cell has 8 vertices (a cube) and corresponds to keeping one of the i,j,k,l constants at 0 or 1.
    '''
    vertList = []
    indexList = []
    edgeList = []
    for i in [0, 1]:
        verts = [[i, j, k, l] for j in [0, 1] for k in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indices = [(i << 3) + (j << 2) + (k << 1) + l for j in [0, 1] for k in [0, 1] for l in [0, 1]]
        indexList.append(indices)
        edges = [edgesIDs(v) for v in verts]
        edgeList.append(edges)
    for j in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for k in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indices = [(i << 3) + (j << 2) + (k << 1) + l for i in [0, 1] for k in [0, 1] for l in [0, 1]]
        indexList.append(indices)
        edges = [edgesIDs(v) for v in verts]
        edgeList.append(edges)
    for k in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indices = [(i << 3) + (j << 2) + (k << 1) + l for i in [0, 1] for j in [0, 1] for l in [0, 1]]
        indexList.append(indices)
        edges = [edgesIDs(v) for v in verts]
        edgeList.append(edges)
    for l in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for k in [0, 1]]
        vertList.append(verts)
        indices = [(i << 3) + (j << 2) + (k << 1) + l for i in [0, 1] for j in [0, 1] for k in [0, 1]]
        indexList.append(indices)
        edges = [edgesIDs(v) for v in verts]
        edgeList.append(edges)

    return vertList, indexList, edgeList


def project(vert4D, d):
    '''
        Project a 4D vector onto 3D space given the projection distance.
    '''
    cx, cy, cz = [0.0, 0.0, 0.0]  # center (projection origin)
    # cx, cy, cz = [0.5, 0.5, 0.5]  # center
    x, y, z, t = vert4D
    return [x + (cx - x) * t / d, y + (cy - y) * t / d, z + (cz - z) * t / d]


def project_hypercube(verts4D, d):
    '''
        Project the Hypercube 4D verts onto 3D space given the projection distance.
    '''
    verts3D = [project(verts4D[i], d) for i in range(len(verts4D))]
    return verts3D


def rotation4D(a1=0, a2=0, a3=0, a4=0, a5=0, a6=0):
    '''
        Return the 4D Rotation matrix given the 6 rotation angles.
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
        Rotate the Hypercube 4D verts by the given rotation angles.
    '''
    rotation = rotation4D(a1, a2, a3, a4, a5, a6)  # 4D rotation matrix
    verts4D = [rotation * verts4D[i] for i in range(len(verts4D))]
    return verts4D


def transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d, s):
    '''
        Transform the Hypercube 4D verts (4D rotation + 4D -> 3D projection).
    '''
    newVerts4D = rotate_hypercube(verts4D , a1, a2, a3, a4, a5, a6)
    verts3D = project_hypercube(newVerts4D, d)
    return verts3D


def generate_hypercube():
    '''
        Generate the unit Hypercube verts, edges & polys (ONCE)
    '''
    if _hypercube:
        return

    cube = [[i, j, k] for i in [0, 1] for j in [0, 1] for k in [0, 1]]  # 3D indices

    hypercube = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for k in [0, 1] for l in [0, 1]]  # 4D indices

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
    verts = [Vector([2 * x - 1, 2 * y - 1, 2 * z - 1, 2 * w - 1]) for x, y, z, w in hypercube]

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
        default=0.0, min=0.0,
        update=updateNode)

    angle_a2 = FloatProperty(
        name="YZ", description="Angle 2",
        default=0.0, min=0.0,
        update=updateNode)

    angle_a3 = FloatProperty(
        name="ZX", description="Angle 3",
        default=0.0, min=0.0,
        update=updateNode)

    angle_a4 = FloatProperty(
        name="XW", description="Angle 4",
        default=0.0, min=0.0,
        update=updateNode)

    angle_a5 = FloatProperty(
        name="YW", description="Angle 5",
        default=0.0, min=0.0,
        update=updateNode)

    angle_a6 = FloatProperty(
        name="ZW", description="Angle 6",
        default=0.0, min=0.0,
        update=updateNode)

    distance = FloatProperty(
        name="D", description="Projection Distance",
        default=2.0, min=0.0,
        update=updateNode)

    scale = FloatProperty(
        name="Scale", description="Scale Hypercube sides",
        default=1.0, min=0.0,
        update=updateNode)

    def sv_init(self, context):
        self.width = 180
        self.inputs.new('StringsSocket', "A1").prop_name = 'angle_a1'
        self.inputs.new('StringsSocket', "A2").prop_name = 'angle_a2'
        self.inputs.new('StringsSocket', "A3").prop_name = 'angle_a3'
        self.inputs.new('StringsSocket', "A4").prop_name = 'angle_a4'
        self.inputs.new('StringsSocket', "A5").prop_name = 'angle_a5'
        self.inputs.new('StringsSocket', "A6").prop_name = 'angle_a6'
        self.inputs.new('StringsSocket', "D").prop_name = 'distance'
        self.inputs.new('StringsSocket', "S").prop_name = 'scale'

        self.outputs.new('StringsSocket', "Verts4D")
        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket',  "Edges")
        self.outputs.new('StringsSocket',  "Polys")
        self.outputs.new('StringsSocket',  "Cells Verts")
        self.outputs.new('StringsSocket',  "Cells Verts IDs")
        self.outputs.new('StringsSocket',  "Cells Edges")
        self.outputs.new('StringsSocket',  "Cells Faces")

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
        input_s = inputs["S"].sv_get()[0]

        # convert everything to radians
        if self.angleType == "DEG":
            # print("Degree")
            aU = pi / 180
        elif self.angleType == "RAD":
            # print("Radians")
            aU = 1
        else:
            # print("Normalized")
            aU = 2 * pi

        params = match_long_repeat([input_a1, input_a2, input_a3, input_a4, input_a5, input_a6, input_d, input_s])

        verts4D, edges, polys = get_hypercube()

        vertList = []
        edgeList = []
        polyList = []
        for a1, a2, a3, a4, a5, a6, d, s in zip(*params):
            a1 *= aU
            a2 *= aU
            a3 *= aU
            a4 *= aU
            a5 *= aU
            a6 *= aU
            # print(a1)
            verts = transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d, s)
            vertList.append(verts)
            edgeList.append(edges)
            polyList.append(polys)

        cells, indices, edges = create_cells()

        self.outputs['Verts4D'].sv_set([verts4D])
        self.outputs['Verts'].sv_set(vertList)
        self.outputs['Edges'].sv_set(edgeList)
        self.outputs['Polys'].sv_set(polyList)

        self.outputs['Cells Verts'].sv_set(cells)
        self.outputs['Cells Verts IDs'].sv_set(indices)
        self.outputs['Cells Edges'].sv_set(edges)


def register():
    bpy.utils.register_class(SvHyperCubeNode)


def unregister():
    bpy.utils.unregister_class(SvHyperCubeNode)

if __name__ == '__main__':
    register()


'''
    TODO:

    translate_hypercube
    scale_hypercube
    matrix multiplication in 4D (4D TRS)
'''