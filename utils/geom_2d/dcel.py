# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import cycle, chain
from typing import List, Union, Set

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
        return "Point"

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
        self.co = (self.co[0] / mem_len, self.co[1] / mem_len, self.co[2] / mem_len)
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

        self.left = None  # Information about nearest left neighbour for hole detection, intersection algorithm user
        self.flags = set()  # For any value wich an algorithm would like to keep with object, only add or remove
        self._slop = None  # Should be recalculated if origin ot origin of twin are changed

    def __str__(self):
        return "Hedge"

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
    def cw_hedges(self):
        # returns hedges originated in one point
        if not self.mesh:
            raise AttributeError("This method doesn't work with hedges({}) without link to a mesh."
                                 "Besides, mesh object should have proper number of half edges "
                                 "in hedges list".format(self))
        yield self
        next_edge = self.twin.next
        counter = 0
        while next_edge != self:
            yield next_edge
            next_edge = next_edge.twin.next
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
        while id(next_edge) != id(self):
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
        if self._slop:
            pass
        elif self.twin._slop:
            self._slop = (self.twin._slop + 2) % 4 if self.twin._slop != 2 else 4  # corner case for horizontal
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

        self.select = False  # actually should be careful with this parameter, some algorithm can use it or not
        self.flags = set()  # For any value wich an algorithm would like to keep with object, only add or remove
        self.sv_data = dict()  # for any data which we would like to keep with face

    def __str__(self):
        return 'Face'

    @property
    def is_unbounded(self):
        # returns true if face is boundless - includes all other faces of a mesh
        return not self.outer

    @property
    def outer(self):
        return self._outer

    @outer.setter
    def outer(self, value):
        self.check_mesh()
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
        self.check_mesh()
        if not isinstance(value, list) and not isinstance(value[0], self.mesh.HalfEdge):
            raise ValueError("List of HalfEdge(s) only can be set to inners attribute, "
                             "({}) was given".format(type(value)))
        self._inners = value

    def insert_holes(self, sv_verts, sv_faces, face_selection=None, face_data=None):
        # not sure super useful, holes should not intersect with the face
        self.check_mesh()
        hole_mesh = generate_dcel_mesh(self.mesh, sv_verts, sv_faces, face_selection, face_data,  new_mesh=True)
        self.inners.extend(hole_mesh.unbounded.inners)
        [setattr(obj, 'mesh', self.mesh) for obj in chain(hole_mesh.points, hole_mesh.hedges, hole_mesh.faces)]
        self.mesh.points.extend(hole_mesh.points)
        self.mesh.hedges.extend(hole_mesh.hedges)
        self.mesh.faces.extend(hole_mesh.faces)
        for start_hedge in hole_mesh.unbounded.inners:
            for hedge in start_hedge.loop_hedges:
                hedge.face = self

    def check_mesh(self):
        # Ensure that the face belongs to a mesh
        if not self.mesh:
            raise AttributeError("This attribute is not available till the face does have link to a mesh")


