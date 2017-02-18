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
from bpy.props import EnumProperty, IntProperty
from mathutils import noise

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_degenerate )

# noise nodes
# from http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html


cell_f = {'SCALAR': noise.cell, 'VECTOR': noise.cell_vector}

class SvCellNode(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Cell node'''
    bl_idname = 'SvCellNode'
    bl_label = 'Vector Cell'
    bl_icon = 'FORCE_TURBULENCE'

    def changeMode(self, context):
        outputs = self.outputs
        if self.out_mode == 'SCALAR':
            if 'Noise S' not in outputs:
                outputs[0].replace_socket('StringsSocket', 'Noise S')
                return
        if self.out_mode == 'VECTOR':
            if 'Noise V' not in outputs:
                outputs[0].replace_socket('VerticesSocket', 'Noise V')
                return

    out_modes = [
        ('SCALAR', 'Scalar', 'Scalar output', '', 1),
        ('VECTOR', 'Vector', 'Vector output', '', 2)]

    out_mode = EnumProperty(
        items=out_modes,
        default='VECTOR',
        description='Output type',
        update=changeMode)

    rseed = IntProperty(default=0, description="Random seed",name="Random seed", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Random seed').prop_name = 'rseed'
        self.outputs.new('VerticesSocket', 'Noise V')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        out = []
        verts = inputs['Vertices'].sv_get()
        rseed = inputs['Random seed'].sv_get()[0][0]

        cell_function = cell_f[self.out_mode]

        coords = []

        if verts and verts[0]:
            for vertex in verts[0]:
                # set the offset origin for random seed
                if rseed == 0:
                    #we set offset value to 0.0
                    offset = [0.0,0.0,0.0]
                else:
                    # randomise origin
                    noise.seed_set( rseed )
                    offset = noise.random_unit_vector() * 10

                new_vertex = [ x+y for x, y in zip(vertex, offset)]
                coords.append(new_vertex)
            out.append([cell_function(v)  for v in coords])

        if 'Noise V' in outputs:
            out = Vector_degenerate(out)
        outputs[0].sv_set(out)



def register():
    bpy.utils.register_class(SvCellNode)


def unregister():
    bpy.utils.unregister_class(SvCellNode)
