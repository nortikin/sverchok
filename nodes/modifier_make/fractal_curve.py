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
    """
    Triggers: Fractal Curve
    Tooltip: Generate fractal (self-repeating) curve
    """
    bl_idname = 'SvFractalCurveNode'
    bl_label = 'Fractal Curve'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FRACTAL_CURVE'

    iterations : IntProperty(name = 'Iterations',
            description = 'Number of iterations',
            default = 3, min = 0, update = updateNode)

    min_length : FloatProperty(name = 'Min. length',
            description = 'Minimum edge length',
            default = 0.01, min = 0, update = updateNode)

    precision : IntProperty(
        name="Precision", min=0, max=10, default=7, update=updateNode,
        description="decimal precision of coordinates for calculations")

    def move_to(self, curve, src, dst):
        vector = dst - src
        return [vertex + vector for vertex in curve]

    def scale_to(self, curve, src, dst):
        coef = dst / src
        return [vertex * coef for vertex in curve]

    def check_plane(self, curve):
        # Try to detect if the whole figure belongs to
        # one of coordinate axes
        epsilon = 10 ** (- self.precision)
        if all([abs(v.z) < epsilon for v in curve]):
            return 'XY'
        elif all([abs(v.x) < epsilon for v in curve]):
            return 'YZ'
        elif all([abs(v.y) < epsilon for v in curve]):
            return 'XZ'
        else:
            return None

    def calc_rotation(self, curve, src, dst, plane=None):
        # Some hacks.
        # Problem: if src and/or dst are exactly parallel to
        # one of coordinate axes, then Vector.rotation_difference
        # sometimes returns a matrix that rotates our vector in
        # completely different plane.
        # For example, if whole figure lays in XY plane, and
        # we are trying to rotate src = (0, 1, 0) into dst = (1, 0, 0),
        # then rotation_difference might return us a matrix, which
        # rotates (-1, 0, 0) into (0, 0, -1), which is out of XY plane
        # ("because why no? it still rotates src into dst").
        # Solution (hack): if whole figure lays in XY plane, then do
        # not use general rotation_difference method, calculate
        # rotation along Z axis only.
        if plane == 'XY':
            # Another unobvious hack: Vector.angle_signed method
            # works with 2D vectors only. Fortunately, in this particular
            # case our vectors are actually 2D.
            dst = Vector((dst[0], dst[1]))
            src = Vector((src[0], src[1]))
            angle = dst.angle_signed(src)
            return Matrix.Rotation(angle, 4, 'Z')
        elif plane == 'YZ':
            dst = Vector((dst[1], dst[2]))
            src = Vector((src[1], src[2]))
            angle = dst.angle_signed(src)
            return Matrix.Rotation(angle, 4, 'X')
        elif plane == 'XZ':
            dst = Vector((dst[2], dst[0]))
            src = Vector((src[2], src[0]))
            angle = dst.angle_signed(src)
            return Matrix.Rotation(angle, 4, 'Y')
        else:
            return autorotate_diff(dst, src)

    def rotate_to(self, curve, src, dst, plane=None):
        matrix = self.calc_rotation(curve, src, dst, plane)
        return [matrix @ vertex for vertex in curve]

    def substitute(self, recipient, donor, min_length, plane=None):
        line = donor[-1] - donor[0]
        result = []
        result.append(donor[0])
        for pair in zip(recipient, recipient[1:]):
            new_line = pair[1] - pair[0]
            if new_line.length < min_length:
                result.append(pair[1])
                continue
            scaled = self.scale_to(donor, line.length, new_line.length)
            rotated = self.rotate_to(scaled, line, new_line, plane)
            item = self.move_to(rotated, rotated[0], pair[0])
            result.extend(item[1:])
        if self.precision > 0:
            result = [Vector(v.to_tuple(self.precision)) for v in result]
        return result

    def make_fractal(self, vertices, iterations, min_length):
        result = vertices
        plane = self.check_plane(vertices)
        print(plane)
        for i in range(iterations):
            result = self.substitute(result, vertices, min_length, plane)
        result = self.move_to(result, result[0], vertices[0])
        return result

    def draw_buttons(self, context, layout):
        if 'Iterations' not in self.inputs:
            layout.prop(self, "iterations")
            layout.prop(self, "min_length")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "precision")

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = "iterations"
        self.inputs.new('SvStringsSocket', 'MinLength').prop_name = "min_length"
        self.inputs.new('SvVerticesSocket', 'Vertices')

        self.outputs.new('SvVerticesSocket', 'Vertices')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        curves = Vector_generate(self.inputs['Vertices'].sv_get())
        if 'Iterations' in self.inputs:
            iterations_s = self.inputs['Iterations'].sv_get()[0]
            min_length_s = self.inputs['MinLength'].sv_get()[0]
        else:
            iterations_s = [[self.iterations]]
            min_length_s = [[self.min_length]]

        verts_out = []

        objects = match_long_repeat([curves, iterations_s, min_length_s])

        for curve, iterations, min_length in zip(*objects):
            if isinstance(iterations, (list, tuple)):
                iterations = iterations[0]
            if isinstance(min_length, (list, tuple)):
                min_length = min_length[0]
            curve_out = self.make_fractal(curve, iterations, min_length)
            verts_out.append([tuple(v) for v in curve_out])

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvFractalCurveNode)


def unregister():
    bpy.utils.unregister_class(SvFractalCurveNode)