class DCELMesh:
    Point = Point
    HalfEdge = HalfEdge
    Face = Face
    accuracy = 1e-5

    def __init__(self, accuracy=None):
        self.points = []
        self.hedges = []
        self.faces = []
        self.unbounded = self.Face(self)
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

    def from_sv_faces(self, verts, faces, face_selection=None, face_data=None):
        # face_data = {name of data: [value 1, val2, .., value n]} - number of values should be equal to number of faces
        generate_dcel_mesh(self, verts, faces, face_selection, face_data, False)

    def from_sv_edges(self, verts, edges):
        # Probably it is worth take in account such cases as: edge with 0 length at least
        # Interesting that this method makes next attribute of end of an edge linked to a twin
        edges = [edge for edge in edges if
                 not all([almost_equal(co1, co2, self.accuracy) for co1, co2 in zip(verts[edge[0]], verts[edge[1]])])]

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

    def generate_faces_from_hedges(self):
        # Generate face list from half edge list
        # Tail edges will be dissolving
        # Left component of hedges is taken in account
        # build outer faces and detect inner faces (holes)
        # if face is not ccw and there is no left neighbour it is boundless super face
        # if there is left neighbour the face should be stored with only inner component,
        # outer component will be find further

        # will detect tails first
        used = set()  # type: Set[HalfEdge]
        tail_key = 'tail'
        rebuild = False  # if there are tails some points and half edges can be loosed
        for hedge in self.hedges:
            if hedge in used:
                continue
            # https://github.com/nortikin/sverchok/pull/2623#issuecomment-546570210
            used_in_loop = set()  # type: Set[HalfEdge]
            for loop_hedge in hedge.loop_hedges:
                if loop_hedge.twin not in used_in_loop:
                    used_in_loop.add(loop_hedge)
                else:
                    # this is tail, useless, for del method but not only
                    loop_hedge.flags.add(tail_key)
                    loop_hedge.twin.flags.add(tail_key)
                    rebuild = True

        faces = []  # type: List[Face]
        min_hedges = set()  # type: Set[HalfEdge]  # all detected leftmost half edges of evry loop, not tails
        inner_hedges = []  # type: List[List[HalfEdge]]  # multiple loops can be produced be desolving tails algorithm
        # relink half edges
        # after this process it will be possible to get from tail to loop but impossible from loop to tail
        # actually this process lead to loosing information which it could be useful
        # dissolving algorithm can create several loops from one but they are related with each other:
        # - if at least one of them is outer loop so the rest are inner components of this one
        # - or if they all are inner so they either belong to boundless face or are inside some another face
        # Also left attribute can have links to tails what make the situation more complicated
        used.clear()
        for hedge in self.hedges:
            if hedge in used:
                continue
            if tail_key in hedge.flags:
                # avoid start form tails
                continue

            # Start handling a loop
            loop_hedges = []  # type: List[HalfEdge]
            for loop_hedge in hedge.loop_hedges:
                loop_hedges.append(loop_hedge)
                # links can be changed only when sub loop is left
                if tail_key in loop_hedge.flags and tail_key not in loop_hedge.last.flags:
                    # this case about when previous step was from sub loop to tail
                    last_hedge = loop_hedge.last  # origin of next hedge is in place where tail connects with a face
                    for cw_hedge in loop_hedge.cw_hedges:
                        # Try to find last normal half edge for next normal half edge
                        if id(cw_hedge) != id(loop_hedge) and tail_key not in cw_hedge.flags:
                            # check either there are other tails in the point
                            next_hedge = cw_hedge
                            break
                    next_hedge.last = last_hedge
                    last_hedge.next = next_hedge

            # detect new sub loops, figure out weather loop is ccw or cw
            # after code above loop_hedges attribute returns new sub loops according start hedge
            new_outer = None  # type: Union[None, HalfEdge]
            new_inners = []  # type: List[HalfEdge]
            for loop_hedge in loop_hedges:
                if tail_key in loop_hedge.flags:
                    used.add(loop_hedge)
                    # just ignore tail
                    continue
                elif loop_hedge in used:
                    # avoid reconsidering sub loop
                    continue
                else:
                    # the start edge for sub loop is found
                    # mark all hedges of the sub loop for avoiding them later
                    [used.add(hedge) for hedge in loop_hedge.loop_hedges]
                    min_hedge = min([hedge for hedge in loop_hedge.loop_hedges],
                                    key=lambda he: (he.origin.co[x], he.origin.co[y]))
                    min_hedges.add(min_hedge)  # avoiding extra calculation later
                    _is_ccw = is_ccw_polygon(most_lefts=[min_hedge.last.origin.co, min_hedge.origin.co,
                                                         min_hedge.next.origin.co], accuracy=self.accuracy)
                    if not _is_ccw:
                        new_inners.append(min_hedge)
                    elif _is_ccw and new_outer is not None:
                        raise ValueError("During dissolving edges algorithm only one ccw face can be created")
                    else:
                        new_outer = loop_hedge
            # handle case when after dissolving tails there are at list one outer face
            if new_outer:
                face = self.Face(self)
                face.outer = new_outer
                faces.append(face)
                for h in new_outer.loop_hedges:
                    h.face = face
                for start_hedge in new_inners:
                    face.inners.append(start_hedge)
                    for h in start_hedge.loop_hedges:
                        h.face = face

            # case when only inners loops was found
            # if left neighbour is None this mean that the inner face is a hole of boundless face in either way
            # if left is not None it is impossible to say which face inner faces belongs at this stage
            # if at list one left neighbour of inner start half edge is None then
            # all inner loops belong to boundless face
            elif new_inners:
                # new inners should be also check because after dissolving half edges some loops can produce nothing
                belong_to_boundless = any([start_hedge.left is None for start_hedge in new_inners])
                if belong_to_boundless:
                    for start_hedge in new_inners:
                        self.unbounded.inners.append(start_hedge)
                        for loop_hedge in start_hedge.loop_hedges:
                            loop_hedge.face = self.unbounded
                else:
                    # it impossible to say to which face the inner loops belong at this stage
                    # it is also possible that they belong to boundless face
                    inner_hedges.append(new_inners)

        used.clear()  # only for start half edges which are leftmost half edges
        # This part about holes detection
        for start_hedges in inner_hedges:

            # check first probably some of the loops already was assigned to a face
            # it is possible if some disjoint loop lies to the right of one sub loop face
            # in this case during ahndling the loop sub loop also will be assigned to face
            assigned_face = None  # type: Union[None, Face]
            for start_hedge in start_hedges:
                if start_hedge.face and start_hedge.face.outer:
                    assigned_face = start_hedge.face  # this can be weather boundless face or outer face
                    break  # this means that hedge loops can belongs only one face
            if assigned_face:
                for start_hedge in start_hedges:
                    if start_hedge not in used:
                        used.add(start_hedge)
                        assigned_face.inners.append(start_hedge)  # repeat of half edges should be avoided
                        for hedge in start_hedge.loop_hedges:
                            hedge.face = assigned_face

            # Well, we have bad luck and no one loop was already marked in given sequence
            # initialisation of walk to leftward direction should be done
            # choose a hedge for start, does not matter which from the set
            left_hedges = [start_hedges[0]]  # type: List[HalfEdge] # list of start hedges of evry inner loop detected
            count = 0
            while not left_hedges[-1].left or not left_hedges[-1].left.face or not left_hedges[-1].left.face.outer:
                # At first check can be next jump done
                if not left_hedges[-1].left:
                    break

                # First of all try to find next loop
                start_loop = None  # type: Union[None, HalfEdge]
                # It is necessary to know what is coming next, whether it tail half edge or normal half edge
                if tail_key in left_hedges[-1].left.flags:
                    # it looks that iterate over tail half edges is not a good idea
                    # it is possible to get into endless loop,
                    # when leftmost point of a loop has left attribute with tail
                    # which leis right from left side of the loop and joined to it
                    # it will be batter to make next jump immediately
                    # but if one of ccw half edges of tail has outer face it means it is boundary face
                    # or if it is inner component then next hole is found and should be iterated
                    # or if twin of one of ccw half edges of tail ahs outer face it means we also het into next hole
                    jump = True  # True if boundary face or next hole in ccw hedges was not found
                    for ccw_hedge in left_hedges[-1].left.ccw_hedges:
                        if ccw_hedge.face and ccw_hedge.face.outer:
                            # the boundary face is found and should be linked to last left half edge
                            # it will be probably better to relink left half edge to half edge with boundary face
                            left_hedges[-1].left = ccw_hedge  # probably not vary nice to do
                            jump = Face
                            break  # todo check the end of while
                        elif ccw_hedge.face and ccw_hedge.face.inners:
                            # new next hole is found
                            start_loop = ccw_hedge
                            jump = False
                            break
                        elif ccw_hedge.twin.face:
                            # this also mean that next hole is found
                            start_loop = ccw_hedge
                            jump = False
                            break
                    if jump:
                        left_hedges.append(left_hedges[-1].left)
                    # start_tail = left_hedges[-1].left
                    # tail_hedges = [start_tail]
                    # next_tail = start_tail
                    # while True:
                    #     if tail_key in next_tail.next.flags:
                    #         # everything okay we are still in tail loop
                    #         next_tail = next_tail.next
                    #         tail_hedges.append(next_tail)
                    #     else:
                    #         # we step out from tail loop, switch to another side
                    #         # so it is possible move further in normal way
                    #         start_loop = next_tail.next
                    #         break
                    #     if id(next_tail) == id(start_tail):
                    #         # this is the end of the loop
                    #         break
                    #     count += 1
                    #     if count > len(self.hedges):
                    #         raise RecursionError('Tail loop can not find the edn of its tail')
                    # # We found tail loop it means inner face without twin outer face
                    # min_tail_hedge = min(tail_hedges, key=lambda he: (he.origin.co[x], he.origin.co[y]))
                    # left_hedges.append(min_tail_hedge)  # next left half edge was found
                else:
                    # we are in a normal loop
                    start_loop = left_hedges[-1].left
                if start_loop:
                    # this means we have jumped to a normal loop or via tail joined to normal loop
                    # will find leftmost half edge
                    for hedge in start_loop.loop_hedges:
                        if hedge in min_hedges:
                            left_hedges.append(hedge)
                            break
                count += 1
                if count > len(self.hedges):
                    raise RecursionError('Hedge of hole cant find outer face')

            # all left half edges was found and last left half edge keeps information about boundary face
            # interesting thing about left hedges is the list can include tails which are useless in face creating
            # set boundary face
            if not left_hedges[-1].left:
                face = self.unbounded
            else:
                face = left_hedges[-1].left.face
            # make links between boundary face and inner loops
            for start_hedge in left_hedges:
                if tail_key in start_hedge.flags:
                    continue
                if start_hedge in used:
                    continue
                face.inners.append(start_hedge)
                used.add(start_hedge)  # this should be enuff
                for hedge in start_hedge.loop_hedges:
                    hedge.face = face
            # all sub loops also can be assigned to founded face
            for start_hedge in start_hedges:
                if start_hedge in used:
                    continue
                face.inners.append(start_hedge)
                used.add(start_hedge)
                for hedge in start_hedge.loop_hedges:
                    hedge.face = face

        self.faces = faces

        if rebuild:
            self.del_loose_hedges(tail_key)

    def to_sv_mesh(self, edges=True, faces=True, only_select=False, del_face_flag=None):
        # all elements of mesh should have correct links
        # will create only selected faces if only_select is True
        sv_points, point_index = generate_sv_points(self)
        if edges and not faces:
            sv_edges = generate_sv_edges(self, point_index)
            return sv_points, sv_edges
        elif faces and not edges:
            sv_faces = generate_sv_faces(self, point_index, only_select, del_face_flag)
            return sv_points, sv_faces
        else:
            sv_edges = generate_sv_edges(self, point_index)
            sv_faces = generate_sv_faces(self, point_index, only_select, del_face_flag)
            return sv_points, sv_edges, sv_faces

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

    def del_loose_hedges(self, flag=None):
        # flag means that half edges with the value will be deleted
        if flag:
            hedges = []
            for hedge in self.hedges:
                if flag in hedge.flags:
                    hedge.mesh = None
                else:
                    hedges.append(hedge)
            self.hedges = hedges
        else:
            self.hedges = [hedge for hedge in self.hedges if hedge.mesh]
        used = set()
        points = []
        for hedge in self.hedges:
            if hedge.origin not in used:
                used.add(hedge.origin)
                points.append(hedge.origin)
                hedge.origin.hedge = hedge  # point can have link to not existing half edge
        self.points = points

    def del_face(self, face):
        # does not remove face from self.faces, only switch link from face to unbounded face
        # not sure that this is good idea, probably should not be used
        # this can lead to wrong topology, difficult to predict
        if face.is_unbounded:
            raise ValueError('Unbounded face can not be deleted')
        for start_hedge in chain([face.outer] if face.outer else [], face.inners):
            self.unbounded.inners.append(start_hedge)
            for hedge in start_hedge.loop_hedges:
                hedge.face = self.unbounded
        face.mesh = None


