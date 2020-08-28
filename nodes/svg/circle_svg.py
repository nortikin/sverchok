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

from math import sin, cos, pi, degrees, radians
from mathutils import Matrix
import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr
from sverchok.utils.svg import SvgGroup
from sverchok.utils.curve import SvCircle

mat_t = Matrix().Identity(4)  # pre-allocate once for performance (translation)
mat_s = Matrix().Identity(4)  # pre-allocate once for performance (scale)

def curve_matrix(loc, angle, rad_x, rad_y):
    # translation
    mat_t[0][3] = loc[0]
    mat_t[1][3] = loc[1]
    mat_t[2][3] = loc[2]
    # rotation
    mat_r = Matrix.Rotation(radians(angle), 4, 'Z')
    # scale
    mat_s[0][0] = 1
    mat_s[1][1] = rad_y/rad_x
    mat_s[2][2] = 0
    # composite matrix
    return mat_t @ mat_r @ mat_s

class SvgCircle():
    def __repr__(self):
        return "<SVG Circle>"

    def __init__(self, rad_x, rad_y, location, angle, attributes):
        self.rad_x = rad_x
        self.rad_y = rad_y
        self.location = location
        self.angle = angle
        self.attributes = attributes

    def draw(self, document):
        height = document.height
        scale = document.scale
        svg = '<ellipse\n'
        x = self.location[0] * scale
        y = height-self.location[1]* scale
        if self.angle != 0:
            svg += f'    transform="translate({x},{y})rotate({self.angle})"\n'
        else:
            svg += f'    cx="{x}"\n'
            svg += f'    cy="{y}"\n'
        svg += f'    rx="{self.rad_x * scale}"\n'
        svg += f'    ry="{self.rad_y * scale}"\n'

        if self.attributes:
            svg += self.attributes.draw(document)
        svg += '/>'
        return svg

class SvSvgCircleNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvSvgCircleNode'
    bl_label = 'Circle SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_CIRCLE_SVG'

    rad_x: FloatProperty(name='Radius X', description='Horizontal Radius', default=1.0, update=updateNode)
    rad_y: FloatProperty(name='Radius Y', description='Vertical Radius', default=1.0, update=updateNode)
    angle: FloatProperty(name='Angle', description='Shape Rotation Angle', default=0.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Center")
        self.inputs.new('SvStringsSocket', "Radius X").prop_name = 'rad_x'
        self.inputs.new('SvStringsSocket', "Radius Y").prop_name = 'rad_y'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")
        self.outputs.new('SvCurveSocket', "Curves")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        params_in = [s.sv_get(deepcopy=False) for s in self.inputs[:4]]
        params_in.append(self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=None))
        get_curves = self.outputs['Curves'].is_linked
        shapes_out = []
        curves_out = []
        for params in zip(*mlr(params_in)):
            shapes = []
            for loc, rad_x, rad_y, angle, atts in zip(*mlr(params)):
                shapes.append(SvgCircle(rad_x, rad_y, loc, angle, atts))

                if get_curves:
                    center = curve_matrix(loc, angle, rad_x, rad_y)
                    curve = SvCircle(center, rad_x)
                    curve.u_bounds = (0, 2*pi)
                    curves_out.append(curve)
            shapes_out.append(SvgGroup(shapes))
        self.outputs[0].sv_set(shapes_out)
        self.outputs[1].sv_set(curves_out)



def register():
    bpy.utils.register_class(SvSvgCircleNode)


def unregister():
    bpy.utils.unregister_class(SvSvgCircleNode)
