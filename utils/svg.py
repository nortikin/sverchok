# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
from math import degrees
class SvgGroup():
    def __repr__(self):
        return "<SVG Group of {} {}>".format(len(self.shapes), self.shapes[0].__repr__())
    def __init__(self, shapes, name=None):
        self.shapes = shapes
        self.name = name


    def draw(self, document):
        scale = document.scale
        if self.name:
            svg = f'<g id="{self.name}">\n'
        else:
            svg = '<g>\n'
        for shape in self.shapes:
            svg += shape.draw(document)
            svg += '\n'

        svg += '</g>'

        return svg
