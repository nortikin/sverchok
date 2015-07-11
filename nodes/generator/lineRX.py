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

import copy

import bpy
from bpy.props import IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat

from mathutils import Vector


class SvRxDispatchFunctionTest(bpy.types.Operator):

    bl_idname = "node.svrx_dispatch_function_test"
    bl_label = "Redux dispatcher"

    fn_name = bpy.props.StringProperty(default='')

    def dispatch(self, context, type_op):
        n = context.node

        if type_op == 'SWITCH':
            n.switch_property()

    def execute(self, context):
        self.dispatch(context, self.fn_name)
        return {'FINISHED'}


def make_line(integer, step):
    vertices = [(0.0, 0.0, 0.0)]
    integer = [int(integer) if type(integer) is not list else int(integer[0])]

    if type(step) is not list:
        step = [step]
    fullList(step, integer[0])

    for i in range(integer[0]-1):
        v = Vector(vertices[i]) + Vector((step[i], 0.0, 0.0))
        vertices.append(v[:])

    edges = []
    for i in range(integer[0]-1):
        edges.append((i, i+1))

    return vertices, edges


class LineNodeRx(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'LineNodeRx'
    bl_label = 'LineRx'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = IntProperty(
        name='N Verts', description='Nº Vertices',
        default=2, min=2, max=10,
        options={'ANIMATABLE'}, update=updateNode)
    
    step_ = FloatProperty(
        name='Step', description='Step length',
        default=1.0, options={'ANIMATABLE'},
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'int_'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step_'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.operator("node.svrx_dispatch_function_test", text="Adjust max").fn_name = 'SWITCH'        

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        if not 'Edges' in outputs:
            return

        integer = inputs["Nº Vertices"].sv_get()
        step = inputs["Step"].sv_get()

        params = match_long_repeat([integer, step])
        out = [a for a in (zip(*[make_line(i, s) for i, s in zip(*params)]))]
            
        # outputs
        if outputs['Vertices'].is_linked:
            outputs['Vertices'].sv_set(out[0])

        if outputs['Edges'].is_linked:
            outputs['Edges'].sv_set(out[1])

    def switch_property(self):
        
        stored_value = copy.copy(int(self.int_))

        self.int_ = IntProperty(
            name='N Verts', description='Nº Vertices',
            default=2, min=4, max=40,
            options={'ANIMATABLE'}, update=updateNode)

        self.int_ = stored_value        





def register():
    bpy.utils.register_class(LineNodeRx)
    bpy.utils.register_class(SvRxDispatchFunctionTest)


def unregister():
    bpy.utils.unregister_class(SvRxDispatchFunctionTest)
    bpy.utils.unregister_class(LineNodeRx)

