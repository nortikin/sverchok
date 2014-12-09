import math
from sverchok.utils.csg_geom import *


class CSG(object):
    """
    ## License
    Copyright (c) 2011 Evan Wallace (http://madebyevan.com/), under the MIT license.
    Python port Copyright (c) 2012 Tim Knip (http://www.floorplanner.com), under the MIT license.
    """
    def __init__(self):
        self.polygons = []

    @classmethod
    def fromPolygons(cls, polygons):
        csg = CSG()
        csg.polygons = polygons
        return csg

    def clone(self):
        csg = CSG()
        csg.polygons = map(lambda p: p.clone(), self.polygons)
        return csg

    def toPolygons(self):
        return self.polygons

    def union(self, csg):
        a = Node(self.clone().polygons)
        b = Node(csg.clone().polygons)
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        a.build(b.allPolygons())
        return CSG.fromPolygons(a.allPolygons())

    def subtract(self, csg):
        a = Node(self.clone().polygons)
        b = Node(csg.clone().polygons)
        a.invert()
        a.clipTo(b)
        b.clipTo(a)
        b.invert()
        b.clipTo(a)
        b.invert()
        a.build(b.allPolygons())
        a.invert()
        return CSG.fromPolygons(a.allPolygons())

    def intersect(self, csg):
        a = Node(self.clone().polygons)
        b = Node(csg.clone().polygons)
        a.invert()
        b.clipTo(a)
        b.invert()
        a.clipTo(b)
        b.clipTo(a)
        a.build(b.allPolygons())
        a.invert()
        return CSG.fromPolygons(a.allPolygons())

    def inverse(self):
        """
        Return a new CSG solid with solid and empty space switched. This solid is
        not modified.
        """
        csg = self.clone()
        map(lambda p: p.flip(), csg.polygons)
        return csg

    # @classmethod
    # def cube(cls, center=[0, 0, 0], radius=[1, 1, 1]):
    #     """
    #     Construct an axis-aligned solid cuboid. Optional parameters.
    #     """
    #     c = Vector(0, 0, 0)
    #     r = [1, 1, 1]
    #     if isinstance(center, list):
    #         c = Vector(center)
    #     if isinstance(radius, list):
    #         r = radius
    #     else:
    #         r = [radius, radius, radius]

    #     cube_indices = [
    #         [[0, 4, 6, 2], [-1, 0, 0]],
    #         [[1, 3, 7, 5], [+1, 0, 0]],
    #         [[0, 1, 5, 4], [0, -1, 0]],
    #         [[2, 6, 7, 3], [0, +1, 0]],
    #         [[0, 2, 3, 1], [0, 0, -1]],
    #         [[4, 5, 7, 6], [0, 0, +1]]
    #     ]

    #     polygons = list(map(
    #         lambda v: Polygon(
    #             map(lambda i:
    #                 Vertex(
    #                     Vector(
    #                         c.x + r[0] * (2 * bool(i & 1) - 1),
    #                         c.y + r[1] * (2 * bool(i & 2) - 1),
    #                         c.z + r[2] * (2 * bool(i & 4) - 1)
    #                     ), None), v[0])), cube_indices))

    #     return CSG.fromPolygons(polygons)

    # @classmethod
    # def sphere(cls, **kwargs):
    #     """ Returns a sphere.

    #         Kwargs:
    #             center (list): Center of sphere, default [0, 0, 0].
    #             radius (float): Radius of sphere, default 1.0.
    #             slices (int): Number of slices, default 16.
    #             stacks (int): Number of stacks, default 8.
    #     """
    #     center = kwargs.get('center', [0.0, 0.0, 0.0])
    #     if isinstance(center, float):
    #         center = [center, center, center]
    #     c = Vector(center)
    #     r = kwargs.get('radius', 1.0)
    #     if isinstance(r, list) and len(r) > 2:
    #         r = r[0]
    #     slices = kwargs.get('slices', 16)
    #     stacks = kwargs.get('stacks', 8)
    #     polygons = []
    #     sl = float(slices)
    #     st = float(stacks)

    #     def vertex(vertices, theta, phi):
    #         theta *= math.pi * 2.0
    #         phi *= math.pi
    #         d = Vector(
    #             math.cos(theta) * math.sin(phi),
    #             math.cos(phi),
    #             math.sin(theta) * math.sin(phi))
    #         vertices.append(Vertex(c.plus(d.times(r)), d))

    #     for i in range(0, slices):
    #         for j in range(0, stacks):
    #             vertices = []
    #             vertex(vertices, i / sl, j / st)
    #             if j > 0:
    #                 vertex(vertices, (i + 1) / sl, j / st)
    #             if j < stacks - 1:
    #                 vertex(vertices, (i + 1) / sl, (j + 1) / st)
    #             vertex(vertices, i / sl, (j + 1) / st)
    #             polygons.append(Polygon(vertices))

    #     return CSG.fromPolygons(polygons)

    # @classmethod
    # def cylinder(cls, **kwargs):
    #     """ Returns a cylinder.

    #         Kwargs:
    #             start (list): Start of cylinder, default [0, -1, 0].
    #             end (list): End of cylinder, default [0, 1, 0].
    #             radius (float): Radius of cylinder, default 1.0.
    #             slices (int): Number of slices, default 16.
    #     """
    #     s = kwargs.get('start', Vector(0.0, -1.0, 0.0))
    #     e = kwargs.get('end', Vector(0.0, 1.0, 0.0))
    #     if isinstance(s, list):
    #         s = Vector(*s)
    #     if isinstance(e, list):
    #         e = Vector(*e)
    #     r = kwargs.get('radius', 1.0)
    #     slices = kwargs.get('slices', 16)
    #     ray = e.minus(s)

    #     axisZ = ray.unit()
    #     isY = (math.fabs(axisZ.y) > 0.5)
    #     axisX = Vector(float(isY), float(not isY), 0).cross(axisZ).unit()
    #     axisY = axisX.cross(axisZ).unit()
    #     start = Vertex(s, axisZ.negated())
    #     end = Vertex(e, axisZ.unit())
    #     polygons = []

    #     def point(stack, slice, normalBlend):
    #         angle = slice * math.pi * 2.0
    #         out = axisX.times(math.cos(angle)).plus(
    #             axisY.times(math.sin(angle)))
    #         pos = s.plus(ray.times(stack)).plus(out.times(r))
    #         normal = out.times(1.0 - math.fabs(normalBlend)).plus(
    #             axisZ.times(normalBlend))
    #         return Vertex(pos, normal)

    #     for i in range(0, slices):
    #         t0 = i / float(slices)
    #         t1 = (i + 1) / float(slices)
    #         polygons.append(Polygon([start, point(0., t0, -1.), point(0., t1, -1.)]))
    #         polygons.append(Polygon([point(0., t1, 0.), point(0., t0, 0.),
    #                                  point(1., t0, 0.), point(1., t1, 0.)]))
    #         polygons.append(Polygon([end, point(1., t1, 1.), point(1., t0, 1.)]))

    #     return CSG.fromPolygons(polygons)

    @classmethod
    def Obj_from_pydata(cls, verts, faces):
        """

        """
        polygons = []
        for face in faces:
            polyg = []
            for idx in face:
                co = verts[idx]
                polyg.append(Vertex(Vector(*co)))
            polygons.append(Polygon(polyg))

        return CSG.fromPolygons(polygons)
