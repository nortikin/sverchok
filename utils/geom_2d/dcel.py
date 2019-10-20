# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle

from .lin_alg import almost_equal, is_more, dot_product, is_ccw_polygon, cross_product
from .dcel_debugger import Debugger


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


class Point:
    accuracy = 1e-5

    def __init__(self, mesh, co):
        self.mesh = mesh
        self.co = co
        self.hedge = None

    def __str__(self):
        return "".join(["{:.2f}, ".format(co) for co in self.co])

    def __add__(self, other):
        # should returns object with class of inputs object
        # will be an error if class of input object has other init arguments
        return self.__class__(None, tuple(co1 + co2 for co1, co2 in zip(self.co, other.co)))

    def __sub__(self, other):
        # should returns object with class of inputs object
        # will be an error if class of input object has other init arguments
        return self.__class__(None, tuple(co1 - co2 for co1, co2 in zip(self.co, other.co)))

    def __mul__(self, other):
        # returns dot product or multiplication vector to scalar
        if isinstance(other, self.__class__):
            return dot_product(self.co, other.co)
        else:
            return self.__class__(None, [co * other for co in self.co])

    def length(self):
        # returns length as vector
        return sum([co ** 2 for co in self.co]) ** 0.5

    def normalize(self):
        # making the length of the vector 1.0
        mem_len = self.length()
        self.co = tuple(co / mem_len for co in list(self.co))
        return self

    def cross_product(self, other):
        return self.__class__(None, cross_product(self.co, other.co))


class HalfEdge:
    accuracy = 1e-5

    def __init__(self, mesh, point, face=None):
        self.mesh = mesh  # can be just None but in this case some method weren't be available
        self.origin = point
        self.face = face

        self.twin = None
        self.next = None
        self.last = None

        self._slop = None  # Should be recalculated if origin ot origin of twin are changed

    def __str__(self):
        return "Hedg({}, {})".format(self.origin, self.twin.origin if self.twin else self.next.origin)

    @property
    def ccw_hedges(self):
        # returns hedges originated in one point
        if not self.mesh:
            raise AttributeError("This method doesn't work with hedges({}) without link to a mesh."
                                 "Besides, mesh object should have proper number of half edges "
                                 "in hedges list".format(self))
        yield self
        next_edge = self.last.twin
        counter = 0
        while next_edge != self:
            yield next_edge
            next_edge = next_edge.last.twin
            counter += 1
            if counter > len(self.mesh.hedges):
                raise RecursionError('Hedge - {} does not have a loop'.format(self))

    @property
    def loop_hedges(self):
        # returns hedges bounding face
        if not self.mesh:
            raise AttributeError("This method doesn't work with hedges({}) without link to a mesh."
                                 "Besides, mesh object should have proper number of half edges "
                                 "in hedges list".format(self))
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
            if counter > len(self.mesh.hedges):
                raise RecursionError('Hedge - {} does not have a loop'.format(self))

    @property
    def slop(self):
        """
        Returns dot product of direction of half edges and -X direction in ccw order in such way
        Angle 45 from -X direction in ccw order returns 0.707
        Angle 90 from -X direction in ccw order returns 1.0
        Angle 180 from -X direction in ccw order returns 2.0
        Angle 360 or 0 from -X direction in ccw order returns 4.0
        :return: float
        """
        if self.twin._slop:
            self._slop = (self.twin._slop + 2) % 4
        elif almost_equal(self.origin.co[y], self.twin.origin.co[y], self.accuracy):  # is horizontal
            if is_more(self.origin.co[x], self.twin.origin.co[x], self.accuracy):
                self._slop = 4.0
            else:
                self._slop = 2.0
        else:
            direction = (self.twin.origin - self.origin).normalize()
            product = dot_product(direction.co, (1, 0))
            self._slop = product + 1 if direction.co[y] < 0 else 3 - product
        return self._slop


class Face:
    accuracy = 1e-5

    def __init__(self, mesh):
        self.mesh = mesh
        self._outer = None  # hedge of boundary loop
        self._inners = []  # hedges of hole loops

        self.select = False
        self.sv_data = dict()  # for any data which we would like to keep with face

    @property
    def is_unbounded(self):
        # returns true if face is boundless - includes all other faces of a mesh
        return not self.outer

    @property
    def outer(self):
        return self._outer

    @outer.setter
    def outer(self, value):
        if not self.mesh:
            raise AttributeError("This attribute is not available till the face does have link to a mesh")
        if not isinstance(value, self.mesh.HalfEdge):
            raise ValueError("HalfEdge type of object only can be set to outer attribute, "
                             "({}) was given".format(type(value)))
        self._outer = value

    @property
    def inners(self):
        # it would be nice to check whether all element of a list are correct, don't know how to do
        return self._inners

    @inners.setter
    def inners(self, value):
        if not self.mesh:
            raise AttributeError("This attribute is not available till the face does have link to a mesh")
        if not isinstance(value, self.mesh.HalfEdge):
            raise ValueError("HalfEdge type of object only can be set to outer attribute, "
                             "({}) was given".format(type(value)))
        self._outer = value



