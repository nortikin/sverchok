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

from mathutils import Vector

class Vertex(object):
    def __init__(self, *args):
        self.index = 0
        if len(args) == 1:
            self.co = Vector(args[0])
        else:
            x,y,z = args
            self.co = Vector((x,y,z))

    def __eq__(self, other):
        return self.index == other.index

    def __hash__(self):
        return self.index

    @property
    def x(self):
        return self.co.x

    @x.setter
    def x(self, x):
        self.co.x = x

    @property
    def y(self):
        return self.co.y

    @y.setter
    def y(self, y):
        self.co.y = y

    @property
    def z(self):
        return self.co.z

    @z.setter
    def z(self, z):
        self.co.z = z

    def __str__(self):
        return "#{}({}, {}, {})".format(self.index, self.x, self.y, self.z)
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

class Edge(object):
    def __init__(self, v1, v2):
        self.vertices = [v1, v2]

    def __eq__(self, other):
        return ((self.v1 == other.v1) and (self.v2 == other.v2)) or ((self.v1 == other.v2) and (self.v2 == other.v1))

    def __hash__(self):
        return self.v1.index + self.v2.index

    def __getitem__(self,key):
        return self.vertices[key]

    @property
    def v1(self):
        return self.vertices[0]

    @v1.setter
    def v1(self, v1):
        self.vertices[0] = v1

    @property
    def v2(self):
        return self.vertices[1]

    @v1.setter
    def v2(self, v2):
        self.vertices[1] = v2

    def sorted(self):
        if self.v1.index < self.v2.index:
            return self
        else:
            return Edge(self.v2, self.v1)

    def __str__(self):
        return "[#{} -- #{}]".format(self.v1.index, self.v2.index)

    def __iter__(self):
        yield self.v1
        yield self.v2

class Face(object):
    def __init__(self, vertices):
        self.vertices = vertices

    def __str__(self):
        indicies = [v.index for v in self.vertices]
        return "[" + ", ".join(indicies) + "]"
    
    def __eq__(self, other):
        self_inds = [v.index for v in self.vertices]
        other_inds = [v.index for v in other.vertices]
        return self_inds == other_inds

    def __hash__(self):
        return sum(v.index for v in self.vertices)
    
    def __iter__(self):
        for v in self.vertices:
            yield v

    def __getitem__(self, key):
        return self.vertices[key]

class Mesh(object):
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.edges = set()
        self.next_index = 0

    def new_vertex(self, co):
        vertex = Vertex(co)
        vertex.index = self.next_index
        self.next_index += 1
        self.vertices.append(vertex)
        return vertex

    def add_vertex(self, vertex):
        if not isinstance(vertex, Vertex):
            raise TypeError("add_vertex() argument must be a Vertex")
        vertex.index = self.next_index
        self.next_index += 1
        self.vertices.append(vertex)
        return vertex

    def new_face(self, vertices):
        if isinstance(vertices[0], int):
            vertices = [self.vertices[i] for i in vertices]
        face = Face(vertices)
        self.faces.append(face)
        for v1, v2 in zip(face, face[1:]):
            self.edges.add(Edge(v1, v2))
        self.edges.add(Edge(face[-1], face[0]))
        return face

    def new_edge(self, v1, v2):
        if isinstance(v1, int):
            v1 = self.vertices[v1]
        if isinstance(v2, int):
            v2 = self.vertices[v2]
        edge = Edge(v1, v2)
        self.edges.add(edge)
        return edge

    @staticmethod
    def from_sv_data(vertices, edges, faces):
        mesh = Mesh()
        for v in vertices:
            mesh.new_vertex(v)
        for face in faces:
            mesh.new_face(face)
        for i, j in edges:
            mesh.new_edge(i, j)
        return mesh

    def get_sv_vertices(self):
        return [tuple(v.co) for v in self.vertices]

    def get_sv_edges(self):
        return [(e.v1.index, e.v2.index) for e in self.edges]

    def get_sv_faces(self):
        return [[v.index for v in f] for f in self.faces]

