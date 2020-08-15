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

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr
from sverchok.utils.svg import SvgGroup

class SvgCircle():
    def __repr__(self):
        return "<SVG Circle>"

    def __init__(self, rad_x, rad_y, location, attributes):
        self.rad_x = rad_x
        self.rad_y = rad_y
        self.location = location
        self.attributes = attributes

    def draw(self, height, scale):
        svg = '<ellipse '
        svg += f'cx="{self.location[0] * scale}" '
        svg += f'cy="{height-self.location[1]* scale}" '
        svg += f'rx="{self.rad_x * scale}" '
        svg += f'ry="{self.rad_y * scale}" '

        if self.attributes:
            svg += self.attributes.draw(height, scale)
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

    rad_x: FloatProperty(name='Radius X', description='Radius', default=1.0, update=updateNode)
    rad_y: FloatProperty(name='Radius Y', description='Radius', default=1.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Center")
        self.inputs.new('SvStringsSocket', "Radius X").prop_name = 'rad_x'
        self.inputs.new('SvStringsSocket', "Radius Y").prop_name = 'rad_y'
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def process(self):

        if not self.outputs[0].is_linked:
            return
        params_in = [s.sv_get(deepcopy=False) for s in self.inputs[:3]]
        shapes_out = []
        params_in.append(self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=None))
        for params in zip(*mlr(params_in)):
            shapes=[]
            for loc, rad_x, rad_y, atts in zip(*mlr(params)):
                print(atts)
                shapes.append(SvgCircle(rad_x, rad_y, loc, atts))
            shapes_out.append(SvgGroup(shapes))
        self.outputs[0].sv_set(shapes_out)



def register():
    bpy.utils.register_class(SvSvgCircleNode)


def unregister():
    bpy.utils.unregister_class(SvSvgCircleNode)