class DCELMesh:
    Point = Point
    HalfEdge = HalfEdge
    Face = Face
    accuracy = 1e-5

    def __init__(self, accuracy=None):
        self.points = []
        self.hedges = []
        self.faces = []
        if accuracy:
            self.set_accuracy(accuracy)

    @classmethod
    def set_accuracy(cls, accuracy):
        # This value is using for comparing float figures
        if isinstance(accuracy, int):
            accuracy = 1 / 10 ** accuracy
        if not (1e-1 > accuracy > 1e-15):
            raise ValueError("Accuracy should between 1^-1 and 1^-15, {} value was given".format(accuracy))
        cls.Point.accuracy = accuracy
        cls.HalfEdge.accuracy = accuracy
        cls.Face.accuracy = accuracy
        cls.accuracy = accuracy

    def from_sv_faces(self, verts, faces, face_mask=None, face_data=None):
        # todo: self intersection polygons? double repeated polygons???
        # face_data = {name of data: [value 1, val2, .., value n]} - number of values should be equal to number of faces
        # I'm not going use zip longest or  something else with face mask and face data inputs
        # Because I think it can lead to unexpected behaviour of algorithms, which will be difficult to debug
        if face_mask and len(face_mask) != len(faces):
            raise IndexError("Length of face_mask({}) input should be equal to"
                             " length of input faces({})".format(len(face_mask), len(faces)))
        if face_data and any([len(val) != len(faces) for val in face_data.values()]):
            bad_key, length = [(key, len(val)) for key, val in face_data.items() if len(val) != len(faces)][0]
            raise IndexError("Face data should be a dictionary."
                             "Each value should be a list with length equal to length of input faces"
                             "At list with key({}) length of input list({}) is not equal to "
                             "length of input faces({})".format(bad_key, length, len(faces)))
        half_edges_list = dict()
        unbounded_face = self.Face(self)
        self.faces.append(unbounded_face)
        len_added_points = len(self.points)
        self.points.extend([self.Point(self, co) for co in verts])

        # Generate outer faces and there hedges
        # face_data_iter is tricky iterator for distributing custom properties among faces, example:
        # d = {'a': [1, 2], 'b': [3, 4]}
        # >>> for names, values in zip(cycle([d.keys()]), zip(*d.values())):
        # ...     print('Next Face')
        # ...     for n, v in zip(names, values):
        # ...         print(n, v)
        # ...
        # Next Face
        # a 1
        # b 3
        # Next Face
        # a 2
        # b 4
        face_data_iter = zip(cycle([face_data.keys()]), zip(*face_data.values())) if face_data else cycle([None])
        for face, fm, fd in zip(faces, face_mask or cycle([False]), face_data_iter):
            face = face if is_ccw_polygon([verts[i] for i in face]) else face[::-1]
            f = self.Face(self)
            f.select = bool(fm)
            if fd:
                for property_name, value in zip(*fd):
                    f.sv_data[property_name] = value
            loop = []
            for i in range(len(face)):
                origin_i = face[i]
                next_i = face[(i + 1) % len(face)]
                half_edge = self.HalfEdge(self, self.points[origin_i + len_added_points], f)
                self.points[origin_i + len_added_points].hedge = half_edge  # this should be overrode several times
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
                outer_edge = self.HalfEdge(self, self.points[key[1] + len_added_points])
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

    def from_sv_edges(self, verts, edges):
        points = [self.Point(self, co) for co in verts]
        self.points.extend(points)
        coincidence_hedges = [[] for _ in range(len(points))]  # hedges coincident to points

        # Generate hedges
        for edge in edges:
            hedge1 = self.HalfEdge(self, points[edge[0]])
            hedge2 = self.HalfEdge(self, points[edge[1]])
            self.points[edge[0]].hedge = hedge1  # this should be overrode several times but looks okay
            self.points[edge[1]].hedge = hedge2
            hedge1.twin = hedge2
            hedge2.twin = hedge1
            coincidence_hedges[edge[0]].append(hedge1)
            coincidence_hedges[edge[1]].append(hedge2)
            self.hedges.extend([hedge1, hedge2])

        # Link hedges around all points
        for hedges in coincidence_hedges:
            hedges.sort(key=lambda hedge: hedge.slop)
            for i in range(len(hedges)):
                i_next = (i + 1) % len(hedges)
                hedges[i].last = hedges[i_next].twin
                hedges[i_next].twin.next = hedges[i]

    def faces_from_hedges(self):
        # Generate face list from half edge list
        # Output will be wrong if there are tales of edge net
        used = set()
        super_face = self.Face(self)
        faces = [super_face]

        # build outer faces and detect inner faces (holes)
        # if face is not ccw and there is no left neighbour it is boundless super face
        # if there is left neighbour the face should be stored with only inner component,
        # outer component will be find further
        for hedge in self.hedges:
            if hedge in used:
                continue
            min_hedge = min([hedge for hedge in hedge.loop_hedges], key=lambda he: (he.origin.co[x], he.origin.co[y]))
            _is_ccw = is_ccw_polygon(most_lefts=[min_hedge.last.origin.co, min_hedge.origin.co,
                                                 min_hedge.next.origin.co], accuracy=self.accuracy)
            # min hedge should be checked whether it look to the left or to the right
            # if to the right previous hedge should be taken
            # https://github.com/nortikin/sverchok/issues/2497#issuecomment-526096898
            min_hedge = min_hedge if min_hedge.slop > 2 else min_hedge.last
            if _is_ccw:
                face = self.Face(self)
                face.outer = hedge
                faces.append(face)
                for h in hedge.loop_hedges:
                    used.add(h)
                    h.face = face
            else:
                super_face.inners.append(min_hedge)
                for h in min_hedge.loop_hedges:
                    used.add(h)
                    h.face = super_face
        self.faces = faces

    def to_sv_mesh(self):
        # all elements of mesh should have correct links
        used = set()
        point_index = dict()
        sv_verts = []
        for hedge in self.hedges:
            if hedge in used:
                continue
            point_index[hedge.origin] = len(sv_verts)
            sv_verts.append(hedge.origin.co)
            for h in hedge.ccw_hedges:
                used.add(h)

        # This part of function creates faces in SV format
        # It ignores  boundless super face
        sv_faces = []
        for i, face in enumerate(self.faces):
            if face.inners and face.outer:
                'Face ({}) has inner components! Sverchok cant show polygons with holes.'.format(i)
            if not face.outer:
                continue
            sv_faces.append([point_index[hedge.origin] for hedge in face.outer.loop_hedges])

        return sv_verts, sv_faces

    def to_sv_edges(self):
        # Half edges data should be correct
        used = set()
        point_index = dict()
        sv_verts = []
        for hedge in self.hedges:
            if hedge in used:
                continue
            point_index[hedge.origin] = len(sv_verts)
            sv_verts.append(hedge.origin.co)
            for h in hedge.ccw_hedges:
                used.add(h)

        # This part of function creates faces in SV format
        # It ignores  boundless super face
        sv_edges = []
        for hedge in self.hedges:
            sv_edges.append((point_index[hedge.origin], point_index[hedge.twin.origin]))

        return sv_verts, sv_edges

    def dissolve_selected_faces(self):

        # mark unused hedges and faces
        boundary_hedges = []
        un_used_hedges = set()
        for face in self.faces:
            if face.select:
                for hedge in face.outer.loop_hedges:
                    if hedge.twin.face.select:
                        un_used_hedges.add(hedge)
                    else:
                        boundary_hedges.append(hedge)
        Debugger.add_hedges(boundary_hedges)
        # create new faces
        used = set()
        new_faces = []
        for hedge in boundary_hedges:
            if hedge in used:
                continue
            used.add(hedge)
            face = self.Face(self)
            new_faces.append(face)
            face.select = True
            face.outer = hedge
            hedge.face = face
            for ccw_hedge in hedge.ccw_hedges:
                if id(ccw_hedge) != id(hedge) and not ccw_hedge.face.select:
                    break
            last_hedge = ccw_hedge.twin
            hedge.last = last_hedge
            last_hedge.next = hedge
            used.add(last_hedge)
            last_hedge.face = face
            count = 0
            current_hedge = last_hedge
            while id(current_hedge) != id(hedge):
                for ccw_hedge in current_hedge.ccw_hedges:
                    if id(ccw_hedge) != id(hedge) and not ccw_hedge.face.select:
                        break
                last_hedge = ccw_hedge.twin
                used.add(last_hedge)
                last_hedge.face = face
                current_hedge.last = last_hedge
                last_hedge.next = current_hedge
                current_hedge = last_hedge
                count += 1
                if count > len(self.hedges):
                    raise RecursionError("Dissolve face algorithm can't built a loop from hedge - {}".format(hedge))
        # update faces
        self.faces = [face for face in self.faces if not face.select]
        self.faces.extend(new_faces)
        # update hedges
        self.hedges = [hedge for hedge in self.hedges if hedge not in un_used_hedges]
        # todo how to rebuilt points list