def generate_dcel_mesh(mesh, verts, faces, face_selection=None, face_data=None, new_mesh=False):
    # todo: self intersection polygons? double repeated polygons???
    # face_data = {name of data: [value 1, val2, .., value n]} - number of values should be equal to number of faces
    # I'm not going use zip longest or  something else with face mask and face data inputs
    # Because I think it can lead to unexpected behaviour of algorithms, which will be difficult to debug
    # If mesh is None all will be bind to new instent
    if face_selection and len(face_selection) != len(faces):
        raise IndexError("Length of face_mask({}) input should be equal to"
                         " length of input faces({})".format(len(face_selection), len(faces)))
    if face_data and any([len(val) != len(faces) for val in face_data.values()]):
        bad_key, length = [(key, len(val)) for key, val in face_data.items() if len(val) != len(faces)][0]
        raise IndexError("Face data should be a dictionary."
                         "Each value should be a list with length equal to length of input faces"
                         "At list with key({}) length of input list({}) is not equal to "
                         "length of input faces({})".format(bad_key, length, len(faces)))
    if new_mesh:
        mesh = type(mesh)(mesh.accuracy)  # can bring trouble with isinstance, not sure
    half_edges_list = dict()
    len_added_points = len(mesh.points)
    mesh.points.extend([mesh.Point(mesh, co) for co in verts])

    # Generate outer faces and there hedges
    # face_data_iter is tricky iterator for distributing custom properties among faces, example:
    # d = {'a': [1, 2], 'b': [3, 4]}
    # >>> for names, values in zip(cycle([d.keys()]), zip(*d.values())):
    # ...     print('Next Face')
    # ...     for n, v in zip(names, values):
    # ...         print(n, v)
    # ...
    # Next Face  # a 1  # b 3  # Next Face  # a 2  # b 4
    face_data_iter = zip(cycle([face_data.keys()]), zip(*face_data.values())) if face_data else cycle([None])
    for face, fm, fd in zip(faces, face_selection or cycle([False]), face_data_iter):
        face = face if is_ccw_polygon([verts[i] for i in face]) else face[::-1]
        f = mesh.Face(mesh)
        f.select = bool(fm)
        if fd:
            for property_name, value in zip(*fd):
                f.sv_data[property_name] = value
        loop = []
        for i in range(len(face)):
            origin_i = face[i]
            next_i = face[(i + 1) % len(face)]
            half_edge = mesh.HalfEdge(mesh, mesh.points[origin_i + len_added_points], f)
            mesh.points[origin_i + len_added_points].hedge = half_edge  # this should be overrode several times
            loop.append(half_edge)
            half_edges_list[(origin_i, next_i)] = half_edge
        for i in range(len(face)):
            loop[i].last = loop[(i - 1) % len(face)]
            loop[i].next = loop[(i + 1) % len(face)]
        f.outer = loop[0]
        mesh.faces.append(f)
    mesh.hedges.extend(list(half_edges_list.values()))

    # to twin hedges and create hedges of unbounded face
    outer_half_edges = dict()
    for key in half_edges_list:
        half_edge = half_edges_list[key]
        if key[::-1] in half_edges_list:
            half_edge.twin = half_edges_list[key[::-1]]
            half_edges_list[key[::-1]].twin = half_edge
        else:
            outer_edge = mesh.HalfEdge(mesh, mesh.points[key[1] + len_added_points])
            outer_edge.face = mesh.unbounded
            half_edge.twin = outer_edge
            outer_edge.twin = half_edge
            if key[::-1] in outer_half_edges:
                raise Exception("It looks like input mesh has adjacent faces with only one common point"
                                "Handle such meshes does not implemented yet.")
            outer_half_edges[key[::-1]] = outer_edge
    mesh.hedges.extend(list(outer_half_edges.values()))

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
        mesh.unbounded.inners.append(outer_hedge)
        [used.add(hedge) for hedge in outer_hedge.loop_hedges]
    return mesh


