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

import time

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (
    match_long_repeat,
    updateNode, match_long_cycle)

from sverchok.utils.boolean_2d_core import crop_verts, crop_edges, crop_pols


list_match_Items = [
    ("Long Repeat", "Long Repeat", "Repeat last item until match the longest list", 0),
    ("Long Cycle", "Long Cycle", "Cycle through the shorter lists until match the longest list", 1)]


def list_matcher(a, list_match):
    '''list match behavior'''
    if list_match == "Long Cycle":
        return match_long_cycle(a)
    else:
        return match_long_repeat(a)



class SvBoolean2DNode(bpy.types.Node, SverchCustomTreeNode):
    '''Crop 2D'''
    bl_idname = 'SvBoolean2DNode'
    bl_label = 'Boolean 2D'
    bl_icon = 'FORCE_FORCE'


    exclude_cutter = BoolProperty(
        name='exclude_cutter',
        description='Exclude cutting geometry from output',
        default=0,
        update=updateNode)

    check_coincidences = BoolProperty(
        name='Check Coincidences',
        description='Search for coincidences between input geometry and cutter',
        default=True,
        update=updateNode)

    check_concavity = BoolProperty(
        name='Check Concavity',
        description='Disabling this with make the node faster but will fail in some scenarios',
        default=True,
        update=updateNode)

    action_modes = [
        ("Intersect", "Intersect", "Intersect geometry with cutter geometry", 1),
        ("Union", "Int + Diff", "Intersect + Difference", 2),
        ("Difference", "Difference", "Difference", 3)]
    modes = [
        ("Vector", "Vect.", "Verts input and output", 1),
        ("Edge", "Edge", "Edges input and output", 2),
        ("Polygon", "Polygon", "Polygon input and output", 3)]
    output_modes = [
        ("Edge", "Edge", "Edges", 1),
        ("Polygon", "Poly.", "polygons", 2)]
    partial_modes = [
        ("Excl.", "Exclude", "Exclude partially selected", 0),
        ("Cut", "Cut", "Cut partially selected", 1),
        ("Include", "Include", "Include partially selected", 2),
        ("Only", "Only", "Only partially selected", 3)]

    def mode_change(self, context):
        '''update sockets'''
        inputs, outputs = self.inputs, self.outputs
        if self.mode == 'Vector':
            if not inputs[1].hide_safe:
                inputs[1].hide_safe = True
                outputs[1].hide_safe = True
            if not inputs[2].hide_safe:
                inputs[2].hide_safe = True
                outputs[2].hide_safe = True

        elif self.mode == 'Edge':
            if inputs[1].hide_safe:
                inputs[1].hide_safe = False
                outputs[1].hide_safe = False
            if not inputs[2].hide_safe:
                inputs[2].hide_safe = True
                outputs[2].hide_safe = True

        if self.mode == 'Polygon':
            if inputs[1].hide_safe:
                inputs[1].hide_safe = False
                outputs[1].hide_safe = False
            if inputs[2].hide_safe:
                inputs[2].hide_safe = False
                outputs[2].hide_safe = False



        updateNode(self, [])

    mode = EnumProperty(
        default='Polygon',
        items=modes,
        name='Mode',
        description='Crop Mode',
        update=mode_change)

    list_match = EnumProperty(
        name="list_match",
        description="Behavior on different list lengths",
        items=list_match_Items, default="Long Repeat",
        update=updateNode)

    mask_t = FloatProperty(
        name='Mask tolerance',
        description="Mask tolerance",
        min=0, default=1.0e-5,
        step=0.02, update=updateNode)

    mode_action = EnumProperty(
        name="Operation",
        description="What do you want to get",
        items=action_modes, default="Intersect",
        update=updateNode)

    partial_mode = EnumProperty(
        name="Partially affected",
        description="Behaviour on partially selected geometry",
        items=partial_modes, default="Cut",
        update=updateNode)

    def sv_init(self, context):
        '''initialize the sockets'''
        inputs, outputs = self.inputs, self.outputs
  
        inputs.new('VerticesSocket', "Verts_in")
        inputs.new('StringsSocket', "Edges_in")
        inputs.new('StringsSocket', "Pols_in")
        inputs.new('VerticesSocket', "Verts Cutter")
        inputs.new('StringsSocket', "Pols Cutter")
        outputs.new('VerticesSocket', "Vertices", "Vertices")
        outputs.new('StringsSocket', "Edges", "Edges")
        outputs.new('StringsSocket', "Polygons", "Pols")

    def draw_buttons(self, context, layout):
        '''draw node ui'''
        # layout.label("Working mode")
        # layout.scale_y = 0.5
        
        layout.prop(self, "mode", expand=False)
        # layout.props_enum(self, "mode")
        # layout.scale_y = 0.8
        # b = layout.box()
        # col = layout.row(align=True)
        # col.label("Operation")
        # layout.scale_y = 1
        layout.prop(self, "mode_action", expand=False)


        if self.mode == 'Polygon':
            if not self.mode_action == 'Union':
                layout.prop(self, "partial_mode", expand=False)
            if self.mode_action == 'Intersect' and self.partial_mode == 'Cut':
                layout.prop(self, "exclude_cutter", text="Exclude cutter")


        elif self.mode == 'Edge':
            if not self.mode_action == 'Union':
                layout.prop(self, "partial_mode", expand=True)
            if self.partial_mode == 'Cut':
                layout.prop(self, "exclude_cutter", text="Exclude cutter")
        else:
            layout.prop(self, "exclude_cutter", text="Exclude cutter")


    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        if self.mode != "Vector":
            layout.prop(self, "check_coincidences")
            layout.prop(self, "check_concavity")
        layout.prop(self, 'mask_t')

        layout.prop(self, "list_match", expand=True)

    def get_inputs(self):
        '''get incoming data'''
        inputs = self.inputs
        parameters = []
        verts_all = inputs['Verts_in'].sv_get(default=[[]])
        parameters.append(verts_all)
        if self.mode in ['Edge', 'Polygon']:
            edges_all = inputs['Edges_in'].sv_get(default=[[]])
            parameters.append(edges_all)
        else:
            parameters.append([[]])
        if self.mode == 'Polygon':
            pols_all = inputs['Pols_in'].sv_get(default=[[]])
            parameters.append(pols_all)
        else:
            parameters.append([[]])

        verts_all_cutter = inputs['Verts Cutter'].sv_get(default=[[]])
        pols_all_cutter = inputs['Pols Cutter'].sv_get(default=[[]])
        parameters.append(verts_all_cutter)
        parameters.append(pols_all_cutter)
        # family = list_matcher([verts_all, edges_all, pols_all, verts_all_cutter, pols_all_cutter], self.list_match)
        family = list_matcher(parameters, self.list_match)

        return family

    def process(self):
        '''Function called every tree update'''

        inputs, outputs = self.inputs, self.outputs
        if not (any(s.is_linked for s in outputs) and any(s.is_linked for s in inputs[:3])):
            return

        timer = time.clock()

        output_lists = [[], [], []]
        if self.mode == 'Vector':
            _ = [crop_verts(self, output_lists, params) for params in zip(*self.get_inputs())]
        elif self.mode == 'Edge':
            _ = [crop_edges(self, output_lists, params) for params in zip(*self.get_inputs())]
        else:
            _ = [crop_pols(self, output_lists, params) for params in zip(*self.get_inputs())]

        vertices_out, edges_out, pols_out = output_lists
        outputs['Vertices'].sv_set(vertices_out)
        if self.mode == 'Edge' or self.mode == 'Polygon':
            if outputs['Edges'].is_linked:
                outputs['Edges'].sv_set(edges_out)
        if self.mode == 'Polygon':
            if outputs['Polygons'].is_linked:
                outputs['Polygons'].sv_set(pols_out)
        print("dur:", time.clock()-timer)


def register():
    '''add Class to Blender'''
    bpy.utils.register_class(SvBoolean2DNode)


def unregister():
    '''delete Class in Blender'''
    bpy.utils.unregister_class(SvBoolean2DNode)
