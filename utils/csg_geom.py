import math


class Vector(object):

    """
    class Vector

    Represents a 3D vector.

    Example usage:
         Vector(1, 2, 3);
         Vector([1, 2, 3]);
         Vector({ 'x': 1, 'y': 2, 'z': 3 });
    """

    def __init__(self, *args):
        if len(args) == 3:
            self.x = args[0]
            self.y = args[1]
            self.z = args[2]
        elif len(args) == 1 and isinstance(args[0], Vector):
            self.x = args[0][0]
            self.y = args[0][1]
            self.z = args[0][2]
        elif len(args) == 1 and isinstance(args[0], list):
            self.x = args[0][0]
            self.y = args[0][1]
            self.z = args[0][2]
        elif len(args) == 1 and args[0] and 'x' in args[0]:
            self.x = args[0]['x']
            self.y = args[0]['y']
            self.z = args[0]['z']
        else:
            self.x = 0.0
            self.y = 0.0
            self.z = 0.0

    def clone(self):
        return Vector(self.x, self.y, self.z)

    def negated(self):
        return Vector(-self.x, -self.y, -self.z)

    def plus(self, a):
        return Vector(self.x + a.x, self.y + a.y, self.z + a.z)

    def minus(self, a):
        return Vector(self.x - a.x, self.y - a.y, self.z - a.z)

    def times(self, a):
        return Vector(self.x * a, self.y * a, self.z * a)

    def dividedBy(self, a):
        return Vector(self.x / a, self.y / a, self.z / a)

    def dot(self, a):
        return self.x * a.x + self.y * a.y + self.z * a.z

    def lerp(self, a, t):
        return self.plus(a.minus(self).times(t))

    def length(self):
        return math.sqrt(self.dot(self))

    def unit(self):
        """ Normalize. """
        return self.dividedBy(self.length())

    def cross(self, a):
        return Vector(
            self.y * a.z - self.z * a.y,
            self.z * a.x - self.x * a.z,
            self.x * a.y - self.y * a.x)

    def __getitem__(self, key):
        return (self.x, self.y, self.z)[key]

    def __setitem__(self, key, value):
        l = [self.x, self.y, self.z]
        l[key] = value
        self.x, self.y, self.z = l

    def __len__(self):
        return 3

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __repr__(self):
        return 'Vector(%.2f, %.2f, %0.2f)' % (self.x, self.y, self.z)


class Vertex(object):

    """
    Class Vertex

    Represents a vertex of a polygon. Use your own vertex class instead of this
    one to provide additional features like texture coordinates and vertex
    colors. Custom vertex classes need to provide a `pos` property and `clone()`,
    `flip()`, and `interpolate()` methods that behave analogous to the ones
    defined by `Vertex`. This class provides `normal` so convenience
    functions like `CSG.sphere()` can return a smooth vertex normal, but `normal`
    is not used anywhere else.
    """

    def __init__(self, pos, normal=None):
        self.pos = Vector(pos)
        self.normal = Vector(normal)

    def clone(self):
        return Vertex(self.pos.clone(), self.normal.clone())

    def flip(self):
        """
        Invert all orientation-specific data (e.g. vertex normal). Called when the
        orientation of a polygon is flipped.
        """
        self.normal = self.normal.negated()

    def interpolate(self, other, t):
        """
        Create a new vertex between this vertex and `other` by linearly
        interpolating all properties using a parameter of `t`. Subclasses should
        override this to interpolate additional properties.
        """
        return Vertex(self.pos.lerp(other.pos, t), self.normal.lerp(other.normal, t))


class Plane(object):

    """
    class Plane

    Represents a plane in 3D space.
    """

    """
    `Plane.EPSILON` is the tolerance used by `splitPolygon()` to decide if a
    point is on the plane.
    """
    EPSILON = 1e-5

    def __init__(self, normal, w):
        self.normal = normal
        self.w = w

    @classmethod
    def fromPoints(cls, a, b, c):
        n = b.minus(a).cross(c.minus(a)).unit()
        return Plane(n, n.dot(a))

    def clone(self):
        return Plane(self.normal.clone(), self.w)

    def flip(self):
        self.normal = self.normal.negated()
        self.w = -self.w

    def splitPolygon(self, polygon, coplanarFront, coplanarBack, front, back):
        """
        Split `polygon` by this plane if needed, then put the polygon or polygon
        fragments in the appropriate lists. Coplanar polygons go into either
        `coplanarFront` or `coplanarBack` depending on their orientation with
        respect to this plane. Polygons in front or in back of this plane go into
        either `front` or `back`
        """
        COPLANAR = 0
        FRONT = 1
        BACK = 2
        SPANNING = 3

        # Classify each point as well as the entire polygon into one of the above
        # four classes.
        polygonType = 0
        types = []

        for i in range(0, len(polygon.vertices)):
            t = self.normal.dot(polygon.vertices[i].pos) - self.w
            type = -1
            if t < -Plane.EPSILON:
                type = BACK
            elif t > Plane.EPSILON:
                type = FRONT
            else:
                type = COPLANAR
            polygonType |= type
            types.append(type)

        # Put the polygon in the correct list, splitting it when necessary.
        if polygonType == COPLANAR:
            if self.normal.dot(polygon.plane.normal) > 0:
                coplanarFront.append(polygon)
            else:
                coplanarBack.append(polygon)
        elif polygonType == FRONT:
            front.append(polygon)
        elif polygonType == BACK:
            back.append(polygon)
        elif polygonType == SPANNING:
            f = []
            b = []
            for i in range(0, len(polygon.vertices)):
                j = (i + 1) % len(polygon.vertices)
                ti = types[i]
                tj = types[j]
                vi = polygon.vertices[i]
                vj = polygon.vertices[j]
                if ti != BACK:
                    f.append(vi)
                if ti != FRONT:
                    if ti != BACK:
                        b.append(vi.clone())
                    else:
                        b.append(vi)
                if (ti | tj) == SPANNING:
                    t = (self.w - self.normal.dot(vi.pos)) / self.normal.dot(vj.pos.minus(vi.pos))
                    v = vi.interpolate(vj, t)
                    f.append(v)
                    b.append(v.clone())
            if len(f) >= 3:
                front.append(Polygon(f, polygon.shared))
            if len(b) >= 3:
                back.append(Polygon(b, polygon.shared))


