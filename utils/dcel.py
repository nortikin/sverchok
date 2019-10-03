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

"""
This module dedicated to Doubly-Connected Edge List data structure.
http://www.holmes3d.net/graphics/dcel/
At this stage the data structure works with faces only and does not support edges.

Advantages:
Have constant time access to the neighborhood of an arbitrary point can be very useful.
We can compute a normal for any given face easily, on demand, even if the vertex locations are changing.
We can also traverse every face touching a vertex (the "star" of the vertex) to easily estimate a normal for that vertex
If we are locally changing small portions of a mesh,
this is much easier than recomputing the normals for every vertex in the mesh.
Similarly, mesh simplification for Level of Detail or compressed storage becomes easier when neighbors are easily found.
Subdivision algorithms such as Loop and Catmull-Clark are relatively easy on a DCEL, especially adaptive subdivision.
"""

x, y, z = 0, 1, 2


def is_ccw(a, b, c):
    """
    Tests whether the turn formed by A, B, and C is counter clockwise
    :param a: 2d point - any massive
    :param b: 2d point - any massive
    :param c: 2d point - any massive
    :return: True if turn is counter clockwise else False
    """
    return (b[x] - a[x]) * (c[y] - a[y]) > (b[y] - a[y]) * (c[x] - a[x])


def is_ccw_polygon(verts):
    x_min = min(range(len(verts)), key=lambda i: verts[i][x])
    return True if is_ccw(verts[(x_min - 1) % len(verts)], verts[x_min], verts[(x_min + 1) % len(verts)]) else False


class Point:
    def __init__(self, mesh, co):
        self.mesh = mesh
        self.co = co
        self.hedge = None

    def __str__(self):
        return "({:.1f}, {:.1f}, {:.1f})".format(self.co[0], self.co[1], self.co[2])


class HalfEdge:
    def __init__(self, mesh, point, face=None):
        self.mesh = mesh
        self.origin = point
        self.face = face

        self.twin = None
        self.next = None
        self.last = None

    def __str__(self):
        return "Hedg({}, {})".format(self.origin, self.twin.origin if self.twin else self.next.origin)

    @property
    def ccw_hedges(self):
        # returns hedges originated in one point
        yield self
        next_edge = self.last.twin
        counter = 0
        while next_edge != self:
            yield next_edge
            next_edge = next_edge.last.twin
            counter += 1
            if counter > self.mesh.hedges:
                raise RecursionError('Hedge - {} does not have a loop'.format(self))

    @property
    def loop_hedges(self):
        # returns hedges bounding face
        yield self
        next_edge = self.next
        counter = 0
        while next_edge != self:
            yield next_edge
            try:
                next_edge = next_edge.next
            except AttributeError:
                raise AttributeError(' Some of half edges has incomplete data (does not have link to next half edge)')
            counter += 1
            if counter > self.mesh.hedges:
                raise RecursionError('Hedge - {} does not have a loop'.format(self))


class Face:
    def __init__(self, mesh):
        self.mesh = mesh
        self.outer = None
        self.inners = []

    @property
    def is_unbounded(self):
        return not self.outer


class DCELMesh:
    def __init__(self):
        self.points = []
        self.hedges = []
        self.faces = []

    def from_sv_faces(self, verts, faces):
        # todo: self intersection polygons? double repeated polygons???
        if self.points or self.hedges or self.faces:
            raise Exception('The mesh should be empty before generation mesh from SV data')
        half_edges_list = dict()
        unbounded_face = Face(self)
        self.faces.append(unbounded_face)
        self.points = [Point(self, co) for co in verts]

        # Generate outer faces and there hedges
        for face in faces:
            face = face if is_ccw_polygon([verts[i] for i in face]) else face[::-1]
            f = Face(self)
            loop = []
            for i in range(len(face)):
                origin_i = face[i]
                next_i = face[(i + 1) % len(face)]
                half_edge = HalfEdge(self, self.points[origin_i], f)
                loop.append(half_edge)
                half_edges_list[(origin_i, next_i)] = half_edge
            for i in range(len(face)):
                loop[i].last = loop[(i - 1) % len(face)]
                loop[i].next = loop[(i + 1) % len(face)]
            f.outer = loop[0]
            self.faces.append(f)
        self.hedges.extend(list(half_edges_list.values()))

        # to twin hedges and create hedges of unbounded face
        outer_half_edges = dict()
        for key in half_edges_list:
            half_edge = half_edges_list[key]
            if key[::-1] in half_edges_list:
                half_edge.twin = half_edges_list[key[::-1]]
                half_edges_list[key[::-1]].twin = half_edge
            else:
                outer_edge = HalfEdge(self, self.points[key[1]])
                outer_edge.face = unbounded_face
                half_edge.twin = outer_edge
                outer_edge.twin = half_edge
                if key[::-1] in outer_half_edges:
                    raise Exception("It looks like input mesh has adjacent faces with only one common point"
                                    "Handle such meshes does not implemented yet.")
                outer_half_edges[key[::-1]] = outer_edge
        self.hedges.extend(list(outer_half_edges.values()))

        # link hedges of unbounded face in loops
        for key in outer_half_edges:
            outer_edge = outer_half_edges[key]
            next_edge = outer_edge.twin
            count = 0
            while next_edge:
                next_edge = next_edge.last.twin
                if next_edge.face.is_unbounded:
                    break
                count += 1
                if count > len(half_edges_list):
                    raise RecursionError("The hedge ({}) cant find next neighbour".format(outer_edge))
            outer_edge.next = next_edge
            next_edge.last = outer_edge

        # link unbounded face to loops of edges of unbounded face
        used = set()
        for outer_hedge in outer_half_edges.values():
            if outer_hedge in used:
                continue
            unbounded_face.inners.append(outer_hedge)
            [used.add(hedge) for hedge in outer_hedge.loop_hedges]

    def to_sv_mesh(self):
        # all elements of mesh should have correct links
        used = set()
        sv_verts = []
        for hedge in self.hedges:
            counter = 0
            if hedge in used:
                continue
            sv_verts.append(hedge.origin.co)
            for h in hedge.ccw_hedges:
                used.add(h)

        # This part of function creates faces in SV format.
        # It ignores  boundless super face
        sv_faces = []
        for i, face in enumerate(self.faces):
            # Debugger.print_f(face, 'build face')
            if face.inners and face.outer:
                print('Face ({}) has inner components! Sverchok cant show polygons with holes.'.format(i))
            if not face.outer:
                continue
            # Debugger.print_he(face.outer, 'build face from')
            sv_faces.append([hedge.i for hedge in face.outer.loop_hedges])

        return sv_verts, sv_faces


