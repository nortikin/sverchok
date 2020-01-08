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

from math import sqrt, atan2
from collections import defaultdict

import bpy
import bmesh
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty
from mathutils import Vector
from mathutils.geometry import intersect_line_line_2d

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.voronoi import Site, computeVoronoiDiagram, computeDelaunayTriangulation, BIG_FLOAT
from sverchok.utils.geom import center, LineEquation2D, CircleEquation2D
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata
from sverchok.utils.logging import debug, info

class Bounds(object):
    def __init__(self):
        self.x_max = 0
        self.y_max = 0
        self.x_min = 0
        self.y_min = 0
        self.r_max = 0
        self.center = (0,0)

    @classmethod
    def new(cls, mode):
        if mode == 'BOX':
            return BoxBounds()
        elif mode == 'CIRCLE':
            return CircleBounds()
        else:
            raise Exception("Unknown bounds type")

    def __repr__(self):
        return f"Bounds[C: {self.center}, R: {self.r_max}, X: {self.x_min} - {self.x_max}, Y: {self.y_min} - {self.y_max}]"

class Mesh2D(object):
    def __init__(self):
        self.verts = []
        self.all_edges = set()
        self.linked_verts = defaultdict(set)
        self._next_vert = 0

    @classmethod
    def from_pydata(cls, verts, edges):
        mesh = Mesh2D()
        for vert in verts:
            mesh.new_vert(vert)
        for i, j in edges:
            mesh.new_edge(i, j)
        return mesh

    def new_vert(self, vert):
        if vert is None:
            raise Exception("new_vert(None)")
        if vert[0] is None or vert[1] is None:
            raise Exception(f"new_vert({vert})")
        self.verts.append(vert)
        idx = self._next_vert
        self._next_vert += 1
        return idx

    def new_edge(self, i, j):
        v1, v2 = self.verts[i], self.verts[j]
        #info("Add: %s (%s) => %s (%s)", i, v1, j, v2)
        self.all_edges.add((v1, v2))
        self.linked_verts[i].add(j)
        self.linked_verts[j].add(i)

    def remove_edge(self, i, j):
        if (self.verts[i], self.verts[j]) in self.all_edges:
            self.all_edges.remove((self.verts[i], self.verts[j]))
        if (self.verts[j], self.verts[i]) in self.all_edges:
            self.all_edges.remove((self.verts[j], self.verts[i]))
        if j in self.linked_verts[i]:
            self.linked_verts[i].remove(j)
        if i in self.linked_verts[j]:
            self.linked_verts[j].remove(i)

    def to_pydata(self):
        verts = [vert for vert in self.verts if vert is not None]
        lut = dict((vert, idx) for idx, vert in enumerate(verts))
        #info(lut)
        edges = []
        for v1, v2 in self.all_edges:
            i1 = lut.get(v1, None)
            i2 = lut.get(v2, None)
            #info("Get: %s (%s) => %s (%s)", v1, i1, v2, i2)
            if i1 is not None and i2 is not None:
                edges.append((i1, i2))

        return verts, edges

