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
from bpy.props import EnumProperty, BoolProperty, StringProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4
from sverchok.utils.svg import SvgGroup

class SvgText():
    def __repr__(self):
        return "<SVG Text>"
    def __init__(self, location, text, size, angle, attributes, font_family):
        self.location = location
        self.text = text
        self.size = size
        self.angle = angle
        self.attributes = attributes
        self.font_family = font_family

    def draw(self, height, scale):
        svg = '<text '

        svg += f'font-size="{self.size * scale}px" '
        svg += f'font-family="{self.font_family}" '
        x = self.location[0] * scale
        y = height - self.location[1] * scale
        if self.angle != 0:
            svg += f'transform="translate({x},{y})rotate({self.angle})" '
        else:
            svg += f'x="{x}" '
            svg += f'y="{y}" '
        if self.attributes:
            svg += self.attributes.draw(height, scale)
        svg += '>'
        svg += self.text
        svg += '</text>'
        return svg

class SvSvgTextNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Circle '''
    bl_idname = 'SvSvgTextNode'
    bl_label = 'Text SVG'
    bl_icon = 'MESH_CIRCLE'

    font_size: FloatProperty(
        name='Size',
        description='Font Size',
        default=10,
        update=updateNode)

    font_family: EnumProperty(
        name='Font',
        description='Font Size',
        items=enum_item_4(["serif", 'sans-serif', 'monospace', 'cursive', 'fantasy', 'user']),
        default='monospace',
        update=updateNode)

    user_font: StringProperty(
        name='Font Name',
        description='Define font name',
        default='',
        update=updateNode)

    angle: FloatProperty(
        name='Angle',
        description='Text Rotation',
        default=0,
        update=updateNode)

    text: StringProperty(
        name='Text',
        description='Text',
        default='',
        update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvStringsSocket', "Text").prop_name = 'text'
        self.inputs.new('SvStringsSocket', "Font Size").prop_name = 'font_size'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'angle'

        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, "font_family", expand=False)
        if self.font_family == 'user':
            layout.prop(self, "user_font")

    def process(self):

        if not self.outputs[0].is_linked:
            return
        params_in = [s.sv_get(deepcopy=False) for s in self.inputs[:4]]
        texts_out = []
        params_in.append(self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=None))
        font_family = self.user_font if self.font_family == 'user' else self.font_family

        for params in zip(*mlr(params_in)):
            svg_texts = []
            for loc, text, size, angle, atts in zip(*mlr(params)):
                svg_texts.append(SvgText(loc, text, size, angle, atts, font_family))

            texts_out.append(SvgGroup(svg_texts))

        self.outputs[0].sv_set(texts_out)



def register():
    bpy.utils.register_class(SvSvgTextNode)


def unregister():
    bpy.utils.unregister_class(SvSvgTextNode)
