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
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_recursive import sv_recursive_transformations


class SvMoveNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Move vectors MK2 '''
    bl_idname = 'SvMoveNodeMK2'
    bl_label = 'Move'
    bl_icon = 'NONE' #'MAN_TRANS'
    sv_icon = 'SV_MOVE'

    mult_: FloatProperty(name='multiplier', default=1.0, update=updateNode)

    separate: BoolProperty(
        name='separate', description='Separate UV coords',
        default=False, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'separate')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "vertices")
        self.inputs.new('SvVerticesSocket', "vectors")
        self.inputs.new('SvStringsSocket', "multiplier").prop_name = 'mult_'
        self.outputs.new('SvVerticesSocket', "vertices")

    def process(self):
        # inputs
        vers = self.inputs['vertices'].sv_get()
        vecs = self.inputs['vectors'].sv_get(default=[[[0.0, 0.0, 0.0]]])
        mult = self.inputs['multiplier'].sv_get()

        if self.outputs[0].is_linked:
            mov = sv_recursive_transformations(self.moving, vers, vecs, mult, self.separate)
            self.outputs['vertices'].sv_set(mov)

    def moving(self, v, c, multiplier):
        return [(Vector(v) + Vector(c) * multiplier)[:]]


def register():
    bpy.utils.register_class(SvMoveNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvMoveNodeMK2)
