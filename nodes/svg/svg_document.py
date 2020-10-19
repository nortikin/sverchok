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
import webbrowser
import sverchok
import bpy
from bpy.props import (
    BoolProperty, StringProperty, EnumProperty, FloatProperty
    )

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

evolver_mem = {}

pixels_to_mm = 3.77952756

def spawn_server(save_path, file_name):

    _dirname = os.path.dirname(sverchok.__file__)
    path1 = os.path.join(_dirname, 'utils', 'sv_svg_server.htm')
    path2 = os.path.join(_dirname, 'utils', 'sv_svg_custom_server.htm')
    # path2 = os.path.join(save_path, 'sv_svg_custom_server.html')
    file_path = os.path.join(save_path, f'{file_name}.svg')
    file_path_js = file_path.replace("\\","/")

    with open(path1) as origin:
        with open(path2, 'w') as destination:
            for line in origin:
                if '{{variable}}' in line:
                    # destination.write(line.replace("{{variable}}", f'"{file_name}.svg"'))
                    destination.write(line.replace("{{variable}}", f'"{file_path_js}"'))
                else:
                    destination.write(line)

    webbrowser.open(path2)


class SvSvgServer(bpy.types.Operator):
    """
    Opens in web browser a html file that updates frecuently showing the changes in the SVG file
    """
    bl_idname = "node.sv_svg_server"
    bl_label = "Append"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        tree = bpy.data.node_groups[self.idtree]
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        inputs = node.inputs
        if not (inputs['Folder Path'].is_linked and inputs['SVG Objects'].is_linked):

            return {'FINISHED'}

        save_path = node.inputs[0].sv_get()[0][0]
        file_name = node.file_name
        bpy.ops.node.svg_write(idtree=self.idtree, idname=self.idname)
        spawn_server(save_path, file_name)

        return {'FINISHED'}

def get_template(complete_name):
    old_svg_file = open(complete_name, "r")
    data = old_svg_file.read()
    file_end = data.find("</svg>")
    return data[:file_end]


def add_head(width, height, units):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}{units}" height="{height}{units}">\n'
    return svg


def draw_svg_defs(document, defs_list, all_defs_list):
    svg_defs=''
    new_def_list = []
    for def_key in defs_list:
        svg_defs += document.defs[def_key].draw(document)

        svg_defs += '\n'
    for def_key in document.defs:
        if def_key not in all_defs_list:
            new_def_list.append(def_key)
            all_defs_list.append(def_key)

    if new_def_list:
        svg_defs += draw_svg_defs(document, new_def_list, all_defs_list)
    return svg_defs

class SvSVGWrite(bpy.types.Operator):

    bl_idname = "node.svg_write"
    bl_label = "Write"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]

        inputs = node.inputs
        if not (inputs['Folder Path'].is_linked and inputs['SVG Objects'].is_linked):

            return {'FINISHED'}

        save_path = inputs[0].sv_get()[0][0]
        template_path = inputs[1].sv_get()[0] if inputs[1].is_linked else []
        shapes = inputs[2].sv_get()

        svg = ''
        scale = node.doc_scale
        doc_width = node.doc_width
        doc_height = node.doc_height
        if template_path:
            svg_head = get_template(template_path[0])
        else:
            units = 'mm'if node.units == 'MM' else 'px'
            svg_head = add_head(doc_width, doc_height, units)
        height = doc_height
        if node.units == 'MM':
            scale *= pixels_to_mm
            height *= pixels_to_mm

        document = lambda: None
        document.defs = {}
        document.height = height
        document.scale = scale
        svg_shapes = ''
        for shape in shapes:
            svg_shapes += shape.draw(document)
            svg_shapes += '\n'


        defs_list= list(document.defs)
        svg_defs = '<defs>\n'
        svg_defs += draw_svg_defs(document, defs_list, defs_list)

        svg_defs += '</defs>\n'
        svg_end = '</svg>'
        file_name = node.file_name
        complete_name = os.path.join(save_path, file_name+".svg")
        svg_file = open(complete_name, "w")
        svg = svg_head + svg_defs +svg_shapes + svg_end
        svg_file.write(svg)

        svg_file.close()
        return {'FINISHED'}


class SvSvgDocumentNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Output SVG
    Tooltip: Creates SVG document, define location, size and units
    """
    bl_idname = 'SvSvgDocumentNode'
    bl_label = 'SVG Document'
    bl_icon = 'RNA'
    sv_icon = 'SV_SVG'

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

    file_name: StringProperty(name="Name", default="Sv_svg")
    live_update: BoolProperty(name='Live Update')

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvFilePathSocket', 'Folder Path')
        self.inputs.new('SvFilePathSocket', 'Template Path')
        self.inputs.new('SvSvgSocket', 'SVG Objects')
        self.outputs.new('SvVerticesSocket', 'Canvas Vertices')
        self.outputs.new('SvStringsSocket', 'Canvas Edges')

    def draw_buttons(self, context, layout):
        layout.prop(self, "live_update")
        self.wrapper_tracked_ui_draw_op(layout, "node.sv_svg_server", icon='RNA', text="Open Server")
        mode_row = layout.split(factor=0.4, align=False)
        mode_row.label(text="Units:")
        mode_row.prop(self, "units", text="")
        layout.prop(self, "file_name")
        layout.prop(self, "doc_width")
        layout.prop(self, "doc_height")
        layout.prop(self, "doc_scale")
        self.wrapper_tracked_ui_draw_op(layout, "node.svg_write", icon='RNA_ADD', text="Write")

    def process(self):

        x = self.doc_width/(self.doc_scale)
        y = self.doc_height/(self.doc_scale)
        verts =[
            (0, 0, 0),
            (x, 0, 0),
            (x, y, 0),
            (0, y, 0),


        ]
        self.outputs['Canvas Vertices'].sv_set([verts])
        self.outputs['Canvas Edges'].sv_set([[(0, 1),(1, 2), (2, 3), (3, 0)]])
        if self.live_update:
            bpy.ops.node.svg_write(idtree=self.id_data.name, idname=self.name)


classes = [SvSvgServer, SvSVGWrite, SvSvgDocumentNode]
register, unregister = bpy.utils.register_classes_factory(classes)
