# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from .lin_alg import almost_equal, is_less, is_more, cross_product, dot_product

from .dcel import Debugger


x, y, z = 0, 1, 2


class SortPointsUpDown:
    """
    This allowed sort points from upward to downward direction. 
    Besides points with equal Y coordinate are sorted from left to right.
    (0, 1, 0) < (0, 0, 0)
    (0, 1, 0) < (1, 1, 0)
    (0, 1.001, 0) == (0, 1.002, 0) if accuracy <= 1e-3

    Should be used with another class with "co" - (x, y, z) and "accuracy" - (float) attributes
    """

    def __lt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if is_less(-self.co[y], -other.co[y], self.accuracy):
            return True
        elif is_more(-self.co[y], -other.co[y], self.accuracy):
            return False
        elif is_less(self.co[x], other.co[x], self.accuracy):
            return True
        else:
            return False

    def __gt__(self, other):
        # Sorting of points from upper left point to lowest right point
        if is_more(-self.co[y], -other.co[y], self.accuracy):
            return True
        elif is_less(-self.co[y], -other.co[y], self.accuracy):
            return False
        elif is_more(self.co[x], other.co[x], self.accuracy):
            return True
        else:
            return False

    def __eq__(self, other):
        # Returns true if points are equal
        return (almost_equal(self.co[x], other.co[x], self.accuracy) and
                almost_equal(self.co[y], other.co[y], self.accuracy))

    def __ne__(self, other):
        # Returns false if points are not equal
        if not almost_equal(self.co[x], other.co[x], self.accuracy):
            return True
        elif not almost_equal(self.co[y], other.co[y], self.accuracy):
            return True
        else:
            return False

    def __hash__(self):
        return id(self)


class SortEdgeSweepingAlgorithm:
    """
    Sorting edges for sweeping line algorithm.
    Edges are sorted along horizontal sweeping line from left to right according their intersection with sweep line.
    If Edges intersects in one points they are sorted in cww order from -X direction.

    There is global event point parameter determining position of sweep line.
    It should be updated each time when sweep line is changing its position.
    """
    global_event_point = None
    accuracy = 1e-6

    def __init__(self, up_p, low_p):
        self.up_p = up_p  # Point object from dcel data structure
        self.low_p = low_p  # Point object from dcel data structure

        self.last_event = None
        self.last_intersection = None
        self.last_product = None

        self.cross = cross_product((self.up_p.co[x], self.up_p.co[y], 1), (self.low_p.co[x], self.low_p.co[y], 1))
        self.is_horizontal = almost_equal(self.up_p.co[y], self.low_p.co[y], self.accuracy)
        self.direction = (self.low_p - self.up_p).normalize()  # set downward direction of edge, Point object

    def __lt__(self, other):
        # when edge are inserting to the three
        if isinstance(other, self.__class__):
            # if two edges intersect in one point less edge will be with bigger angle with X coordinate
            if almost_equal(self.intersection, other.intersection, self.accuracy):
                # "Edges intersects in the same point"
                if almost_equal(self.product, other.product, self.accuracy):
                    # two edges are overlapping each other, there is no need of storing them together in tree
                    # longest edge should take place in tree with information of both overlapping edges
                    # input can have equal edges, such cases should be handled externally
                    return False
                else:
                    return self.product < other.product
            else:
                return self.intersection < other.intersection
        # this part is for searching edges by value of x coordinate of event point
        else:
            if almost_equal(self.intersection, other, self.accuracy):
                return False
            else:
                return self.intersection < other

    def __gt__(self, other):
        # when edge are inserting to the three
        if isinstance(other, self.__class__):
            # if two edges intersect in one point bigger edge will be with less angle with X coordinate
            if almost_equal(self.intersection, other.intersection, self.accuracy):
                # "Edges intersects in the same point"
                if almost_equal(self.product, other.product, self.accuracy):
                    # two edges are overlapping each other, there is no need of storing them together in tree
                    # longest edge should take place in tree with information of both overlapping edges
                    # input can have equal edges, such cases should be handled externally
                    return False
                else:
                    return self.product > other.product
            else:
                return self.intersection > other.intersection
        # this part is for searching edges by value of x coordinate of event point
        else:
            if almost_equal(self.intersection, other, self.accuracy):
                return False
            else:
                return self.intersection > other

    @property
    def intersection(self):
        # find intersection current edge with sweeping line
        if self.is_horizontal:
            return self.event_point.co[x]
        if not self.last_event or self.event_point != self.last_event:
            self.update_params()
        return self.last_intersection

    @property
    def product(self):
        # if edges has same point of intersection with sweep line they are sorting by angle to sweep line
        if self.is_horizontal:
            # if inserting edge is horizontal it always bigger for storing it to the end of sweep line
            return 1
        if not self.last_event or self.event_point != self.last_event:
            self.update_params()
        return self.last_product

    def update_params(self):
        # when new event point some parameters should be recalculated
        self.last_intersection = (self.event_point.co[y] * self.cross[y] + self.cross[z]) / -self.cross[x]
        self.last_product = dot_product(self.direction.co[:2], (1, 0))
        self.last_event = self.event_point

    @property
    def event_point(self):
        # get actual event point
        if self.global_event_point is not None:
            return self.global_event_point
        else:
            raise Exception('Sweep line should be initialized before')


class SortHalfEdgesCCW:
    """
    Half edges are sorting in counterclockwise direction from -X direction.
    Should be used with HalfEdge class from dcel_mesh module
    """

    def __lt__(self, other):
        # if self < other other it means that direction if closer to (-1, 0) direction
        if isinstance(other, self.__class__):
            if almost_equal(self.slop, other.slop, self.accuracy):
                return False
            else:
                return self.slop < other.slop
        else:
            raise TypeError('unorderable types: {} < {}'.format(type(self), type(other)))

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            if almost_equal(self.slop, other.slop, self.accuracy):
                return False
            else:
                return self.slop > other.slop
        else:
            raise TypeError('unorderable types: {} > {}'.format(type(self), type(other)))