class BoxBounds(Bounds):

    def contains(self, p):
        x, y = tuple(p)
        return (self.x_min <= x <= self.x_max) and (self.y_min <= y <= self.y_max)
    
    @property
    def edges(self):
        v1 = (self.x_min, self.y_min)
        v2 = (self.x_min, self.y_max)
        v3 = (self.x_max, self.y_max)
        v4 = (self.x_max, self.y_min)

        e1 = (v1, v2)
        e2 = (v2, v3)
        e3 = (v3, v4)
        e4 = (v4, v1)

        return [e1, e2, e3, e4]

    def segment_intersection(self, p1, p2):
        if not isinstance(p1, Vector):
            p1 = Vector(p1)
        if not isinstance(p2, Vector):
            p2 = Vector(p2)

        min_r = BIG_FLOAT
        nearest = None

        for v_i, v_j in self.edges:
            intersection = intersect_line_line_2d(p1, p2, v_i, v_j)
            if intersection is not None:
                r = (p1 - intersection).length
                if r < min_r:
                    nearest = intersection
                    min_r = r

        return nearest

    def ray_intersection(self, p, line):
        p = Vector(center(line.sites))

        min_r = BIG_FLOAT
        nearest = None

        for v_i, v_j in self.edges:
            bound = LineEquation2D.from_two_points(v_i, v_j)
            intersection = bound.intersect_with_line(line)
            if intersection is not None:
                r = (p - intersection).length
                #info("INT: [%s - %s] X [%s] => %s (%s)", v_i, v_j, line, intersection, r)
                if r < min_r:
                    nearest = intersection
                    min_r = r

        return nearest

    def line_intersection(self, line):
        result = []
        eps = 1e-8
        for v_i, v_j in self.edges:
            bound = LineEquation2D.from_two_points(v_i, v_j)
            intersection = bound.intersect_with_line(line)
            if intersection is not None:
                x,y = tuple(intersection)
                if (self.x_min-eps <= x <= self.x_max+eps) and (self.y_min-eps <= y <= self.y_max+eps):
                    result.append(intersection)
        return result

class CircleBounds(Bounds):

    @property
    def circle(self):
        return CircleEquation2D(self.center, self.r_max)

    def contains(self, p):
        return self.circle.contains(p)

    def segment_intersection(self, p1, p2):
        r = self.circle.intersect_with_segment(p1, p2)
        if r is None:
            return None
        if r[0] is None and r[1] is None:
            return None
        if r[0] is not None:
            return r[0]
        if r[1] is not None:
            return r[1]

    def ray_intersection(self, p, line):
        p = Vector(center(line.sites))
        intersection = self.circle.intersect_with_line(line)
        #info("RI: {line} X {self.circle} => {intersection}")
        if intersection is None:
            return None
        else:
            v1, v2 = intersection
            r1 = (p - v1).length
            r2 = (p - v2).length
            if r1 < r2:
                return v1
            else:
                return v2

    def line_intersection(self, line):
        intersection = self.circle.intersect_with_line(line)
        return intersection

