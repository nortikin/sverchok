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
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr

class SvgPolygons():
    def __repr__(self):
        return "<SVG Path>"
    def __init__(self, verts, polygons, attributes):
        self.verts = verts
        self.polygons = polygons
        self.attributes = attributes


    def draw(self, height, scale):
        verts = self.verts
        svg = '<g>\n'
        for p, atts in zip(*mlr([self.polygons, self.attributes])):
            svg += '<polygon '
            svg += 'points="'
            for c in p:
                svg += ' {} {}'.format(verts[c][0]* scale, height-verts[c][1]* scale)


            svg += ' "\n'


            if atts:

                svg += atts.draw(height, scale)
            svg += '/>'
        svg += '</g>'
        return svg

class SvSvgPolygonsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SVG Path
    Tooltip: Generate SVG Path
    """
    bl_idname = 'SvSvgPolygonsNode'
    bl_label = 'Polygons SVG'
    bl_icon = 'MESH_CIRCLE'


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvVerticesSocket', "Polygons")
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def process(self):

        if not self.outputs[0].is_linked:
            return
        verts_in = self.inputs['Vertices'].sv_get(deepcopy=True)
        pols_in = self.inputs['Polygons'].sv_get(deepcopy=True)
        shapes = []
        atts_in = self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=None)
        for verts, pols, atts in zip(*mlr([verts_in, pols_in, atts_in])):
            shapes.append(SvgPolygons(verts, pols, atts))
        self.outputs[0].sv_set(shapes)



def register():
    bpy.utils.register_class(SvSvgPolygonsNode)


def unregister():
    bpy.utils.unregister_class(SvSvgPolygonsNode)
