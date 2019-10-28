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
in _ s
in index s d=0 n=2
in number s d=0 n=2
in mode s d=0 n=2
in scale s d=0.1 n=2
out v v
out f s
out sv v
out sf s
'''

from sverchok.utils.geom_2d.dcel import Debugger as D
v, f, sv, sf = D.printed_to_sv_mesh(index, scale=scale)
#v, f, sv, sf = D.hedges_to_sv_mesh(index, number, mode, scale=scale, clear=True)


Output of this node will be all that is printed via Debug class available by index.
"""


class Debugger:
    Point = None
    HalfEdge = None
    Face = None
    Edge = None
    DCELMesh = None
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
            return cls.print_warning('You have tried to print nothing')
        if not isinstance(dcel_object, list):
            dcel_object = [dcel_object]
        for db in dcel_object:
            cls.data.append(db)
            cls.msg.append(msg if msg is not None else db)
            blank_msg = '  {}  '.format(msg)
            print('{} - {:*^50}'.format(cls._count, blank_msg if msg is not None else str(db)))
            cls._count += 1

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

    @classmethod
    def print_warning(cls, msg):
        print("{:!^50}".format(msg))

    # #########__for draw function__#######

    @staticmethod
    def _ccw_hedges(hedge):
        # returns hedges originated in one point
        yield hedge
        next_edge = hedge.last.twin
        while next_edge != hedge:
            yield next_edge
            next_edge = next_edge.last.twin

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
        return [p.co for p in hedge_face] + [p.co for p in arrow_v], [hedge_i, arrow_i]  # single sv object

    @classmethod
    def _edge_to_sv(cls, edge):
        edge_co = edge.up_p, edge.low_p
        edge_face, edge_i = cls._edge_to_face(edge_co)
        return [p.co for p in edge_face], [edge_i]

    @classmethod
    def _point_to_sv(cls, point, scale=0.1):
        p = [cls.Point(None, (1, 0, 0)) * scale, cls.Point(None, (0, 1, 0)) * scale,
             cls.Point(None, (-1, 0, 0)) * scale, cls.Point(None, (0, -1, 0)) * scale]
        p = [p + point for p in p]
        return [p.co for p in p], [(0, 1, 2, 3)]

    @classmethod
    def _face_to_sv(cls, face, scale=0.1):
        if not face.outer and not face.inners:
            cls.print_warning("You have tried to print empty face")
        out = []
        for hedge in chain([face.outer] if face.outer else [], face.inners):
            v, f = cls._hedge_to_sv(hedge, scale)
            out.append((v, f))
        return zip(*out)

    @classmethod
    def hedges_to_sv_mesh(cls, selection_index=None, number=0, mode=None, scale=0.1, clear=False):
        # for visualization all DCEL data
        # modes: 0 - ccw hedges, 1 - loop hedges
        cls.init_dcel_classes()
        empty_mesh = [[[(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)]], [[(0, 1, 2)]]]
        if not cls.half_edges:
            print("DCEL DEBUGER: You should record your half edges into the class before"
                  " calling the method ({})".format(cls.hedges_to_sv_mesh.__name__))
            return empty_mesh
        out = dict()
        select_out = dict()
        for i, hedge in enumerate(cls.half_edges):
            if selection_index and selection_index == i:
                continue
            v, f = cls._hedge_to_sv(hedge, scale)
            out[hedge] = (v, f)

        if selection_index is not None:
            if not len(cls.half_edges) > selection_index:
                if clear:
                    cls.half_edges.clear()
                print('{:~^50}'.format('Nothing to print. Try to lessen the index'))
                return list(zip(*[out[key] for key in out if key not in select_out])) + empty_mesh
            select_hedge = cls.half_edges[selection_index]
            if mode == 0:
                for i, ccw_hedge in enumerate(cls._ccw_hedges(select_hedge)):
                    if i > number:
                        break
                    v, f = cls._hedge_to_sv(ccw_hedge, scale)
                    select_out[ccw_hedge] = (v, f)

        if clear:
            cls.half_edges.clear()
        return list(zip(*[out[key] for key in out if key not in select_out])) + list(zip(*select_out.values()))

    @classmethod
    def printed_to_sv_mesh(cls, index, scale=0.1):
        cls.init_dcel_classes()
        empty_mesh = [[[(0, 0, 0), (0.01, 0, 0), (0, 0.01, 0)]], [[(0, 1, 2)]]]
        is_index = len(cls.data) > index
        item = cls.data[index] if is_index else None
        msg = 'print {:~^50} - {}'.format(item.__class__.__name__, cls.msg[index]) if is_index else ''
        if not is_index:
            if not cls.data:
                print("DCEL DEBUGER: You should record your data into the class before"
                      " calling the method ({})".format(cls.printed_to_sv_mesh.__name__))
            else:
                print('{:~^50}'.format('Nothing to print. Try to lessen the index'))
            return empty_mesh + empty_mesh
        elif type(item).__name__ == 'HalfEdge':
            v, f = cls._hedge_to_sv(item, scale)
            check_attrs = {'mesh', 'origin', 'face', 'next', 'last', 'twin'}
            warning = ''.join(['{} is None, '.format(attr) for attr in check_attrs if getattr(item, attr) is None])
            warning = ' WARNING - ' + warning if warning else ''
            print(msg + warning)
            return [v], [f], empty_mesh[0], empty_mesh[1]
        elif type(item).__name__ == 'Point':
            v, f = cls._point_to_sv(item, scale)
            check_attrs = {'mesh', 'co', 'hedge'}
            warning = ''.join(['{} is None, '.format(attr) for attr in check_attrs if getattr(item, attr) is None])
            warning = ' WARNING - ' + warning if warning else ''
            print(msg + warning)
            return [v], [f], empty_mesh[0], empty_mesh[1]
        elif type(item).__name__ == 'Face':
            check_attrs = {'mesh', 'outer'}
            warning = ''.join(['{} is None, '.format(attr) for attr in check_attrs if getattr(item, attr) is None])
            warning = ' WARNING - ' + warning if warning else ''
            print(msg + warning)
            return list(cls._face_to_sv(item, scale)) + empty_mesh
        elif type(item).__name__ == 'Edge':
            v, f = cls._edge_to_sv(item)
            print(msg)
            return [v], [f], empty_mesh[0], empty_mesh[1]
        else:
            cls.print_warning("Can't print object with such name - {}".format(item.__class__.__name__))
            return empty_mesh

    @classmethod
    def init_dcel_classes(cls):
        # this function does not work properly
        # after pressing F8 button isinstance can't recognize equal objects came from different parts of the code

        from .dcel import Point
        # from sverchok.utils.geom_2d.sort_mesh import SortEdgeSweepingAlgorithm

        cls.Point = Point
        # cls.DCELMesh = DCELMesh
        # cls.HalfEdge = HalfEdge
        # cls.Face = Face
        # cls.Edge = SortEdgeSweepingAlgorithm