class Voronoi2DNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi vr
    Tooltip: Generate 2D Voronoi diagram for a set of vertices.
    """
    bl_idname = 'Voronoi2DNode'
    bl_label = 'Voronoi 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    clip: FloatProperty(
        name='clip', description='Clipping Distance',
        default=1.0, min=0, update=updateNode)

    bound_modes = [
            ('BOX', 'Bounding Box', "Bounding Box", 0),
            ('CIRCLE', 'Circle', "Circle", 1)
        ]

    bound_mode: EnumProperty(
        name = 'Bounds Mode',
        description = "Bounding mode",
        items = bound_modes,
        default = 'BOX',
        update = updateNode)

    draw_bounds: BoolProperty(
        name = "Draw Bounds",
        description = "Draw bounding edges",
        default = True,
        update = updateNode)

    draw_hangs: BoolProperty(
        name = "Draw Tails",
        description = "Draw lines that end outside of clipping area",
        default = True,
        update = updateNode)

    @throttled
    def update_sockets(self, context):
        if 'Faces' in self.outputs:
            self.outputs['Faces'].hide_safe = not self.make_faces
        if 'MaxSides' in self.inputs:
            self.inputs['MaxSides'].hide_safe = not self.make_faces

    make_faces: BoolProperty(
        name = "Make faces",
        description = "Use `fill holes` function to make Voronoi polygons",
        default = False,
        update = update_sockets)

    max_sides: IntProperty(
        name='Sides',
        description='Maximum number of polygon sides',
        default=10,
        min=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'MaxSides').prop_name = 'max_sides'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "bound_mode")
        layout.prop(self, "draw_bounds")
        if not self.draw_bounds:
            layout.prop(self, "draw_hangs")
        layout.prop(self, "clip", text="Clipping")
        layout.prop(self, "make_faces")

    def process(self):

        if not self.inputs['Vertices'].is_linked:
            return

        if not self.outputs['Vertices'].is_linked:
            return

        points_in = self.inputs['Vertices'].sv_get()
        max_sides_in = self.inputs['MaxSides'].sv_get()

        pts_out = []
        edges_out = []
        faces_out = []
        for sites, max_sides in zip_long_repeat(points_in, max_sides_in):
            if isinstance(max_sides, (list, tuple)):
                max_sides = max_sides[0]

            bounds = Bounds.new(self.bound_mode)
            source_sites = []
            bounds.x_max = -BIG_FLOAT
            bounds.x_min = BIG_FLOAT
            bounds.y_min = BIG_FLOAT
            bounds.y_max = -BIG_FLOAT
            x0, y0, z0 = center(sites)
            bounds.center = (x0, y0)
            # creates points in format for voronoi library, throwing away z
            for x, y, z in sites:
                r = sqrt((x-x0)**2 + (y-y0)**2)
                bounds.r_max = max(r, bounds.r_max)
                bounds.x_max = max(x, bounds.x_max)
                bounds.x_min = min(x, bounds.x_min)
                bounds.y_max = max(y, bounds.y_max)
                bounds.y_min = min(y, bounds.y_min)
                source_sites.append(Site(x, y))

            delta = self.clip
            bounds.x_max = bounds.x_max + delta
            bounds.y_max = bounds.y_max + delta

            bounds.x_min = bounds.x_min - delta
            bounds.y_min = bounds.y_min - delta

            bounds.r_max = bounds.r_max + delta

            voronoi_data = computeVoronoiDiagram(source_sites)
            verts = voronoi_data.vertices
            lines = voronoi_data.lines
            all_edges = voronoi_data.edges

            finite_edges = [(edge[1], edge[2]) for edge in all_edges if -1 not in edge]
            bm = Mesh2D.from_pydata(verts, finite_edges)

            # clipping box to bounding box.
            verts_to_remove = set()
            edges_to_remove = set()
            bounding_verts = []

            # For each diagram vertex that is outside of the bounds,
            # cut each edge connected with that vertex by bounding line.
            # Remove such vertices, remove such edges, and instead add
            # vertices lying on the bounding line and corresponding edges.
            for vert_idx, vert in enumerate(bm.verts[:]):
                x, y = tuple(vert)
                if not bounds.contains((x,y)):
                    verts_to_remove.add(vert_idx)
                    for other_vert_idx in list(bm.linked_verts[vert_idx]):
                        edges_to_remove.add((vert_idx, other_vert_idx))
                        if self.draw_hangs or self.draw_bounds:
                            other_vert = bm.verts[other_vert_idx]
                            if other_vert is not None:
                                x2, y2 = tuple(other_vert)
                                intersection = bounds.segment_intersection((x,y), (x2,y2))
                                if intersection is not None:
                                    intersection = tuple(intersection)
                                    new_vert_idx = bm.new_vert(intersection)
                                    bounding_verts.append(new_vert_idx)
                                    #info("CLIP: Added point: %s => %s", (x_i, y_i), new_vert_idx)
                                    bm.new_edge(other_vert_idx, new_vert_idx)

            # Diagram lines that go infinitely from one side of diagram to another
            infinite_lines = []
            # Lines that start at the one vertex of the diagram and go to infinity
            rays = defaultdict(list)
            if self.draw_hangs or self.draw_bounds:
                sites_by_line = defaultdict(list)

                for site_idx in voronoi_data.polygons.keys():
                    for line_index, i1, i2 in voronoi_data.polygons[site_idx]:
                        if i1 == -1 or i2 == -1:
                            site = source_sites[site_idx]
                            sites_by_line[line_index].append((site.x, site.y))

                for line_index, i1, i2 in all_edges:
                    if i1 == -1 or i2 == -1:
                        line = lines[line_index]
                        a, b, c = line
                        eqn = LineEquation2D(a, b, -c)
                        if i1 == -1 and i2 != -1:
                            eqn.sites = sites_by_line[line_index]
                            rays[i2].append(eqn)
                        elif i2 == -1 and i1 != -1:
                            eqn.sites = sites_by_line[line_index]
                            rays[i1].append(eqn)
                        elif i1 == -1 and i2 == -1:
                            infinite_lines.append(eqn)

                # For each (half-infinite) ray, calculate it's intersection
                # with the bounding line and draw an edge from ray's beginning to
                # the bounding line.
                # NB: The data returned from voronoi.py for such lines
                # is a vertex and a line equation. The line obviously intersects
                # the bounding line in two points; which one should we choose?
                # Let's choose that one which is closer to site points which the
                # line is dividing.
                for vert_index in rays.keys():
                    x,y = bm.verts[vert_index]
                    vert = Vector((x,y))
                    if vert_index not in verts_to_remove:
                        for line in rays[vert_index]:
                            intersection = bounds.ray_intersection(vert, line)
                            intersection = tuple(intersection)
                            new_vert_idx = bm.new_vert(intersection)
                            bounding_verts.append(new_vert_idx)
                            #info("INF: Added point: %s: %s => %s", (x,y), (x_i, y_i), new_vert_idx)
                            bm.new_edge(vert_index, new_vert_idx)

                # For each infinite (in two directions) line,
                # calculate two it's intersections with the bounding
                # line and connect them by an edge.
                for eqn in infinite_lines:
                    intersections = bounds.line_intersection(eqn)
                    if len(intersections) == 2:
                        v1, v2 = intersections
                        new_vert_1_idx = bm.new_vert(tuple(v1))
                        new_vert_2_idx = bm.new_vert(tuple(v2))
                        bounding_verts.append(new_vert_1_idx)
                        bounding_verts.append(new_vert_2_idx)
                        bm.new_edge(new_vert_1_idx, new_vert_2_idx)
                    else:
                        self.error("unexpected number of intersections of infinite line %s with area bounds: %s", eqn, intersections)

                # TODO: there could be (finite) edges, which have both ends
                # outside of the bounding line. We could detect such edges and
                # process similarly to infinite lines - calculate two intersections
                # with the bounding line and connect them by an edge.
                # Currently I consider such cases as rare, so this is a low priority issue.
                # Btw, such edges do not fall under definition of either "bounding edge"
                # or "hanging edge"; so should we add a separate checkbox for such edges?...

            if self.draw_bounds and bounding_verts:
                bounding_verts.sort(key = lambda idx: atan2(bm.verts[idx][1], bm.verts[idx][0]))
                for i, j in zip(bounding_verts, bounding_verts[1:]):
                    bm.new_edge(i, j)
                bm.new_edge(bounding_verts[-1], bounding_verts[0])

            for i, j in edges_to_remove:
                bm.remove_edge(i, j)
            for vert_idx in verts_to_remove:
                bm.verts[vert_idx] = None

            verts, edges = bm.to_pydata()

            new_vertices = [(vert[0], vert[1], 0) for vert in verts]

            if self.make_faces:
                bm = bmesh_from_pydata(new_vertices, edges, [])
                bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=max_sides)
                new_vertices, edges, new_faces = pydata_from_bmesh(bm)
                bm.free()
                faces_out.append(new_faces)

            pts_out.append(new_vertices)
            edges_out.append(edges)
            #edges_out.append(finite_edges)

        # outputs
        self.outputs['Vertices'].sv_set(pts_out)
        self.outputs['Edges'].sv_set(edges_out)
        if 'Faces' in self.outputs and self.make_faces:
            self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(Voronoi2DNode)

def unregister():
    bpy.utils.unregister_class(Voronoi2DNode)

