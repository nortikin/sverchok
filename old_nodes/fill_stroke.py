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
    def __init__(self, fill_color, stroke_width, stroke_color, dash_pattern, node):
        self.fill_color = fill_color
        self.stroke_width = stroke_width
        self.stroke_color = stroke_color
        self.node = node
        self.dash_pattern = dash_pattern

    def draw(self, height, scale):
        svg = 'style="\n'
        if self.node.fill_mode == 'NONE':
            svg += '    fill:none;\n    fill-opacity:0;'
        else:
            col_p = self.fill_color
            svg += f'    fill:rgb{(int(255*col_p[0]), int(255*col_p[1]), int(255*col_p[2]))};\n'
            svg += f'    fill-opacity:{col_p[3]};\n'
        if self.node.stroke_mode == 'NONE':
            svg += '    stroke:none;\n    stroke-opacity:0;\n    stroke-width:0\n'
        else:
            col_p = self.stroke_color
            svg += f'    stroke:rgb{(int(255*col_p[0]), int(255*col_p[1]), int(255*col_p[2]))};\n'
            svg += f'    stroke-opacity:{col_p[3]};\n'
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

    replacement_nodes = [('SvSvgFillStrokeNodeMk2', None, None)]
    
    def update_actual_sockets(self):
        self.inputs['Fill Color'].hide_safe = self.fill_mode == 'NONE'
        self.inputs['Stroke Color'].hide_safe = self.stroke_mode == 'NONE'
        self.inputs['Stroke Width'].hide_safe = self.stroke_mode == 'NONE'
        self.inputs['Dash Pattern'].hide_safe = self.stroke_type == 'Solid' or self.stroke_mode == 'NONE'
    def update_sockets(self, context):
        self.update_actual_sockets()
        updateNode(self, context)

    fill_modes = [('NONE', 'None', '', 0), ('FLAT', 'Flat', '', 1)]
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
# fill-rule stroke-dasharray stroke-linecap, stroke-linejoin

    def sv_init(self, context):

        self.inputs.new('SvColorSocket', "Fill Color").prop_name = 'fill_color'
        self.inputs.new('SvColorSocket', "Stroke Color").prop_name = 'stroke_color'
        self.inputs.new('SvStringsSocket', "Stroke Width").prop_name = 'stroke_width'
        self.inputs.new('SvStringsSocket', "Dash Pattern")
        self.update_actual_sockets()
        self.outputs.new('SvSvgSocket', "Fill / Stroke")

    def draw_buttons(self, context, layout):
        layout.prop(self, "fill_mode", expand=False)
        col = layout.column(align=True)
        col.prop(self, "stroke_mode", expand=False)
        if self.stroke_mode != 'NONE':

            col.prop(self, "stroke_linecap", expand=False)
            col.prop(self, "stroke_linejoin", expand=False)
            col.prop(self, "stroke_type", expand=False)
            if self.fill_mode != 'NONE':
                layout.prop(self, "paint_order", expand=False)


    def process(self):

        if not self.outputs[0].is_linked:
            return
        params_in = [s.sv_get(deepcopy=False, default=[[None]]) for s in self.inputs]
        attributes_out = []
        for params in zip(*mlr(params_in)):
            attributes = []
            dash_pattern = params[-1]
            for fill_color, stroke_color, stroke_width  in zip(*mlr(params[:-1])):
                attributes.append(SvgAttributes(fill_color, stroke_width, stroke_color, dash_pattern, self))
            attributes_out.append(attributes)
        self.outputs[0].sv_set(attributes_out)



def register():
    bpy.utils.register_class(SvSvgFillStrokeNode)


def unregister():
    bpy.utils.unregister_class(SvSvgFillStrokeNode)
