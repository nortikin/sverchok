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
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty, FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4, updateNode

class SvgAttributes():
    def __repr__(self):
        return "SVG Attributes"
    def __init__(self, fill, stroke, stroke_width, dash_pattern, node):
        self.fill = fill
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.dash_pattern = dash_pattern
        self.node = node

    def draw(self, document):
        scale = document.scale
        svg = 'style="\n'
        svg += f'    mix-blend-mode:{self.node.blend_mode.lower()};\n'
        if self.node.fill_mode == 'NONE':
            svg += '    fill:none;\n    fill-opacity:0;\n'
        elif self.node.fill_mode == 'FLAT':
            color = self.fill
            svg += f'    fill:rgb{(int(255*color[0]), int(255*color[1]), int(255*color[2]))};\n'
            svg += f'    fill-opacity:{color[3]};\n'
        else:
            document.defs[self.fill.name] = self.fill
            svg += f'    fill:url(#{self.fill.name});\n'
        if self.node.stroke_mode == 'NONE':
            svg += '    stroke:none;\n    stroke-opacity:0;\n    stroke-width:0\n'
        else:
            if self.node.stroke_mode == 'FLAT':
                color = self.stroke
                svg += f'    stroke:rgb{(int(255*color[0]), int(255*color[1]), int(255*color[2]))};\n'
                svg += f'    stroke-opacity:{color[3]};\n'
            else:
                document.defs[self.stroke.name] = self.stroke
                svg += f'    stroke:url(#{self.stroke.name});\n'
            svg += f'    stroke-width:{self.stroke_width*scale};\n'
            svg += f'    stroke-linecap:{self.node.stroke_linecap.lower()};\n'
            svg += f'    stroke-linejoin:{self.node.stroke_linejoin.lower()};\n'
            svg += f'    paint-order:markers {self.node.paint_order.lower().replace("_", " ")};\n'

            if self.dash_pattern[0]:
                dasharray = [num*scale for num in self.dash_pattern]
                svg += f'    stroke-dasharray:{str(dasharray)[1:-1].replace(",", "")};\n'
        svg += '"'

        return svg

class SvSvgFillStrokeNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: color, line width
    Tooltip: Define Fill /Stroke Style for svg objects
    """
    bl_idname = 'SvSvgFillStrokeNode'
    bl_label = 'Fill / Stroke SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_FILL_STROKE_SVG'

    def update_actual_sockets(self):
        self.inputs['Fill Color'].hide_safe = self.fill_mode != 'FLAT'
        self.inputs['Fill Pattern'].hide_safe = self.fill_mode != 'PATTERN'
        self.inputs['Stroke Color'].hide_safe = self.stroke_mode != 'FLAT'
        self.inputs['Stroke Pattern'].hide_safe = self.stroke_mode != 'PATTERN'
        self.inputs['Stroke Width'].hide_safe = self.stroke_mode == 'NONE'
        self.inputs['Dash Pattern'].hide_safe = self.stroke_type == 'Solid' or self.stroke_mode == 'NONE'

    def update_sockets(self, context):
        self.update_actual_sockets()
        updateNode(self, context)

    blend_mode: EnumProperty(
        name='Blend',
        items=enum_item_4(['Normal', 'Multiply', 'Screen', 'Overlay', 'Darken', 'Lighten', 'Color-dodge', 'Color-burn', 'Hard-light', 'Soft-light', 'Difference', 'Exclusion', 'Hue', 'Saturation', 'Color', 'Luminosity']),
        default="Normal",
        update=update_sockets
        )
    fill_modes = [('NONE', 'None', '', 0), ('FLAT', 'Flat', '', 1), ('PATTERN', 'Pattern', '', 2)]
    fill_mode: EnumProperty(
        name='Fill',
        items=fill_modes,
        default="FLAT",
        update=update_sockets
        )
    stroke_mode: EnumProperty(
        name='Stroke',
        items=fill_modes,
        update=update_sockets
        )
    stroke_width: FloatProperty(
        name='Stroke width',
        description='Stroke width',
        default=1.0,
        update=updateNode
        )
    stroke_color: FloatVectorProperty(
        name="Stroke Color",
        description="Color",
        size=4,
        min=0.0,
        max=1.0,
        default=(0,0,0,1),
        subtype='COLOR',
        update=update_sockets
        )
    stroke_linecap: EnumProperty(
        name='Cap',
        description='Line Cap',
        items=enum_item_4(['Butt', 'Round', 'Square']),
        update=updateNode
        )
    stroke_linejoin: EnumProperty(
        name='Join',
        description='Line Join',
        items=enum_item_4(['Bevel', 'Miter', 'Round']),
        update=updateNode
        )
    paint_order: EnumProperty(
        name='Order',
        description="Paint Order",
        items=enum_item_4(['Fill Stroke', 'Stroke Fill']),
        update=updateNode
        )
    stroke_type: EnumProperty(
        name='Type',
        items=enum_item_4(['Solid', 'Dashed']),
        update=update_sockets
        )

    fill_color: FloatVectorProperty(
        name="Fill Color",
        description="Color", size=4,
        min=0.0,
        max=1.0,
        default=(0,0,0,1),
        subtype='COLOR',
        update=updateNode
        )


    def sv_init(self, context):

        self.inputs.new('SvColorSocket', "Fill Color").prop_name = 'fill_color'
        self.inputs.new('SvSvgSocket', "Fill Pattern")
        self.inputs.new('SvColorSocket', "Stroke Color").prop_name = 'stroke_color'
        self.inputs.new('SvSvgSocket', "Stroke Pattern")
        self.inputs.new('SvStringsSocket', "Stroke Width").prop_name = 'stroke_width'
        self.inputs.new('SvStringsSocket', "Dash Pattern")
        self.update_actual_sockets()
        self.outputs.new('SvSvgSocket', "Fill / Stroke")

    def draw_buttons(self, context, layout):
        layout.prop(self, "blend_mode", expand=False)
        layout.prop(self, "fill_mode", expand=False)
        col = layout.column(align=True)
        col.prop(self, "stroke_mode", expand=False)
        if self.stroke_mode != 'NONE':

            col.prop(self, "stroke_linecap", expand=False)
            col.prop(self, "stroke_linejoin", expand=False)
            col.prop(self, "stroke_type", expand=False)
            if self.fill_mode != 'NONE':
                layout.prop(self, "paint_order", expand=False)

    def get_data(self):
        if self.fill_mode == 'FLAT':
            fill = self.inputs['Fill Color'].sv_get(deepcopy=False)
        elif self.fill_mode == 'PATTERN':
            fill = self.inputs['Fill Pattern'].sv_get(deepcopy=False, default=[[None]])
        else:
            fill = [[None]]
        if self.stroke_mode == 'FLAT':
            stroke = self.inputs['Stroke Color'].sv_get(deepcopy=False)
        elif self.stroke_mode == 'PATTERN':
            stroke = self.inputs['Stroke Pattern'].sv_get(deepcopy=False, default=[[None]])
        else:
            stroke = [[None]]

        stroke_width = self.inputs['Stroke Width'].sv_get(deepcopy=False)
        dash_pattern = self.inputs['Dash Pattern'].sv_get(deepcopy=False, default=[[None]])

        return mlr([fill, stroke, stroke_width, dash_pattern])

    def process(self):

        if not self.outputs[0].is_linked:
            return
        params_in = [s.sv_get(deepcopy=False, default=[[None]]) for s in self.inputs]
        params_in = self.get_data()

        attributes_out = []
        for params in zip(*params_in):
            attributes = []
            dash_pattern = params[-1]
            for fill, stroke, stroke_width  in zip(*mlr(params[:-1])):
                attributes.append(SvgAttributes(fill, stroke, stroke_width, dash_pattern, self))
            attributes_out.append(attributes)
        self.outputs[0].sv_set(attributes_out)



def register():
    bpy.utils.register_class(SvSvgFillStrokeNode)


def unregister():
    bpy.utils.unregister_class(SvSvgFillStrokeNode)
