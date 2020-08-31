# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from math import degrees
from numpy import float64 as np_float64, linspace as np_linspace
from sverchok.utils.curve import SvLine
class SvgGroup():
    def __repr__(self):
        return "<SVG Group of {} {}>".format(len(self.shapes), self.shapes[0].__repr__())
    def __init__(self, shapes, name=None, location=None):
        self.shapes = shapes
        self.name = name
        self.location=location


    def draw(self, document):
        scale = document.scale
        svg = '<g '
        if self.name:
            svg += f'id="{self.name}" '
        if self.location:
            svg +=  f'transform="translate({self.location[0]*scale},{-self.location[1]*scale})"'
        svg += '>\n'

        for shape in self.shapes:
            svg += shape.draw(document)
            svg += '\n'

        svg += '</g>'

        return svg

def draw_path_linear_mode(verts, height, scale, start):
    svg = ''
    if start:
        x = verts[0][0] * scale
        y = height - verts[0][1] * scale
        svg += f'd="M {x} {y}'

    for v in verts[1:]:
        x = scale * v[0]
        y = height - scale * v[1]
        svg += f' L {x} {y}'
    return svg

def end_path(attributes, document):
    svg = ''
    if attributes:
        svg += attributes.draw(document)
    else:
        svg += 'fill="none" '
        svg += 'stroke-width="1px"'
        svg += ' stroke="rgb(0,0,0)"'
    svg += '/>'
    return svg

def generic_path(self, height, scale, document, start=False):
    t_min, t_max = self.curve.get_u_bounds()
    ts = np_linspace(t_min, t_max, num=self.node.curve_samples, dtype=np_float64)
    verts = self.curve.evaluate_array(ts).tolist()
    svg = draw_path_linear_mode(verts, height, scale, start)
    return svg

class SvgCurve():
    def __repr__(self):
        return "<SVG Curve>"

    def __init__(self, curve, attributes, node):
        self.curve = curve
        self.attributes = attributes
        self.node = node

    def draw(self, document):
        height = document.height
        scale = document.scale
        if isinstance(self.curve, SvLine):
            svg = '<path\n'
            u_min, u_max = self.curve.get_u_bounds()
            p1 = self.curve.evaluate(u_min)
            p2 = self.curve.evaluate(u_max)

            x = p1[0] * scale
            y = height - p1[1] * scale
            svg += f'd="M {x} {y}'

            x = scale * p2[0]
            y = height - scale * p2[1]
            svg += f' L {x} {y}" '
            svg += end_path(self.attributes, document)

        elif hasattr(self.curve, 'to_bezier_segments'):
            svg = ''
            last_point = []
            for segment in self.curve.to_bezier_segments():
                if segment.get_degree() not in {2, 3}: print("SVG supports only curves of 2nd and 3rd degree Linear Interpretation used")
                bezier_points = segment.get_control_points()
                if last_point != bezier_points[0].tolist():
                    if last_point:
                        svg += '" '
                        svg += end_path(self.attributes, document)

                    svg += '<path\n'
                    x = bezier_points[0][0] * scale
                    y = height - bezier_points[0][1] * scale
                    svg += f'd="M {x} {y}'
                if len(bezier_points) == 3:
                    cx = bezier_points[1][0] * scale
                    cy = height - bezier_points[1][1] * scale
                    x = bezier_points[2][0] * scale
                    y = height - bezier_points[2][1] * scale

                    svg += f' Q {cx} {cy} {x} {y}'
                    # svg += end_path(self.attributes, document)
                    last_point = bezier_points[2].tolist()

                if len(bezier_points) == 4:
                    cx = bezier_points[1][0] * scale
                    cy = height - bezier_points[1][1] * scale
                    cx2 = bezier_points[2][0] * scale
                    cy2 = height - bezier_points[2][1] * scale
                    x = bezier_points[3][0] * scale
                    y = height - bezier_points[3][1] * scale

                    svg += f' C {cx} {cy} {cx2} {cy2} {x} {y}'

                    last_point = bezier_points[3].tolist()

                else:
                    generic_path(self, height, scale, document)

            if self.node.cyclic:
                svg += ' Z'
            svg += '" '
            svg += end_path(self.attributes, document)
        else:
            svg = '<path\n'
            svg += generic_path(self, height, scale, document, start=True)
            if self.node.cyclic:
                svg += ' Z'
            svg += '" '
            svg += end_path(self.attributes, document)

        return svg
