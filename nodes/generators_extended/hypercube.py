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
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from math import sin, cos, pi, sqrt, radians
from mathutils import Vector, Matrix
import copy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
import itertools

# dictionary to store once the unit/untransformed hypercube verts, edges & polys
_hypercube = {}

angleTypes = [
    ("RAD", "Rad", "", 0),   # expects input as radian values
    ("DEG", "Deg", "", 1),   # expects input as degree values
    ("NORM", "Norm", "", 2)]  # expects input as 0-1 values


def flip(n, v):
    '''
        Flips the N-th coordinate of the binary N dimensional vector between 0 and 1.

        e.g. for v = [1, 0, 0, 1] => flip(1, v) = [1, 1, 0, 1]
                 n :  0  1  2  3                   0  1  2  3
    '''
    return [(v[i] + 1) % 2 if i == n else v[i] for i in range(len(v))]

    return []


def flipper(v):
    '''
        Flips each dimension of the binary N dimensional vector between 0 and 1
        returning the list of all single flips of the given binary vector.

        Note: In essense this is equivalent to generating all vertices in a N
        dimensional Hypercube touching a given ND vertex along all dimensions.

        e.g. v = [1, 0, 1] => flipper(v) = [[0, 0, 1], [1, 1, 1], [1, 0, 0]]
    '''
    links = []
    for n in range(len(v)):
        links.append(flip(n, v))
    return links


def edges_touching(v):
    '''
        Returns the list of edges connecting the binary N dimensional vertex
        of a N dimensional Hypercube to all the adjacent N dimensional vertices
        along all dimensions.

        e.g. v = [1, 0, 1] =>
        edges(v) = [[[1, 0, 1], [0, 0, 1]], [[1, 0, 1], [1, 1, 1]], [[1, 0, 1], [1, 0, 0]]]
    '''
    return [list(tup) for tup in itertools.product([v], flipper(v))]


def index(v):
    '''
        Convert a binary N dimensional vector into a decimal index.

        Note: this essentially indexes the vertices in a Hypercube.

        e.g. v = [1,0,1] => 101 (binary) = 5 (decimal)
    '''
    a = 0
    N = len(v)
    for i in range(N):
        a += v[i] << (N - 1 - i)
    return a


def edgesIDs_touching(v):
    '''
        Return the list of all edges (as a pair of vertex indices) touching a given vertex.

        e.g. v = [1, 0, 1] =>
        edges(v)   = [[[1, 0, 1], [0, 0, 1]], [[1, 0, 1], [1, 1, 1]], [[1, 0, 1], [1, 0, 0]]]
        edgesID(v) = [[    5    ,     1    ], [    5    ,     7    ], [    5    ,     4    ]]
    '''
    es = edges_touching(v)
    return [[index(v1), index(v2)] for v1, v2 in es]


def create_cells2():
    vertList = []
    indexList = []
    edgeList = []
    faceList = []

    indexList = get_cell_verts_IDs(4)
    edgeList = get_cell_edges_IDs(4)

    return vertList, indexList, edgeList, faceList


def create_cells():
    '''
        Create the Hypercube faces (cells) and indices forming each face

        A cell has 8 vertices (a cube) and corresponds to keeping one of the i,j,k,l constants at 0 or 1.
    '''
    vertList = []
    indexList = []
    edgeList = []
    faceList = []
    for i in [0, 1]:
        verts = [[i, j, k, l] for j in [0, 1] for k in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indices = [index(v) for v in verts]
        indexList.append(indices)
        edges = [edgesIDs_touching(v) for v in verts]
        edgeList.append(edges)
    for j in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for k in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indexList.append(indices)
        edges = [edgesIDs_touching(v) for v in verts]
        edgeList.append(edges)
    for k in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for l in [0, 1]]
        vertList.append(verts)
        indices = [index(v) for v in verts]
        indexList.append(indices)
        edges = [edgesIDs_touching(v) for v in verts]
        edgeList.append(edges)
    for l in [0, 1]:
        verts = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for k in [0, 1]]
        vertList.append(verts)
        indices = [index(v) for v in verts]
        indexList.append(indices)
        edges = [edgesIDs_touching(v) for v in verts]
        edgeList.append(edges)

    return vertList, indexList, edgeList, faceList


