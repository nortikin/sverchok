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

import operator

import bpy
from mathutils import Matrix, Vector

from bpy.props import IntProperty, FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (Vector_generate, updateNode,
                                     match_long_repeat)
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff, diameter


class SvFractalCurveNode(bpy.types.Node, SverchCustomTreeNode):
    '''Fractal curve'''
    bl_idname = 'SvFractalCurveNode'
    bl_label = 'Fractal Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'

    iterations = IntProperty(name = 'Iterations',
            description = 'Number of iterations',
            default = 3, min = 0, update = updateNode)

    min_length = FloatProperty(name = 'Min. length',
            description = 'Minimum edge length',
            default = 0.01, min = 0, update = updateNode)

    precision = IntProperty(
        name="Precision", min=0, max=10, default=8, update=updateNode,
        description="decimal precision of coordinates for calculations")

    def move_to(self, curve, src, dst):
        vector = dst - src
        return [vertex + vector for vertex in curve]

    def scale_to(self, curve, src, dst):
        coef = dst / src
        return [vertex * coef for vertex in curve]

    def rotate_to(self, curve, src, dst):
        matrix = autorotate_diff(dst, src)
        return [matrix * vertex for vertex in curve]

    def substitute(self, recipient, donor):
        line = donor[-1] - donor[0]
        result = []
        result.append(donor[0])
        for pair in zip(recipient, recipient[1:]):
            new_line = pair[1] - pair[0]
            if new_line.length < self.min_length:
                result.append(pair[1])
                continue
            scaled = self.scale_to(donor, line.length, new_line.length)
            rotated = self.rotate_to(scaled, line, new_line)
            item = self.move_to(rotated, rotated[0], pair[0])
            result.extend(item[1:])
        if self.precision > 0:
            result = [Vector(round(x, self.precision) for x in v) for v in result]
            print(result)
        return result

    def make_fractal(self, vertices):
        result = vertices
        for i in range(self.iterations):
            result = self.substitute(result, vertices)
        result = self.move_to(result, result[0], vertices[0])
        return result

    def draw_buttons(self, context, layout):
        layout.prop(self, "iterations")
        layout.prop(self, "min_length")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "precision")

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')

        self.outputs.new('VerticesSocket', 'Vertices')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        curves = Vector_generate(self.inputs['Vertices'].sv_get())

        verts_out = []

        for curve in curves:
            curve_out = self.make_fractal(curve)
            verts_out.append([tuple(v) for v in curve_out])

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvFractalCurveNode)


def unregister():
    bpy.utils.unregister_class(SvFractalCurveNode)

