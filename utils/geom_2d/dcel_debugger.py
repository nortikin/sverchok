# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain
from functools import wraps


x, y, z = 0, 1, 2


"""
The sooner the DCEL does not have any indexes of its elements
the difficulties to debug algorithm which run with such data structure.
The class below can be used for recording any element of DCEL in class variable
which can be visualized by Sverchok via SN light.

Example of script node code:


'''
in index s d=0 n=2
out v v
out f s
'''

from sverchok.utils.geom_2d.dcel import Debugger as D
v, f = D.printed_to_sv_mesh(index)
v, f = [v], [f]

Output of this node will be all that is printed via Debug class available by index.
"""


class Debugger:
    Point = None
    HalfEdge = None
    Face = None
    data = []  # all print methods put data here
    msg = []  # all print methods put messages here
    half_edges = []
    _count = 0
    to_print = True

    @classmethod
    def print(cls, dcel_object, msg=None):
        # prints half edges
        if not cls.to_print:
            return
        if not dcel_object:
            print("!!!You have tried to print nothing!!!")
            return
        if not isinstance(dcel_object, list):
            dcel_object = [dcel_object]
        for db in dcel_object:
            cls.data.append(db)
            print('{} - {}'.format(cls._count, msg if msg is not None else db))
            cls._count += 1
            cls.msg.append(msg if msg is not None else db)

    @classmethod
    def print_function(cls, func):
        # decorator for inspecting a functions
        @wraps(func)
        def wrapper(*args, **kwargs):
            cls.clear()
            [cls.print(arg, 'Args from function -{}'.format(func.__name__)) for arg in args]
            [cls.print(kwargs[kw], 'Kwarg {} from function -{}'.format(kw, func.__name__)) for kw in kwargs]
            res = func(*args, **kwargs)
            [cls.print(r, 'Result of the function 0{}'.format(func.__name__)) for r in res]
            return res
        return wrapper

    @classmethod
    def add_hedges(cls, hedges):
        if isinstance(hedges, list):
            cls.half_edges.extend(hedges)
        else:
            cls.half_edges.append(hedges)

    @classmethod
    def clear(cls, to_print=True):
        # clear all recoded data, should be coled before each iteration of a node
        cls.data.clear()
        cls.msg.clear()
        cls._count = 0
        cls.to_print = to_print
        cls.half_edges.clear()

    # #########__for draw function__#######

    @classmethod
    def _rotate_by_direction(cls, points, normal):
        # https://habr.com/ru/post/131931/
        x_axis = normal
        y_axis = normal.cross_product(cls.Point(None,(0, 0, 1)))
        return [x_axis * p.co[x] + y_axis * p.co[y] for p in points]

    @classmethod
    def _get_arrow(cls, edge, scale=1.0):
        nor = (edge[1] - edge[0]).normalize()
        tri = [cls.Point(None, (1, 0, 0)) * scale, cls.Point(None, (-1, 1, 0)) * scale,
               cls.Point(None, (-1, -1, 0)) * scale]
        tri = cls._rotate_by_direction(tri, nor)
        tri = [p + edge[1] for p in tri]
        return tri, (4, 5, 6)

    @classmethod
    def _shift_hedge(cls, hedge, scale=1.0):
        v1 = (hedge.origin - hedge.twin.origin).normalize()
        v2 = cls.Point(None, (0, 0, 1))
        nor = v1.cross_product(v2) * scale
        edge = ((hedge.origin - (v1 * (scale * 2))), hedge.twin.origin + (v1 * (scale * 2)))
        return [p + nor for p in edge]

    @classmethod
    def _edge_to_face(cls, edge):
        return [*edge, edge[1] + cls.Point(None, (0, 0, 0.1)), edge[0] + cls.Point(None,(0, 0, 0.1))], (0, 1, 2, 3)

    @classmethod
    def _hedge_to_sv(cls, hedge, scale=0.1):
        edge_co = cls._shift_hedge(hedge, scale)
        hedge_face, hedge_i = cls._edge_to_face(edge_co)
        arrow_v, arrow_i = cls._get_arrow(edge_co, scale)
        return [p.co for p in hedge_face] + [p.co for p in arrow_v], [hedge_i, arrow_i]

    @classmethod
    def _point_to_sv(cls, point, scale=0.1):
        p = [cls.Point(None, (1, 0, 0)) * scale, cls.Point(None, (0, 1, 0)) * scale,
             cls.Point(None, (-1, 0, 0)) * scale, cls.Point(None, (0, -1, 0)) * scale]
        p = [p + point for p in p]
        return [p.co for p in p], [(0, 1, 2, 3)]

    @classmethod
    def _face_to_sv(cls, face, scale=0.1):
        if not face.outer and not face.inners:
            print("!!!You have tried to print empty face!!!")
        out = []
        for hedge in chain([face.outer], face.inners):
            print("type hedge!!!", type(hedge))
            v, f = cls._hedge_to_sv(hedge, scale)
            out.append(([v], [f]))
        print("!!!!!!!!!!!!!!!!!!!", out)
        return zip(*out)

    @classmethod
    def hedges_to_sv_mesh(cls, scale=0.1, clear=False):
        # for visualization all DCEL data
        if not cls.half_edges:
            print("DCEL DEBUGER: You should record your half edges into the class before"
                  " calling the method ({})".format(cls.hedges_to_sv_mesh.__name__))
        out = []
        for i, hedge in enumerate(cls.half_edges):
            v, f = cls._hedge_to_sv(hedge, scale)
            out.append([v, f])
        if clear:
            cls.half_edges.clear()
        return out

    @classmethod
    def printed_to_sv_mesh(cls, index):
        cls.init_dcel_classes()
        if not cls.data:
            print("DCEL DEBUGER: You should record your data into the class before"
                  " calling the method ({})".format(cls.printed_to_sv_mesh.__name__))
        item = cls.data[index] if len(cls.data) > index else ([[(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)]], [[(0, 1, 2)]])
        print('item' , item)
        if isinstance(item, cls.HalfEdge):
            return cls._hedge_to_sv(item)
        elif isinstance(item, cls.Point):
            return cls._point_to_sv(item)
        elif isinstance(item, cls.Face):
            return cls._face_to_sv(item)
        else:
            return [(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)], [(0, 1, 2)]

    @classmethod
    def init_dcel_classes(cls):
        if cls.Point is None:
            from .dcel import Point, HalfEdge, Face
            cls.Point = Point
            cls.HalfEdge = HalfEdge
            cls.Face = Face
