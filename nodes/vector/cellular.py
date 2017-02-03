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
from bpy.props import EnumProperty
from mathutils import noise

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, Vector_degenerate )

# noise nodes
# from http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html


cellular_f = {'SCALAR': noise.cell, 'VECTOR': noise.cell_vector}

class SvCellularNode(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Cellular node'''
    bl_idname = 'SvCellularNode'
    bl_label = 'Vector Cellular'
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
    
    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('VerticesSocket', 'Noise V')
        
    def draw_buttons(self, context, layout):
        layout.prop(self, 'out_mode', expand=True)

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        out = []
        verts = inputs['Vertices'].sv_get()

        cellular_function = cellular_f[self.out_mode]


        if verts and verts[0]:
            for vertices in verts:
                out.append([cellular_function(v) for v in vertices])
        
        if 'Noise V' in outputs:
            out = Vector_degenerate(out)
        outputs[0].sv_set(out)



def register():
    bpy.utils.register_class(SvCellularNode)


def unregister():
    bpy.utils.unregister_class(SvCellularNode)
