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

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, fullList, match_long_repeat

from mathutils import Vector


def make_line(integer, step, orientation):

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

class SvLineNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Line hyper'''
    bl_idname = 'SvLineNodeMK2'
    bl_label = 'Line'
    bl_icon = 'GRIP'
    
    int_ = IntProperty(
        name='N Verts', description='Nº Vertices',
        default=2, min=2,
        options={'ANIMATABLE'}, update=updateNode)

    step_ = FloatProperty(
        name='Step', description='Step length',
        default=1.0, options={'ANIMATABLE'},
        update=updateNode)

    orientation_ = IntProperty(min=0, max=2)  # x , y , z   (we make it a socket)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices").prop_name = 'int_'
        self.inputs.new('StringsSocket', "Step").prop_name = 'step_'
        self.inputs.new('StringsSocket', "Orientation").prop_name = 'orientation_'

        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        pass

    def process(self):
        inputs = [s.sv_get() for s in self.inputs]

        params = match_long_repeat(inputs)
        outputs = zip(*[make_line(i, s) for i, s in zip(*params)])

        _ = [socket.sv_set(d) for socket, d in zip(self.outputs, outputs)]



def register():
    bpy.utils.register_class(SvLineNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK2)