class Polygon(object):

    """
    class Polygon

    Represents a convex polygon. The vertices used to initialize a polygon must
    be coplanar and form a convex loop. They do not have to be `Vertex`
    instances but they must behave similarly (duck typing can be used for
    customization).

    Each convex polygon has a `shared` property, which is shared between all
    polygons that are clones of each other or were split from the same polygon.
    This can be used to define per-polygon properties (such as surface color).
    """

    def __init__(self, vertices, shared=None):
        self.vertices = list(vertices)
        self.shared = shared
        self.plane = Plane.fromPoints(
            self.vertices[0].pos, 
            self.vertices[1].pos, 
            self.vertices[2].pos)

    def clone(self):
        vertices = map(lambda v: v.clone(), self.vertices)
        return Polygon(vertices, self.shared)

    def flip(self):
        self.vertices.reverse()
        map(lambda v: v.flip(), self.vertices)
        self.plane.flip()


class Node(object):

    """
    class Node

    Holds a node in a BSP tree. A BSP tree is built from a collection of polygons
    by picking a polygon to split along. That polygon (and all other coplanar
    polygons) are added directly to that node and the other polygons are added to
    the front and/or back subtrees. This is not a leafy BSP tree since there is
    no distinction between internal and leaf nodes.
    """

    def __init__(self, polygons=None):
        self.plane = None
        self.front = None
        self.back = None
        self.polygons = []
        if polygons:
            self.build(polygons)

    def clone(self):
        node = Node()
        if self.plane:
            node.plane = self.plane.clone()
        if self.front:
            node.front = self.front.clone()
        if self.back:
            node.back = self.back.clone()
        node.polygons = map(lambda p: p.clone(), self.polygons)
        return node

    def invert(self):
        """
        Convert solid space to empty space and empty space to solid space.
        """
        for poly in self.polygons:
            poly.flip()
        self.plane.flip()
        if self.front:
            self.front.invert()
        if self.back:
            self.back.invert()
        temp = self.front
        self.front = self.back
        self.back = temp

    def clipPolygons(self, polygons):
        """
        Recursively remove all polygons in `polygons` that are inside this BSP
        tree.
        """
        if not self.plane:
            return polygons[:]
        front = []
        back = []
        for poly in polygons:
            self.plane.splitPolygon(poly, front, back, front, back)
        if self.front:
            front = self.front.clipPolygons(front)
        if self.back:
            back = self.back.clipPolygons(back)
        else:
            back = []
        front.extend(back)
        return front

    def clipTo(self, bsp):
        """
        Remove all polygons in this BSP tree that are inside the other BSP tree
        `bsp`.
        """
        self.polygons = bsp.clipPolygons(self.polygons)
        if self.front:
            self.front.clipTo(bsp)
        if self.back:
            self.back.clipTo(bsp)

    def allPolygons(self):
        """
        Return a list of all polygons in this BSP tree.
        """
        polygons = self.polygons[:]
        if self.front:
            polygons.extend(self.front.allPolygons())
        if self.back:
            polygons.extend(self.back.allPolygons())
        return polygons

    def build(self, polygons):
        if isinstance(polygons, map):
            # if not len(list(polygons)):
            #     return
            polygons = list(polygons)
            if not len(polygons):
                return

        if not self.plane:
            self.plane = polygons[0].plane.clone()
        front = []
        back = []
        for poly in polygons:
            self.plane.splitPolygon(
                poly, self.polygons, self.polygons, front, back)
        if len(front):
            if not self.front:
                self.front = Node()
            self.front.build(front)
        if len(back):
            if not self.back:
                self.back = Node()
            self.back.build(back)
