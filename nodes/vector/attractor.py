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

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
import math

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, fullList
from sverchok.utils.math import inverse, inverse_square, inverse_cubic, inverse_exp, gauss

def get_avg_vector(vectors):
    result = Vector((0,0,0))
    for vector in vectors:
        result += vector
    return result / len(vectors)

class SvAttractorNode(bpy.types.Node, SverchCustomTreeNode):
    '''Attraction vectors calculator'''
    bl_idname = 'SvAttractorNode'
    bl_label = 'Vector Attraction'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VECTOR_ATTRACTION'

    types = [
            ("Point", "Point", "Attraction to single or multiple points", 0),
            ("Line", "Line", "Attraction to straight line", 1),
            ("Plane", "Plane", "Attraction to plane", 2)
        ]

    falloff_types = [
            ("inverse", "Inverse - 1/R", "", 0),
            ("inverse_square", "Inverse square - 1/R^2", "Similar to gravitation or electromagnetizm", 1),
            ("inverse_cubic", "Inverse cubic - 1/R^3", "", 2),
            ("inverse_exp", "Inverse exponent - Exp(-R)", "", 3),
            ("gauss", "Gauss - Exp(-R^2/2)", "", 4)
        ]

    @throttled
    def update_type(self, context):
        self.inputs['Direction'].hide_safe = (self.attractor_type == 'Point')
        self.inputs['Coefficient'].hide_safe = (self.falloff_type not in ['inverse_exp', 'gauss'])

    attractor_type: EnumProperty(
        name="Attractor type", items=types, default='Point', update=update_type)

    falloff_type: EnumProperty(
        name="Falloff type", items=falloff_types, default='inverse_square', update=update_type)

    clamp: BoolProperty(
        name="Clamp", description="Restrict coefficient with R", default=True, update=updateNode)

    amplitude: FloatProperty(
        name="Amplitude", default=0.5, min=0.0, update=updateNode)

    coefficient: FloatProperty(
        name="Coefficient", default=0.5, update=updateNode)

    point_modes = [
        ('AVG', "Average", "Use average distance to all attraction centers", 0),
        ('MIN', "Nearest", "Use minimum distance to any of attraction centers", 1)
    ]

    point_mode : EnumProperty(
        name = "Points mode",
        description = "How to define the distance when multiple attraction centers are used",
        items = point_modes,
        default = 'AVG',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        c = self.inputs.new('SvVerticesSocket', "Center")
        c.use_prop = True
        c.default_property = (0.0, 0.0, 0.0)

        d = self.inputs.new('SvVerticesSocket', "Direction")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', 'Amplitude').prop_name = 'amplitude'
        self.inputs.new('SvStringsSocket', 'Coefficient').prop_name = 'coefficient'

        self.outputs.new('SvVerticesSocket', "Vectors")
        self.outputs.new('SvVerticesSocket', "Directions")
        self.outputs.new('SvStringsSocket', "Coeffs")

        self.update_type(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'attractor_type')
        if self.attractor_type == 'Point':
            layout.prop(self, 'point_mode')
        layout.prop(self, 'falloff_type')
        layout.prop(self, 'clamp')

    def _falloff(self, coefficient, rho):
        func = globals()[self.falloff_type]
        return func(coefficient, rho)

    def falloff(self, amplitude, coefficient, rho):
        if rho == 0:
            return amplitude
        result = amplitude * self._falloff(coefficient, rho)
        if result <= 0:
            return 0.0
        if self.clamp:
            if result >= rho:
                return rho
        return result

    def to_point(self, amplitude, coefficient, vertex, centers, direction):
        vertex = Vector(vertex)
        n = len(centers)
        if self.point_mode == 'AVG' or n <= 1:
            vectors = []
            for center in centers:
                vector = Vector(center) - vertex
                vector = self.falloff(amplitude, coefficient, vector.length) * vector.normalized()
                vectors.append(vector)
            result = get_avg_vector(vectors)
            return result.length, result.normalized()
        else:
            kdt = KDTree(n)
            for i, center in enumerate(centers):
                kdt.insert(Vector(center), i)
            kdt.balance()
            nearest_co, nearest_idx, nearest_distance = kdt.find(vertex)
            vector = nearest_co - vertex
            coeff = self.falloff(amplitude, coefficient, nearest_distance)
            return coeff, vector.normalized()

    def to_line(self, amplitude, coefficient, vertex, centers, direction):
        center = Vector(centers[0])
        direction = Vector(direction)
        dirlength = direction.length
        if dirlength <= 0:
            raise ValueError("Direction vector must have nonzero length!")
        vertex = Vector(vertex)

        to_center = center - vertex
        # cosine of angle between to_center and direction
        cos_phi = to_center.dot(direction) / (to_center.length * dirlength)
        # projection of to_center on direction
        to_center_projection = to_center.length * cos_phi * direction.normalized()
        # projection of vertex on direction
        projection = center - to_center_projection
        vector = projection - vertex
        return self.falloff(amplitude, coefficient, vector.length), vector.normalized()

    def to_plane(self, amplitude, coefficient, vertex, centers, direction):
        center = Vector(centers[0])
        direction = Vector(direction)
        vertex = Vector(vertex)
        dirlength = direction.length
        if dirlength <= 0:
            raise ValueError("Direction vector must have nonzero length!")

        d = - direction.dot(center)
        # distance from vertex to plane
        rho = abs(vertex.dot(direction) + d) / dirlength

        from_center = center - vertex

        # vector is either direction or negative direction
        if from_center.dot(direction) >= 0:
            vector = direction.normalized()
        else:
            # for some reason mathutil's Vector does not have .negated()
            # thankfully we do not need direction itself anymore.
            direction.negate()
            vector = direction.normalized()

        return self.falloff(amplitude, coefficient, rho), vector


    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        centers = self.inputs['Center'].sv_get(default=[[]])[0]
        directions_s = self.inputs['Direction'].sv_get(default=[[(0,0,1)]])
        amplitudes_s = self.inputs['Amplitude'].sv_get(default=[0.5])
        coefficients_s = self.inputs['Coefficient'].sv_get(default=[0.5])

        out_vectors = []
        out_units = []
        out_lens = []

        meshes = match_long_repeat([vertices_s, directions_s, amplitudes_s, coefficients_s])
        for vertices, directions, amplitudes, coefficients in zip(*meshes):
            if isinstance(directions, (tuple, list)) and len(directions) == 3 and all([isinstance(x, (int, float)) for x in directions]):
                direction = directions
            else:
                direction = directions[0]

            if isinstance(amplitudes, (int, float)):
                amplitudes = [amplitudes]
            if isinstance(coefficients, (int, float)):
                coefficients = [coefficients]

            fullList(amplitudes, len(vertices))
            fullList(coefficients, len(vertices))

            vectors = []
            units = []
            lens = []
            for vertex, amplitude, coefficient in zip(vertices, amplitudes, coefficients):
                if self.attractor_type == 'Point':
                    length, unit = self.to_point(amplitude, coefficient, vertex, centers, direction)
                elif self.attractor_type == 'Line':
                    length, unit = self.to_line(amplitude, coefficient, vertex, centers, direction)
                elif self.attractor_type == 'Plane':
                    length, unit = self.to_plane(amplitude, coefficient, vertex, centers, direction)
                else:
                    raise ValueError("Unknown attractor type: " + self.attractor_type)
                vector = length * unit
                units.append(tuple(unit))
                lens.append(length)
                vectors.append(tuple(vector))
            out_vectors.append(vectors)
            out_units.append(units)
            out_lens.append(lens)

        self.outputs['Vectors'].sv_set(out_vectors)
        self.outputs['Directions'].sv_set(out_units)
        self.outputs['Coeffs'].sv_set(out_lens)

def register():
    bpy.utils.register_class(SvAttractorNode)


def unregister():
    bpy.utils.unregister_class(SvAttractorNode)
