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
import os
import ast
import random
import time
from collections import namedtuple
from typing import NamedTuple
import numpy as np
import bpy
from bpy.props import (
    BoolProperty, StringProperty, EnumProperty, IntProperty, FloatProperty
    )

from mathutils.noise import seed_set, random
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.core.update_system import make_tree_from_nodes, do_update

evolver_mem = {}

pixels_to_mm = 3.77952756

class SvSvgAppend(bpy.types.Operator):

    bl_idname = "node.svg_append"
    bl_label = "Append"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]

        if not all([s.is_linked for s in node.inputs]):

            return {'FINISHED'}


        return {'FINISHED'}


def add_head(svg, width, height):
    svg += '<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" width="'+str(width) +'mm" height="'+str(height)+'mm">\n'
    return svg

class SvSVGWrite(bpy.types.Operator):

    bl_idname = "node.svg_write"
    bl_label = "Write"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        if not all([s.is_linked for s in node.inputs]):

            return {'FINISHED'}
        svg = ''
        scale = node.doc_scale
        doc_width = node.doc_width
        doc_height = node.doc_height
        svg = add_head(svg, doc_width, doc_height)
        height = doc_height
        if node.units == 'MM':
            scale *= pixels_to_mm
            height *= pixels_to_mm
        shapes = node.inputs[1].sv_get()


        for shape in shapes:
            svg += shape.draw(height, scale)
            svg += '\n'

        svg += '</svg>'
        save_path = node.inputs[0].sv_get()[0]
        file_name = node.file_name
        complete_name = os.path.join(save_path, file_name+".svg")
        svg_file = open(complete_name, "w")
        svg_file.write(svg)

        svg_file.close()
        return {'FINISHED'}

class SvSvgDocumentNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Genetics algorithm
    Tooltip: Advanced node to find the best solution to a defined problem using a genetics algorithm technic
    """
    bl_idname = 'SvSvgDocumentNode'
    bl_label = 'SVG Document'
    bl_icon = 'RNA'

    mode_items = [
        ('MM', 'mm', '', 0),
        ('PIX', 'px', '', 1),
        ]
    units: EnumProperty(
        name="Mode",
        description="Set Fitness as maximun or as minimum",
        items=mode_items,
        update=updateNode
        )
    doc_width: FloatProperty(
        default=210,
        name='Width', description='Document Width',
        update=updateNode)
    doc_height: FloatProperty(
        default=297,
        min=1,
        name='Height', description='Iterations',
        update=updateNode)
    doc_scale: FloatProperty(
        default=10,
        min=1,
        name='Scale', description='Iterations',
        update=updateNode)


    info_label: StringProperty(default="Not Executed")

    memory: StringProperty(default="")
    file_name: StringProperty(default="")

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvFilePathSocket', 'File Path')
        self.inputs.new('SvSvgSocket', 'SVG Objects')
        self.outputs.new('SvVerticesSocket', 'Canvas Vertices')
        self.outputs.new('SvStringsSocket', 'Canvas Edges')



    def draw_buttons(self, context, layout):
        mode_row = layout.split(factor=0.4, align=False)
        mode_row.label(text="Units:")
        mode_row.prop(self, "units", text="")
        layout.prop(self, "file_name")
        layout.prop(self, "doc_width")
        layout.prop(self, "doc_height")
        layout.prop(self, "doc_scale")
        self.wrapper_tracked_ui_draw_op(layout, "node.svg_append", icon='RNA', text="Append")
        self.wrapper_tracked_ui_draw_op(layout, "node.svg_write", icon='RNA_ADD', text="Write")

    def process(self):

        # if self.node_id in evolver_mem and 'genes' in evolver_mem[self.node_id]:
        x = self.doc_width/(self.doc_scale)
        y = self.doc_height/(self.doc_scale)
        verts =[
            (0,0,0),
            (x,0,0),
            (x,y,0),
            (0,y,0),


        ]
        self.outputs['Canvas Vertices'].sv_set([verts])
        self.outputs['Canvas Edges'].sv_set([[(0, 1),(1, 2), (2, 3), (3, 0)]])






classes = [SvSvgAppend, SvSVGWrite, SvSvgDocumentNode]
register, unregister = bpy.utils.register_classes_factory(classes)
