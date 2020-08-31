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
from bpy.props import FloatProperty, StringProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr
from sverchok.utils.svg import SvgGroup
from sverchok.utils.curve import SvCircle

class SvgPattern():
    def __repr__(self):
        return f"<SVG Pattern {self.name}>"

    def __init__(self, name, width, height, objects, offset, angle):

        self.name = name.replace(" ", "_")
        self.width = width
        self.height = height
        self.objects = objects
        self.offset = offset
        self.angle = angle


    def draw(self, document):
        scale = document.scale
        pattern = lambda: None
        pattern.height = self.height * scale
        pattern.scale = document.scale
        pattern.defs = document.defs
        svg = '<pattern patternUnits="userSpaceOnUse" '
        svg += f'patternTransform="translate({self.offset[0]*scale},{self.offset[1]*scale}) rotate({self.angle})" '
        svg += f'id="{self.name}" '
        svg += f'width="{self.width*scale}" '
        svg += f'height="{self.height*scale}"> '


        svg += self.objects.draw(pattern)

        svg += '</pattern>'

        return svg

class SvSvgPatternNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Pattern SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvSvgPatternNode'
    bl_label = 'Pattern SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_PATTERN_SVG'

    pattern_width: FloatProperty(name='Width', description='Pattern Tile Width', default=1.0, update=updateNode)
    pattern_height: FloatProperty(name='Height', description=' PatternTile Height', default=1.0, update=updateNode)
    pattern_name: StringProperty(name='Name', description='Pattern base name', default="pattern 1", update=updateNode)
    pattern_offset: FloatVectorProperty(name='Offset', description='Pattern Offset', default=(0, 0, 0), update=updateNode)
    pattern_angle: FloatProperty(name='Angle', description='Pattern rotation angle', default=0.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvSvgSocket', "SVG Objects")
        self.inputs.new('SvStringsSocket', "Width").prop_name = "pattern_width"
        self.inputs.new('SvStringsSocket', "Height").prop_name = "pattern_height"
        self.inputs.new('SvVerticesSocket', "Offset").prop_name = "pattern_offset"
        self.inputs.new('SvStringsSocket', "Angle").prop_name = "pattern_angle"
        self.outputs.new('SvSvgSocket', "SVG Pattern")


    def draw_buttons(self, context, layout):
        layout.prop(self, 'pattern_name')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return

        objs_in = self.inputs['SVG Objects'].sv_get(deepcopy=False, default=None)
        width_in = self.inputs['Width'].sv_get(deepcopy=False)[0]
        height_in = self.inputs['Height'].sv_get(deepcopy=False)[0]
        offset_in = self.inputs['Offset'].sv_get(deepcopy=False)[0]
        angle_in = self.inputs['Angle'].sv_get(deepcopy=False)[0]
        patterns = []
        idx = 0

        name = f'p_{hash(self)}' if not self.pattern_name else self.pattern_name

        for objs, width, height, offset, angle in zip(*mlr([objs_in, width_in, height_in, offset_in, angle_in])):
            pattern = SvgPattern(f'{name}_{idx}', width, height, objs, offset, angle)
            idx += 1
            patterns.append(pattern)
        self.outputs[0].sv_set([patterns])


def register():
    bpy.utils.register_class(SvSvgPatternNode)


def unregister():
    bpy.utils.unregister_class(SvSvgPatternNode)