def get_cells_verts():
    cells = []
    cellIDs = []
    cube = [[i1, i2, i3] for i1 in [0, 1] for i2 in [0, 1] for i3 in[0, 1]]
    for n in range(4):  # 0 1 2 3 (for each dimension)
        for b in range(2):  # 0 1 (flip side)
            cell = copy.deepcopy(cube)
            [v.insert(n, b) for v in cell]
            cells.append(cell)
            ids = [index(v) for v in cell]
            cellIDs.append(ids)
    return cells, cellIDs


def get_verts(n):
    return [list(v) for v in list(itertools.product([0, 1], repeat=n))]


def get_verts_IDs(n):
    verts = get_verts(n)
    return [index(v) for v in verts]


def get_edges(n):
    return [[a, a | 1 << l] for a in range(2**n) for l in range(n) if ~ a & 1 << l]


def get_edges_IDs(n):
    edges = get_edges(n)
    return [[index(v1), index(v2)] for v1, v2 in edges]


def clear_bit(v, n):
    '''
        Clear the n-th bit in the binary representation of v.
        e.g.  v = 101101, n = 3 => 100101
    '''
    return v & (1 << n)


def set_bit(v, n):
    '''
        Set the n-th bit in the binary representation of v.
        e.g.  v = 101101, n = 1 => 101111
    '''
    return v | (1 << n)


def flip_bit(v, n):
    '''
        Flip the n-th bit in the binary representation of v.
        e.g.  v = 101101, n = 3 => 100101
    '''
    return v ^ (1 << n)


def insert_bit(v, b, n):
    '''
        Insert a bit (0/1) at the n-th bit in the binary representation of v
        shifting the higher end bits by one.
        e.g.  v = 101101, b = 0, n = 2 => 1011001
    '''
    return (v & ~(2**n - 1)) << 1 | b << n | v & (2**n - 1)


def vinarize(v, n):
    '''
        Convert an integer into a list of its binary representation.
        e.g.  v = 6, n = 7 => [0, 0, 0, 0, 1, 1, 0]
    '''
    return [(v & (1 << l)) >> l for l in reversed(range(n))]


def get_cell_verts(n):
    verts = get_verts_IDs(n - 1)
    cellv = []
    for m in range(n):
        for b in [0, 1]:
            cell = []
            for v in verts:
                # print("m=", m)
                # print("b=", b)
                # print("v=", vinarize(v, n))
                vx = insert_bit(v, b, m)
                # print("vx=", vinarize(vx, n))
                # cell.append(vx)
                cell.append(vinarize(vx, n))
                # print("\n")
            cellv.append(cell)
    return cellv


def get_cell_verts_IDs(n):
    cells = get_cell_verts(n)
    return [[index(v) for v in cell] for cell in cells]


def get_cell_edges(n):
    edges = get_edges(n - 1)
    celle = []
    for m in range(n):
        for b in [0, 1]:
            cell = []
            for v1, v2 in edges:
                # print("m=", m)
                # print("b=", b)
                # print("v=", vinarize(v, n))
                v1x = insert_bit(v1, b, m)
                v2x = insert_bit(v2, b, m)
                # print("vx=", vinarize(vx, n))
                # cell.append(vx)
                cell.append([vinarize(v1x, n), vinarize(v2x, n)])
                # print("\n")
            celle.append(cell)
    return celle


def get_cell_edges_IDs(n):
    cells = get_cell_edges(n)
    return [[[index(v1), index(v2)] for v1, v2 in cell] for cell in cells]