def generate_sv_points(dcel_mesh):
    used = set()
    point_index = dict()
    sv_verts = []
    for hedge in dcel_mesh.hedges:
        if hedge in used:
            continue
        point_index[hedge.origin] = len(sv_verts)
        sv_verts.append(hedge.origin.co)
        for h in hedge.ccw_hedges:
            used.add(h)
    return sv_verts, point_index


def generate_sv_edges(dcel_mesh, point_index):
    sv_edges = []
    used = set()
    for hedge in dcel_mesh.hedges:
        if hedge in used:
            continue
        used.add(hedge)
        used.add(hedge.twin)
        sv_edges.append((point_index[hedge.origin], point_index[hedge.twin.origin]))
    return sv_edges


def generate_sv_faces(dcel_mesh, point_index, only_select=False, del_flag=None):
    # This part of function creates faces in SV format
    # It ignores  boundless super face
    sv_faces = []
    for i, face in enumerate(dcel_mesh.faces):
        if face.inners and face.outer:
            'Face ({}) has inner components! Sverchok cant show polygons with holes.'.format(i)
        if not face.outer or del_flag in face.flags:
            continue
        if only_select and not face.select:
            continue
        sv_faces.append([point_index[hedge.origin] for hedge in face.outer.loop_hedges])
    return sv_faces
