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

class SvgPath():
    def __repr__(self):
        return "<SVG Path>"
    def __init__(self, verts, attributes, mode, cyclic):
        self.verts = verts
        self.mode = mode
        self.attributes = attributes[0] if attributes else []

        self.cyclic = cyclic

    def draw(self, height, scale):
        verts = self.verts
        svg = '<path '
        if self.mode == 'LIN' or len(verts) < 3:
            svg += 'd="M {} {}'.format(verts[0][0]* scale, height-verts[0][1]* scale)
            for v in verts[1:]:
                svg += ' L {} {}'.format(scale * v[0], height - scale * v[1])
        else:
            svg += 'd="M {} {}'.format(verts[0][0]* scale, height-verts[0][1]* scale)
            svg += ' Q {} {}'.format(verts[1][0]* scale, height-verts[1][1]* scale)
            svg += ' {} {}'.format(verts[2][0]* scale, height-verts[2][1]* scale)
            for v in verts[3:]:
                svg += ' T {} {}'.format(scale * v[0], height - scale * v[1])
        if self.cyclic:
            svg += ' Z" '
        else:
            svg += '" '

        if self.attributes:
            svg += self.attributes.draw(height, scale)
        svg += '/>'
        return svg

class SvSvgPathNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: SVG Path
    Tooltip: Generate SVG Path
    """
    bl_idname = 'SvSvgPathNode'
    bl_label = 'Path SVG'
    bl_icon = 'MESH_CIRCLE'

    modes = [('LIN', 'Linear', '',0), ('QUAD', 'Quadratic', '',1)]
    mode: EnumProperty(
        name='Mode',
        items=modes,
        update=updateNode
    )
    cyclic: BoolProperty(
        name='Cyclic',
        update=updateNode
    )
    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        layout.prop(self, "cyclic", expand=True)

    def process(self):

        if not self.outputs[0].is_linked:
            return
        verts_in = self.inputs['Vertices'].sv_get(deepcopy=True)
        shapes = []
        atts_in = self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=[[]])
        for verts, atts in zip(*mlr([verts_in, atts_in])):
            shapes.append(SvgPath(verts, atts, self.mode, self.cyclic))
        self.outputs[0].sv_set(shapes)



def register():
    bpy.utils.register_class(SvSvgPathNode)


def unregister():
    bpy.utils.unregister_class(SvSvgPathNode)
