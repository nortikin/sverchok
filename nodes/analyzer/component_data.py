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

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, match_long_repeat, fullList, dataCorrect
from sverchok.utils.listutils import lists_flat

from sverchok.utils.modules.polygon_utils import faces_modes_dict, areas_from_polygons

from sverchok.utils.modules.edge_utils import edges_modes_dict
from sverchok.utils.modules.vertex_utils import vertex_modes_dict


modes_dicts = {
    'Verts': vertex_modes_dict,
    'Edges': edges_modes_dict,
    'Faces': faces_modes_dict
}

socket_dict = {
    "v": "SvVerticesSocket",
    "s":"SvStringsSocket",
    "m": "SvMatrixSocket"
}
class SvComponentDataNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Norm, Tang, Mat
    Tooltip: Select vertices, edges, faces similar to selected ones

    """

    bl_idname = 'SvComponentDataNode'
    bl_label = 'Component Analyzer'
    bl_icon = 'VIEWZOOM'


    modes = [
        ('Verts', "Vertices", "Vertices Operators", 0),
        ('Edges', "Edges", "Edges Operators", 1),
        ('Faces', "Faces", "Faces Operators", 2)
    ]

    edge_modes =   [(k, k, descr, ident) for k, (ident, _, _, _, _, _, descr) in sorted(edges_modes_dict.items(), key=lambda k: k[1][0])]
    vertex_modes = [(k, k, descr, ident) for k, (ident, _, _, _, _, _, descr) in sorted(vertex_modes_dict.items(), key=lambda k: k[1][0])]
    face_modes =   [(k, k, descr, ident) for k, (ident, _, _, _, _, _, descr) in sorted(faces_modes_dict.items(), key=lambda k: k[1][0])]

    cmp_modes = [
        ("0", "=", "Compare by ==", 0),
        ("1", ">=", "Compare by >=", 1),
        ("2", "<=", "Compare by <=", 2)
    ]
    @throttled
    def update_mode(self, context):
        # for mode in self.modes:
        info = modes_dicts[self.mode][self.actual_mode()]
        sockt_type = info[1]
        sockt_names = info[5].split(' ')
        for i, s in enumerate(sockt_type):
            self.outputs[i].name = sockt_names[i]
            self.outputs[i].replace_socket(socket_dict[s])
        if len(sockt_type) < len(self.outputs):
            for s in self.outputs[len(sockt_type):]:
                s.hide_safe = True
        updateNode(self, context)

    mode: EnumProperty(
        name="Component",
        items=modes,
        default='Faces',
        update=update_mode)

    vertex_mode: EnumProperty(
        name="Operator",
        items=vertex_modes,
        default="Normal",
        update=update_mode)
    edge_mode: EnumProperty(
        name="Operator",
        items=edge_modes,
        default="Length",
        update=update_mode)
    face_mode: EnumProperty(
        name="Operator",
        items=face_modes,
        default="Normal",
        update=update_mode)
    flat_output: BoolProperty(
        name="Flat output",
        description="Flatten output by list-joining level 1",
        default=True,
        update=updateNode)
    sum_items: BoolProperty(
        name="Separate", description="Separate tiles",
        default=False, update=updateNode)

    def actual_mode(self):
        if self.mode == 'Verts':
            component_mode = self.vertex_mode
        elif self.mode == 'Edges':
            component_mode = self.edge_mode
        else:
            component_mode = self.face_mode
        return component_mode

    def draw_label(self):
        text = self.mode + " "+ self.actual_mode()
        return text

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

        if self.mode == 'Verts':
            layout.prop(self, "vertex_mode", text="")
        elif self.mode == 'Edges':
            layout.prop(self, "edge_mode", text="")
            if self.edge_mode == "Length":
                layout.prop(self, "sum_items", text="Sum Lengths")
        elif self.mode == 'Faces':
            layout.prop(self, "face_mode", text="")
            if self.face_mode == "Area":
                layout.prop(self, "sum_items", text="Sum Areas")


    def sv_init(self, context):
        inew = self.inputs.new
        inew('SvVerticesSocket', "Vertices")
        inew('SvStringsSocket', "Edges")
        inew('SvStringsSocket', "Faces")


        onew = self.outputs.new
        onew('SvStringsSocket', "Vals")
        onew('SvVerticesSocket', "Faces")

        self.update_mode(context)

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return
        modes_dict = modes_dicts[self.mode]
        component_mode = self.actual_mode()
        func_inputs = modes_dict[component_mode][3]
        params = []
        if "v" in func_inputs:
            params.append(self.inputs['Vertices'].sv_get())
        if "e" in func_inputs:
            params.append(self.inputs['Edges'].sv_get(default=[[]]))
        if "p" in func_inputs:
            params.append(self.inputs['Faces'].sv_get(default=[[]]))

        result_vals = []

        meshes = match_long_repeat(params)
        func = modes_dict[component_mode][4]
        for param in zip(*meshes):
            if "s" in func_inputs:
                vals = func(*param, self.sum_items)
            else:
                vals = func(*param)
            result_vals.append(vals)


        if len(modes_dict[component_mode][1]) > 1:
            results = list(zip(*result_vals))
            for r, s in zip(results, self.outputs):
                s.sv_set(dataCorrect(r))

        else:
            if 'u' in modes_dict[component_mode][2]:
                result_vals = lists_flat([result_vals])[0]
            self.outputs[0].sv_set(result_vals)

        # self.outputs['Edges'].sv_set(result_edges)
        # self.outputs['Faces'].sv_set(result_faces)

def register():
    bpy.utils.register_class(SvComponentDataNode)


def unregister():
    bpy.utils.unregister_class(SvComponentDataNode)
