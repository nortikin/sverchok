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
import sys
from bpy.props import EnumProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_cycle as mlr
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode

def boolean_internal(VA, PA, VB, PB, operation, solver):
    """
    Create two temporary mesh objects from the given vertices and faces,
    apply a Boolean modifier on object A using object B as the target,
    then extract the resulting geometry.
    """
    #create temporary object A
    mesh_a = bpy.data.meshes.new("temp_mesh_a")
    mesh_a.from_pydata(VA, [], PA)
    mesh_a.update()
    obj_a = bpy.data.objects.new("temp_obj_a", mesh_a)
    bpy.context.collection.objects.link(obj_a)

    #create temporary object B
    mesh_b = bpy.data.meshes.new("temp_mesh_b")
    mesh_b.from_pydata(VB, [], PB)
    mesh_b.update()
    obj_b = bpy.data.objects.new("temp_obj_b", mesh_b)
    bpy.context.collection.objects.link(obj_b)

    mod = obj_a.modifiers.new(name="Boolean", type='BOOLEAN')
    mod.object = obj_b
    mod.solver = solver

    if operation == 'ITX':
        mod.operation = 'INTERSECT'
    elif operation == 'JOIN':
        mod.operation = 'UNION'
    elif operation == 'DIFF':
        mod.operation = 'DIFFERENCE'

    #apply modifier
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj_a.evaluated_get(depsgraph)
    new_mesh = bpy.data.meshes.new_from_object(obj_eval)

    verts = [list(v.co) for v in new_mesh.vertices]
    faces = [list(p.vertices) for p in new_mesh.polygons]

    #cleanup
    bpy.data.meshes.remove(new_mesh)
    bpy.data.objects.remove(obj_a, do_unlink=True)
    bpy.data.objects.remove(obj_b, do_unlink=True)
    bpy.data.meshes.remove(mesh_a)
    bpy.data.meshes.remove(mesh_b)

    return verts, faces

class SvInternalBooleanNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    '''Internal Boolean Node using Blender’s Boolean Modifier'''
    bl_idname = 'SvInternalBooleanNode'
    bl_label = 'Internal Boolean'
    bl_icon = 'MOD_BOOLEAN'

    mode_options = [
        ("ITX", "Intersect", "", 0),
        ("JOIN", "Union", "", 1),
        ("DIFF", "Difference", "", 2)
    ]

    selected_mode: EnumProperty(
        items=mode_options,
        description="Select the Boolean operation (using Blender's internal modifier)",
        default="ITX",
        update=updateNode)

    solver_options: EnumProperty(
        items=[
            ("FAST", "Fast", "Fast, but does not support overlapping geometry"),
            ("EXACT", "Exact", "Best result")
        ],
        description="Select solver type for the Boolean modifier",
        default="EXACT",
        update=updateNode)

    def update_mode(self, context):
        self.inputs['Verts A'].hide_safe = self.nest_objs
        self.inputs['Polys A'].hide_safe = self.nest_objs
        self.inputs['Verts B'].hide_safe = self.nest_objs
        self.inputs['Polys B'].hide_safe = self.nest_objs
        self.inputs['Verts Nested'].hide_safe = not self.nest_objs
        self.inputs['Polys Nested'].hide_safe = not self.nest_objs
        updateNode(self, context)

    nest_objs: BoolProperty(
        name="Accumulate Nested",
        description="Boolean the first two objects, then apply subsequent booleans to the result one by one",
        default=False,
        update=update_mode)

    out_last: BoolProperty(
        name="Only Final Result",
        description="Output only the final iteration result",
        default=True,
        update=update_mode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts A')
        self.inputs.new('SvStringsSocket',  'Polys A')
        self.inputs.new('SvVerticesSocket', 'Verts B')
        self.inputs.new('SvStringsSocket',  'Polys B')
        self.inputs.new('SvVerticesSocket', 'Verts Nested').hide_safe = True
        self.inputs.new('SvStringsSocket',  'Polys Nested').hide_safe = True
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Polygons')

    @property
    def sv_internal_links(self):
        if self.nest_objs:
            return [
                (self.inputs['Verts Nested'], self.outputs[0]),
                (self.inputs['Polys Nested'], self.outputs[1]),
            ]
        else:
            return super().sv_internal_links

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)
        layout.prop(self, "solver_options", text="Solver")
        col = layout.column(align=True)
        col.prop(self, "nest_objs", toggle=True)
        if self.nest_objs:
            col.prop(self, "out_last", toggle=True)

    def process(self):
        OutV, OutP = self.outputs
        if not OutV.is_linked:
            return
        VertA, PolA, VertB, PolB, VertN, PolN = self.inputs
        SMode = self.selected_mode
        solver = self.solver_options
        out = []
        recursionlimit = sys.getrecursionlimit()
        sys.setrecursionlimit(10000)

        if not self.nest_objs:
            for v1, p1, v2, p2 in zip(*mlr([VertA.sv_get(), PolA.sv_get(),
                                              VertB.sv_get(), PolB.sv_get()])):
                out.append(boolean_internal(v1, p1, v2, p2, SMode, solver))
        else:
            vnest, pnest = VertN.sv_get(), PolN.sv_get()
            First = boolean_internal(vnest[0], pnest[0], vnest[1], pnest[1], SMode, solver)
            if not self.out_last:
                out.append(First)
                for i in range(2, len(vnest)):
                    out.append(boolean_internal(First[0], First[1], vnest[i], pnest[i], SMode, solver))
                    First = out[-1]
            else:
                for i in range(2, len(vnest)):
                    First = boolean_internal(First[0], First[1], vnest[i], pnest[i], SMode, solver)
                out.append(First)
        sys.setrecursionlimit(recursionlimit)
        OutV.sv_set([i[0] for i in out])
        if OutP.is_linked:
            OutP.sv_set([i[1] for i in out])

def register():
    bpy.utils.register_class(SvInternalBooleanNode)

def unregister():
    bpy.utils.unregister_class(SvInternalBooleanNode)