"""
The sooner the DCEL does not have any indexes of its elements
the difficulties to debug algorithm which run with such data structure.
The class below can be used for recording any element of DCEL in class variable
which can be visualized by Sverchok via SN light.

Example of script node code:


'''
in _ s d=[] n=0
in i s d=0 n=2
out out_v v
out out_e s
out arrow_v v
out arrow_f s
'''
from mathutils import Vector, Matrix
from sverchok.nodes.modifier_change.merge_mesh_2d import Debugger as debug

def get_arrow(hedge, scale=1):
    nor = Vector(hedge[1]) - Vector(hedge[0])
    nor = nor.to_track_quat('X', 'Z')
    m = Matrix.Translation(Vector(hedge[1])) * nor.to_matrix().to_4x4()
    tri = [Vector((1, 0, 0))*scale, Vector((-1, 1, 0))*scale, Vector((-1, -1, 0))*scale]
    return [[(m*v)[:] for v in tri]], [[(0,1,2)]]

if debug.data:
    if i > len(debug.data) - 1:
        out_v = [[0,0,0]]
    else:
        out_v = [debug.data[i]]
        if len(debug.data[i]) == 2:
            out_e = [[[0,1]]]
            arrow_v, arrow_f = get_arrow(debug.data[i], 0.1)
        elif len(debug.data[i]) > 2:
            out_e = [list(range(len(debug.data[i])))]
else:
    out_v = [[0,0,0]]


Output of this node will be all that is printed via Debug class available by index.
"""


class Debugger:
    data = []  # all print methods put data here
    msg = []  # all print methods put messages here
    half_edges = []
    _count = 0
    to_print = True

    @staticmethod
    def print_f(face, msg=None):
        if not Debugger.to_print:
            return
        if not face.outer:
            print('This is probably super boundless face')
            return
        print('{} - {}'.format(Debugger._count, msg or 'Face'))
        Debugger._count += 1
        loop = [face.outer.origin]
        next_hedge = face.outer.next
        count = 0
        while next_hedge != face.outer:
            loop.append(next_hedge.origin)
            next_hedge = next_hedge.next
            count += 1
            if count > 1000:
                print('Face ({}) does not ave a loop'.format(face.i))
                break
        Debugger.data.append(loop)
        Debugger.msg.append(msg or 'Face')

    @staticmethod
    def print_he(hedge, msg=None, gen_type='twin'):
        if not Debugger.to_print:
            return
        if not isinstance(hedge, list):
            hedge = [hedge]
        for h in hedge:
            print('{} - {}'.format(Debugger._count, msg or "Hedge"))
            Debugger._count += 1
            if gen_type == 'twin':
                Debugger.data.append([h.origin, h.twin.origin])
            else:
                Debugger.data.append([h.origin, h.next.origin])
            Debugger.msg.append(msg or "Hedge")

    @staticmethod
    def print_e(edge, msg=None):
        if not Debugger.to_print:
            return
        if not isinstance(edge, list):
            edge = [edge]
        for e in edge:
            print('{} - {}'.format(Debugger._count, msg or "Edge"))
            Debugger._count += 1
            Debugger.data.append([e.v1, e.v2])
            Debugger.msg.append([msg or "Edge"])

    @staticmethod
    def print_p(point, msg=None):
        if not Debugger.to_print:
            return
        print('{} - {}'.format(Debugger._count, msg or 'Point'))
        Debugger._count += 1
        Debugger.data.append([point.co])
        Debugger.msg.append(msg or "Point")

    @staticmethod
    def print(*msg):
        if not Debugger.to_print:
            return
        print(msg)

    @staticmethod
    def clear(to_print=True):
        # Should be called before using the class
        Debugger.data.clear()
        Debugger.msg.clear()
        Debugger._count = 0
        Debugger.to_print = to_print

    @staticmethod
    def set_dcel_data(half_edges):
        Debugger.half_edges = list(half_edges)
