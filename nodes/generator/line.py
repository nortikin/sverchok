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
from bpy.props import IntProperty, FloatProperty

from sv_node_tree import SverchCustomTreeNode
from sv_data_structure import updateNode, fullList, match_long_repeat

from mathutils import Vector


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

class LineNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Line '''
    bl_idname = 'LineNode'
    bl_label = 'Line'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = IntProperty(name='N Verts', description='Nº Vertices',
                       default=2, min=2,
                       options={'ANIMATABLE'}, update=updateNode)
    step_ = FloatProperty(name='Step', description='Step length',
                          default=1.0, options={'ANIMATABLE'},
                          update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'int_'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step_'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        pass

    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        if not 'Edges' in outputs:
            return

        integer = inputs["Nº Vertices"].sv_get()
        step = inputs["Step"].sv_get()

        params = match_long_repeat([integer, step])
        out = [a for a in (zip(*[make_line(i, s) for i, s in zip(*params)]))]
            
        # outputs
        if outputs['Vertices'].links:
            outputs['Vertices'].sv_set(out[0])

        if outputs['Edges'].links:
            outputs['Edges'].sv_set(out[1])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(LineNode)


def unregister():
    bpy.utils.unregister_class(LineNode)