def project(vert4D, d):
    '''
        Project a 4D vector onto 3D space given the projection distance.
    '''
    cx, cy, cz = [0.0, 0.0, 0.0]  # center (projection origin)
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
    verts4D = [rotation * v for v in verts4D]
    return verts4D


def translate_hypercube(verts4D, t):
    '''
        Translate the Hypercube 4D vertices by the given 4D vector
    '''
    newVerts4D = [v + t for v in verts4D]
    return newVerts4D


def scale_hypercube(verts4D, s):
    '''
        Scale the Hypercube 4D vertices by the given scale factor
    '''
    newVerts4D = [v * s for v in verts4D]
    return newVerts4D


def transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d, s, t):
    '''
        Transform the Hypercube 4D verts (4D TRS + 4D -> 3D projection).
    '''
    t = Vector(list(t))
    center = Vector([-0.5, -0.5, -0.5, -0.5])
    newVerts4D = translate_hypercube(verts4D, center)
    newVerts4D = scale_hypercube(newVerts4D, s)
    newVerts4D = rotate_hypercube(newVerts4D, a1, a2, a3, a4, a5, a6)
    newVerts4D = translate_hypercube(newVerts4D, t)
    verts3D = project_hypercube(newVerts4D, d)
    return verts3D


def generate_hypercube():
    '''
        Generate the unit Hypercube verts, edges, faces, cells.

        Note: This is generated ONCE and cached during the first invocation.
    '''
    if _hypercube:
        return

    # hypercube = [[i, j, k, l] for i in [0, 1] for j in [0, 1] for k in [0, 1] for l in [0, 1]]  # 4D indices
    # hypercube = [list(v) for v in itertools.product([0, 1], repeat=4)]
    hypercube = list(itertools.product([0, 1], repeat=4))

    # TODO: find a better (and working) way to do this
    edges = []
    faces = []
    # for k in [0, 1]:  # tries (and fails) to create the faces with normals pointing to the outside
    #     for l in [0, 1]:
    #         faces.append(list(map(hypercube.index, [[i ^ j, j, k, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
    #         faces.append(list(map(hypercube.index, [[i ^ j, k, j, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
    #         faces.append(list(map(hypercube.index, [[i ^ j, k, l, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
    #         faces.append(list(map(hypercube.index, [[k, i ^ j, j, l] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
    #         faces.append(list(map(hypercube.index, [[k, i ^ j, l, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))
    #         faces.append(list(map(hypercube.index, [[k, l, i ^ j, j] for j in [k, k ^ 1] for i in [l, l ^ 1]])))

    # verts = [Vector([x, y, z, w]) for x, y, z, w in hypercube]
    verts = [Vector(v) for v in hypercube]

    edges = get_edges(4)

    cells = {}
    cells["verts"] = get_cell_verts_IDs(4)
    cells["edges"] = get_cell_edges_IDs(4)
    cells["vertsIDs"] = []
    cells["faces"] = []

    # print("***", type(cells))
    names = [":".join(map(str, a)) for a in hypercube]

    # store hypercube's verts, edges, polys & cells in a global dictionary
    _hypercube["verts"] = verts
    _hypercube["edges"] = edges
    _hypercube["faces"] = faces
    _hypercube["cells"] = cells
    _hypercube["names"] = names


def get_hypercube():
    '''
        Get the unit hypercube's verts, edges and polys (generate one if needed)
    '''
    if not _hypercube:
        generate_hypercube()

    return _hypercube["verts"], _hypercube["edges"], _hypercube["faces"], _hypercube["cells"], _hypercube["names"]


class SvHyperCubeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' HyperCube '''
    bl_idname = 'SvHyperCubeNode'
    bl_label = 'Hypercube'

    def update_angle(self, context):
        if self.syncing:
            return
        updateNode(self, context)

    def update_mode(self, context):
        '''
            Update angle values when switching mode to keep the same radian values
        '''
        if self.lastAngleType == self.angleType:
            return

        if self.lastAngleType == "RAD":
            if self.angleType == "DEG":
                aU = 180 / pi
            elif self.angleType == "NORM":
                aU = 1 / (2 * pi)

        elif self.lastAngleType == "DEG":
            if self.angleType == "RAD":
                aU = pi / 180
            elif self.angleType == "NORM":
                aU = 1 / 360

        elif self.lastAngleType == "NORM":
            if self.angleType == "RAD":
                aU = 2 * pi
            elif self.angleType == "DEG":
                aU = 360
        self.lastAngleType = self.angleType

        self.syncing = True
        self.angle_a1 *= aU
        self.angle_a2 *= aU
        self.angle_a3 *= aU
        self.angle_a4 *= aU
        self.angle_a5 *= aU
        self.angle_a6 *= aU
        self.syncing = False

        updateNode(self, context)

    angleType = EnumProperty(
        name="Angle Type", description="Angle units",
        default="RAD", items=angleTypes, update=update_mode)

    lastAngleType = EnumProperty(
        name="Last Angle Type", description="Last angle units",
        default="RAD", items=angleTypes)

    angle_a1 = FloatProperty(
        name="XY", description="Angle 1",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a2 = FloatProperty(
        name="YZ", description="Angle 2",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a3 = FloatProperty(
        name="ZX", description="Angle 3",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a4 = FloatProperty(
        name="XW", description="Angle 4",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a5 = FloatProperty(
        name="YW", description="Angle 5",
        default=0.0, min=0.0,
        update=update_angle)

    angle_a6 = FloatProperty(
        name="ZW", description="Angle 6",
        default=0.0, min=0.0,
        update=update_angle)

    distance = FloatProperty(
        name="Distance", description="Projection Distance",
        default=2.0, min=0.0,
        update=updateNode)

    scale = FloatProperty(
        name="Scale", description="Scale Hypercube sides",
        default=1.0, min=0.0,
        update=updateNode)

    translate = FloatVectorProperty(
        size=4,
        name="Translate", description="Translate Hypercube in 4D space",
        default=(0, 0, 0, 0),
        update=updateNode)

    syncing = BoolProperty(
        name='Syncing', description='Syncing flag', default=False)

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
        self.inputs.new('VerticesSocket', "Translate").prop_name = 'translate'

        self.outputs.new('StringsSocket', "Verts4D")
        self.outputs.new('VerticesSocket', "V4D")
        self.outputs.new('VerticesSocket', "Verts")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polys")
        self.outputs.new('StringsSocket', "Cells Verts")
        self.outputs.new('StringsSocket', "Cells Verts IDs")
        self.outputs.new('StringsSocket', "Cells Edges")
        self.outputs.new('StringsSocket', "Cells Faces")
        self.outputs.new('StringsSocket', "Vert Names")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'angleType', expand=True)

    def process(self):
        # return if no outputs are connected
        outputs = self.outputs
        if not any(s.is_linked for s in outputs):
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
        input_t = inputs["Translate"].sv_get()[0]

        # convert everything to radians
        if self.angleType == "DEG":
            aU = pi / 180
        elif self.angleType == "RAD":
            aU = 1
        else:
            aU = 2 * pi

        params = match_long_repeat([input_a1, input_a2, input_a3, input_a4,
                                    input_a5, input_a6, input_d, input_s, input_t])

        verts4D, edges, polys, cells, names = get_hypercube()

        vertList = []
        edgeList = []
        polyList = []
        for a1, a2, a3, a4, a5, a6, d, s, t in zip(*params):
            a1 *= aU
            a2 *= aU
            a3 *= aU
            a4 *= aU
            a5 *= aU
            a6 *= aU
            verts = transform_hypercube(verts4D, a1, a2, a3, a4, a5, a6, d, s, t)
            vertList.append(verts)
            edgeList.append(edges)
            polyList.append(polys)

        # cells, indices, edges, faces = create_cells2()
        cellVerts = cells["verts"]
        cellVertsIDs = cells["vertsIDs"]
        cellEdges = cells["edges"]
        cellFaces = cells["faces"]

        outputs['Verts4D'].sv_set([verts4D])

        v4d = [list(v) for v in verts4D]
        # print(v4d)
        outputs['V4D'].sv_set([v4d])

        outputs['Verts'].sv_set(vertList)
        outputs['Edges'].sv_set(edgeList)
        outputs['Polys'].sv_set(polyList)

        outputs['Cells Verts'].sv_set(cellVerts)
        outputs['Cells Verts IDs'].sv_set(cellVertsIDs)
        outputs['Cells Edges'].sv_set(cellEdges)
        outputs['Cells Faces'].sv_set(cellFaces)

        outputs['Vert Names'].sv_set([names])


def register():
    bpy.utils.register_class(SvHyperCubeNode)


def unregister():
    bpy.utils.unregister_class(SvHyperCubeNode)


'''
    TODO:

    matrix multiplication in 4D (4D TRS)
    toggle on/off hyper faces
    select all edges along a given dimension
    hyperplane intersections (verts 0D, edges 1D, faces 2D, cells 3D)
    scale, rotate, translate cells of a hypercube (unfolding)
    4D point, 4D line, 4D plane locations in 4D/3D space
    4D camera/projection origin
    edge/face/cell centroids


    verts in a cell k/n (n/n is the whole hypercube)
    E(k,n) = 2^k * c(n,k)
    for n = 4
    cell 1/4 = 2^1 * c(1,4) = 2 * 4  = 8  : cells/cubes @ (4-1=3 -> 2^3=8 verts)
    cell 2/4 = 2^2 * c(2,4) = 4 * 6  = 24 : faces       @ (4-2=2 -> 2^2=4 verts)
    cell 3/4 = 2^3 * c(3,4) = 8 * 4  = 32 : edges       @ (4-3=1 -> 2^1=2 verts)
    cell 4/4 = 2^4 * c(4,4) = 16 * 1 = 16 : vertices    @ (4-4=0 -> 2^0=1 verts)

    x x x x
    1 1
    1   1
    1     1
      1 1
      1   1
        1 1

    mkdir -p hypercube/cells/faces/edges/verts
    mkdir -p hypercube/cells/faces/verts
    mkdir -p hypercube/cells/edges/verts
    mkdir -p hypercube/cells/verts

    mkdir -p hypercube/faces/edges/verts
    mkdir -p hypercube/faces/verts

    mkdir -p hypercube/edges/verts

    mkdir -p hypercube/verts

    C [dimension] : component : count : index range

    H [4] : hypercube : 1 : 0
    │
    ├── C [3] : cells : 8 : 0->7
    │   ├── faces : 6 : 0->23 (F)
    │   │   ├── edges : 4 : 0->31 (E)
    │   │   │   └── verts : 2 : 0->15 (V)
    │   │   └── verts : 4 : 0->15 (V)
    │   ├── edges : 12 : 0->31 (E) *
    │   │   └── verts : 2 : 0->15 (V) *
    │   └── verts : 8 : 0->15 (V) *
    │    
    ├── F [2] : faces : 24 : 0->23
    │   ├── edges : 4 : 0->31 (E)
    │   │   └── verts : 2 : 0->15 (V)
    │   └── verts : 4 : 0->15 (V)
    │     
    ├── E [1] : edges : 32 : 0->31 *
    │   └── verts : 2 : 0->15 (V) *
    │  
    └── V [0] : verts : 16 : 0->15 *

    H(1)C(4)F(2)E(3)V(2) - selection

    5D Hypercube rotations (10):

    XY
    XZ
    XW
    XT

    YZ
    YW
    YT

    ZW
    ZT

    WT

'''
