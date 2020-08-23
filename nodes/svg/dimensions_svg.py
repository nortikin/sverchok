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

from math import pi, degrees
from mathutils import Vector, Matrix
import bpy
from bpy.props import EnumProperty, StringProperty, FloatProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4, updateNode
from sverchok.utils.svg import SvgGroup


def draw_edge(p, scale, height):
    svg = '<line '
    svg += f'x1="{p[0][0]* scale}" y1="{height- p[0][1]* scale}" '
    svg += f'x2="{p[1][0]* scale}" y2="{height- p[1][1]* scale}" '
    return svg

class SvgDimension():
    def __repr__(self):
        return "<SVG Dimension>"

    def __init__(self, location, location_b, dim_type, dim_offset, font_size, text_offset, text_attrib, lines_attrib, font_family, node):
        self.node = node
        self.location = location
        self.location_b = location_b
        self.dim_type = dim_type
        self.dim_offset = dim_offset
        self.font_size = font_size
        self.text_offset = text_offset

        self.text_attributes = text_attrib
        self.line_attributes = lines_attrib
        self.font_family = font_family

    def draw(self, height, scale):
        loc_a = Vector(self.location)
        loc_b = Vector(self.location_b)

        if self.dim_type == "Horizontal" or self.dim_type == 0:
            line_dir = Vector((1, 0, 0))
            perp = Vector ((0, 1, 0))
            diagonal = (line_dir + perp).normalized()
            higher_a = loc_a[1] > loc_b[1]
            angle = 0
            if higher_a:
                dim_loc_a = loc_a + perp * (self.dim_offset)
                dim_loc_b = loc_b + perp * (self.dim_offset + loc_a[1] - loc_b[1])
                sign = 1 if self.dim_offset > 0 else -1
                sign_b = 1 if self.dim_offset + loc_a[1] - loc_b[1] > 0 else -1
            else:
                dim_loc_a = loc_a + perp * (self.dim_offset + loc_b[1] - loc_a[1])
                dim_loc_b = loc_b + perp * (self.dim_offset)
                sign = 1 if self.dim_offset+loc_b[1]-loc_a[1] > 0 else -1
                sign_b = 1 if self.dim_offset > 0 else -1

        if self.dim_type == "Vertical" or self.dim_type == 1:
            line_dir = Vector((0, -1, 0))
            perp = Vector ((1, 0, 0))
            diagonal = (line_dir + perp).normalized()
            higher_a = loc_a[0] > loc_b[0]
            angle = 90
            if higher_a:
                dim_loc_a = loc_a + perp * (self.dim_offset)
                dim_loc_b = loc_b + perp * (self.dim_offset + loc_a[0] - loc_b[0])
                sign = 1 if self.dim_offset > 0 else -1
                sign_b = 1 if self.dim_offset+loc_a[0] - loc_b[0] > 0 else -1
            else:
                line_dir = Vector((0, 1, 0))
                dim_loc_a = loc_a + perp * (self.dim_offset + loc_b[0] - loc_a[0])
                dim_loc_b = loc_b + perp * (self.dim_offset)
                sign = 1 if self.dim_offset + loc_b[0] - loc_a[0] > 0 else -1
                sign_b = 1 if self.dim_offset > 0 else -1

        if self.dim_type == "Aligned" or self.dim_type == 2:
            line_dir = (loc_b - loc_a).normalized()

            rot = Matrix.Rotation(pi/2, 4, 'Z')
            perp = (line_dir @ rot).normalized()
            diagonal = (line_dir + perp).normalized()
            dim_loc_a = loc_a + perp*(self.dim_offset)
            dim_loc_b = loc_b + perp*(self.dim_offset)
            angle = 180 + degrees(line_dir.angle(Vector((1, 0, 0))))
            sign = 1 if self.dim_offset > 0 else -1
            sign_b = sign

        line_extension = self.node.line_extension

        lines = []

        lines.append([loc_a, dim_loc_a + sign * perp * line_extension])
        lines.append([loc_b, dim_loc_b + sign_b * perp * line_extension])
        lines.append([dim_loc_a - line_dir * line_extension, dim_loc_b + line_dir * line_extension])
        lines.append([dim_loc_a - diagonal * line_extension, dim_loc_a + diagonal * line_extension])
        lines.append([dim_loc_b - diagonal * line_extension, dim_loc_b + diagonal * line_extension])
        lines_svg = ''

        for line in lines:
            lines_svg += draw_edge(line, scale, height)
            if self.line_attributes:
                lines_svg += self.line_attributes.draw(height, scale)
            else:
                lines_svg += 'stroke-width="1px" '
                lines_svg += 'stroke="rgb(0,0,0)"'
            lines_svg += '/>'

        text_svg = self.draw_dimension_text(dim_loc_a, dim_loc_b, height, scale, angle)
        return lines_svg + text_svg

    def draw_dimension_text(self, dim_loc_a, dim_loc_b, height, scale, angle):
        text_loc = (dim_loc_a + dim_loc_b)/2
        x = text_loc[0] * scale
        y = height - text_loc[1] * scale

        text_svg = '<text text-anchor="middle" '
        text_svg += f'font-size="{self.font_size * scale}px" '
        text_svg += f'font-family="{self.font_family}" '
        text_svg += f'transform="translate({x},{y})rotate({angle})translate({0},{self.text_offset * scale})" '

        if self.text_attributes:
            text_svg += self.text_attributes.draw(height, scale)
        text_svg += '>'
        precision = self.node.decimal_precision
        p_format = "{:10."+str(precision)+"f}"
        text_svg += p_format.format((dim_loc_b - dim_loc_a).length)
        text_svg += f' {self.node.units}'
        text_svg += '</text>'

        return text_svg


class SvSvgDimensionNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Text SVG
    Tooltip: Creates SVG Dimesions
    """
    bl_idname = 'SvSvgDimensionNode'
    bl_label = 'Dimension SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_DIMENSION_SVG'

    font_size: FloatProperty(
        name='Font Size',
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

    dimension_type: EnumProperty(
        name='Type',
        description='Dimension type. Horizontal = 0, Vertical = 1, Aligned = 2',
        items=enum_item_4(["Horizontal", 'Vertical', 'Aligned']),
        default='Aligned',
        update=updateNode)

    dimension_offset: FloatProperty(
        name='Dim. Offset',
        description='Dimension offset',
        default=0,
        update=updateNode)

    line_extension: FloatProperty(
        name='Lines Extension',
        description='Text Rotation',
        default=0,
        update=updateNode)
    decimal_precision: IntProperty(
        name='Decimals',
        description='Text Rotation',
        default=2,
        update=updateNode)

    units: StringProperty(
        name='Units',
        description='units',
        default='',
        update=updateNode)
    text: StringProperty(
        name='Text',
        description='Text',
        default='',
        update=updateNode)

    text_offset: FloatProperty(
        name='Text Offset',
        description='Text offset',
        default=0,
        update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location A")
        self.inputs.new('SvVerticesSocket', "Location B")
        self.inputs.new('SvStringsSocket', "Dim. Type").prop_name = 'dimension_type'
        self.inputs.new('SvStringsSocket', "Dim. Offset").prop_name = 'dimension_offset'
        self.inputs.new('SvStringsSocket', "Font Size").prop_name = 'font_size'
        self.inputs.new('SvStringsSocket', "Text Offset").prop_name = 'text_offset'

        self.inputs.new('SvSvgSocket', "Text Fill / Stroke")
        self.inputs.new('SvSvgSocket', "Lines Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, "line_extension", expand=False)
        layout.prop(self, "decimal_precision", expand=False)
        layout.prop(self, "units", expand=False)
        layout.prop(self, "font_family", expand=False)
        if self.font_family == 'user':
            layout.prop(self, "user_font")

    def process(self):

        if not self.outputs[0].is_linked:
            return
        params_in = [s.sv_get(deepcopy=False) for s in self.inputs[:6]]
        texts_out = []
        params_in.append(self.inputs['Text Fill / Stroke'].sv_get(deepcopy=False, default=None))
        params_in.append(self.inputs['Lines Fill / Stroke'].sv_get(deepcopy=False, default=None))
        font_family = self.user_font if self.font_family == 'user' else self.font_family

        for params in zip(*mlr(params_in)):
            svg_texts = []

            for local_params in zip(*mlr(params)):
                svg_texts.append(SvgDimension(*local_params, font_family, self))

            texts_out.append(SvgGroup(svg_texts))

        self.outputs[0].sv_set(texts_out)



def register():
    bpy.utils.register_class(SvSvgDimensionNode)


def unregister():
    bpy.utils.unregister_class(SvSvgDimensionNode)
