# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from mathutils.geometry import interpolate_bezier as bezlerp
from mathutils import Vector
import numpy as np

def get_offset(vec1, vec2, width):
    p1 = Vector(vec1[:2])
    p2 = Vector(vec2[:2])
    vp = (p2 - p1).normalized().orthogonal()
    return (width / 2 * vp)

def get_all_offsets(controls, points, samples, thickness):
    offsets = []
    offsets.append(get_offset(controls[0], controls[1], thickness))
    for r1, r2 in [[i, i+2] for i in range(samples-2)]:
        offsets.append(get_offset(points[r1], points[r2], thickness))
    offsets.append(get_offset(controls[2], controls[3], thickness))
    return offsets

class ShaderLib2D():
    def __init__(self):
        """
        docstring ?
        """
        self.can_use_cache = False
        self.vectors = []
        self.vertex_colors = []
        self.indices = []
        self.addv = self.vectors.extend
        self.addc = self.vertex_colors.extend
        self.addi = self.indices.extend

    def use_cached_canvas(self, geom):
        self.add_data(geom.vectors, geom.vertex_colors, geom.indices)
        self.can_use_cache = True

    def add_data(self, new_vectors=None, new_colors=None, new_indices=None):
        """
        input
            see `add_rect` for a reference implementation

            new_vectors:    a list of 2d vectors as lists
            new_colors:     a list of colors of the same length as new_vectors
            new_indices:    a list of indices to make up tri-face topology
                            this function automatically offsets the new_indices, so you only have to write
                            topology for one instance of your object
        """
        offset = len(self.vectors)
        self.addv(new_vectors)
        self.addc(new_colors)
        self.addi([[offset + i for i in tri] for tri in new_indices])

    def add_rect(self, x, y, w, h, color, color2=False):
        """
        b - c
        | / |
        a - d
        """
        if self.can_use_cache: return

        a = (x, y)
        b = (x, y - h)
        c = (x + w, y - h)
        d = (x + w, y)

        colors = [color for _ in range(4)]
        if color2:
            colors = [color, color2, color2, color]

        self.add_data(
            new_vectors=[a, b, c, d], 
            new_colors=colors,
            new_indices=[[0, 1, 2], [0, 2, 3]]
        )

    def add_rect_outline(self, x, y, w, h, thickness, direction, color):
        """
        direction: outside, inside, both
        """
        if self.can_use_cache: return

        TH = thickness / 2.0
        T = thickness


        if direction == "inside":
            a = (x, y)
            b = (x, y - h)
            c = (x + w, y - h)
            d = (x + w, y)
            e = a[0]+T, a[1]-T
            f = b[0]+T, b[1]+T
            g = c[0]-T, c[1]+T
            h = d[0]-T, d[1]-T
        elif direction == "outside":
            e = (x, y)
            f = (x, y - h)
            g = (x + w, y - h)
            h = (x + w, y)
            a = e[0]-T, e[1]+T
            b = f[0]-T, f[1]-T
            c = g[0]+T, g[1]-T
            d = h[0]+T, h[1]+T
        else:
            a = x-TH, y+TH
            b = x-TH, y-h-TH
            c = x+w+TH, y-h-TH
            d = x+w+TH, y+TH
            e = x+TH, y-TH
            f = x+TH, y-h+TH
            g = x+w-TH, y-h+TH
            h = x+w-TH, y-TH

        A, B, C, D, E, F, G, H = 0, 1, 2, 3, 4, 5, 6, 7
        self.add_data(
            new_vectors=[a, b, c, d, e, f, g, h], 
            new_colors=[color for _ in range(8)],
            new_indices=[
                [A, E, F], [A, F, B], [B, F, G], [B, G, C], 
                [C, G, H], [C, H, D], [D, H, E], [D, E, A]]
        )


    def add_rect_rounded(self, x, y, w, h, color, r=0, precision=5):
        xa = x - r       ;   ya = y + h
        xb = x           ;   yb = y + h - r
        xc = x + w - r   ;   yc = y
        xd = x + w       ;   yd = y - r

        # https://user-images.githubusercontent.com/619340/120084214-b8bb2300-c0ce-11eb-8d83-d86078f42d55.png
        # the core, when all dimensions are supported by input
        points = [
            (xb, yd), (xb, yc), (xa, yc), (xa, yb), (xb, yb), (xb, ya),
            (xc, ya), (xc, yb), (xd, yb), (xd, yc), (xc, yc), (xc, yd)
        ]
        indices = [
            [0, 10, 11], [0, 1, 10], [1, 7, 10], [1, 4, 7], [4, 6, 7],
            [4, 5, 6], [2, 3, 4], [2, 4, 1], [10, 7, 8], [10, 8, 9]
        ]

        self.add_data(
            new_vectors=points, new_indices=indices,
            new_colors=[color for _ in range(len(points))]
        )

        N = precision
        half_pi = np.pi / 2.0
        theta = np.linspace(0, half_pi, N, endpoint=True)

        #            SW        NW        NE        SE 
        quarters = [[xb, yc], [xb, yb], [xc, yb], [xc, yc]]
        offsets = [np.pi, half_pi, 0, -half_pi]

        for quarter, offset in zip(quarters, offsets):
            arc_coords = np.array([np.sin(theta-offset), np.cos(theta-offset)])
            coords = arc_coords.T * r
            coords += np.array([quarter])
            coords = np.vstack([coords, quarter])
            points = coords.tolist()
            last_idx = len(points) - 1
            indices = [[i, i+1, last_idx] for i in range(len(points)-1)]
            self.add_data(
                new_vectors=points, new_indices=indices,
                new_colors=[color for _ in range(len(points))]
            )


    def add_line(self, x1, y1, x2, y2, width, color):

        p1 = Vector((x1, y1))
        p2 = Vector((x2, y2))
        v = (p2 - p1).normalized()
        vp = v.orthogonal()
        offset = (width / 2 * vp)
        a = p1 + offset
        b = p1 - offset
        c = p2 - offset
        d = p2 + offset

        self.add_data(
            new_vectors=[a, b, c, d], 
            new_colors=[color for _ in range(4)],
            new_indices=[[0, 1, 2], [0, 2, 3]]
        )

    def add_polyline(self, path, width, color, closed=False):
        ...

    def add_bezier(self, controls, width, color, samples=20, resampled=False):
        # knot1, ctrl_1, ctrl_2, knot2 = controls 

        N = samples
        bezier_points = bezlerp(*controls, samples)
        offsets = get_all_offsets(controls, bezier_points, samples, width)
        verts = [(b.to_2d() + offset)[:] for b, offset in zip(bezier_points, offsets)]
        verts.extend([(b.to_2d() - offset)[:] for b, offset in zip(bezier_points, offsets)])

        indices = []
        add_indices = indices.extend
        _ = [add_indices([[i, i+1, N+i], [i+N, i+N+1, i+1]]) for i in range(N-1)]
        self.add_data(
            new_vectors=verts, 
            new_colors=[color for _ in range(len(verts))],
            new_indices=indices
        )        


    def add_circle(self, x, y, radius, color, precision=32):
        N = precision
        theta = np.linspace(0, np.pi * 2, N, endpoint=False)
        circle_coords = np.array([np.sin(theta), np.cos(theta)])
        coords = circle_coords.T * radius
        coords += np.array([[x, y]])
        coords = np.vstack([coords, [x, y]])
        verts = coords.tolist()
        last_idx = len(verts) - 1
        indices = [[i, i+1, last_idx] for i in range(N)] + [[N-1, 0, last_idx]]
        self.add_data(
            new_vectors=verts, 
            new_colors=[color for _ in range(len(verts))],
            new_indices=indices
        )

    def add_arc(self, x, y, start_angle, end_angle, radius, width, color, precision=32):
        # angle is in radians.
        # pecision can be an int or the word "adaptive"
        # should return the midpoint of the arc's area.
        N = precision
        theta = np.linspace(start_angle, end_angle, N, endpoint=True)
        arc_coords = np.array([np.sin(theta), np.cos(theta)])
        offset = (width / 2)
        outer_coords = arc_coords.T * (radius + offset)
        inner_coords = arc_coords.T * (radius - offset)
        coords = np.vstack([outer_coords, inner_coords])
        coords += np.array([[x, y]])
        verts = coords.tolist()
        indices = []
        add_indices = indices.extend
        _ = [add_indices([[i, i+1, N+i], [i+N, i+N+1, i+1]]) for i in range(N-1)]
        self.add_data(
            new_vectors=verts, 
            new_colors=[color for _ in range(len(verts))],
            new_indices=indices
        )


    def compile(self):
        geom = lambda: None
        geom.vectors = self.vectors
        geom.vertex_colors = self.vertex_colors
        geom.indices = self.indices
        return geom
