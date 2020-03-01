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

from mathutils import Vector

import bpy
from bpy.props import FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_recursive import sv_recursive_transformations


class SvScaleNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Scale MK2 '''
    bl_idname = 'SvScaleNodeMK2'
    bl_label = 'Scale'
    bl_icon = 'NONE' #'MAN_SCALE'
    sv_icon = 'SV_SCALE'
    replacement_nodes = [('SvScaleNodeMk3', dict(vertices='Vertices', centers='Centers', multiplier='Strength'), dict(vertices='Vertices'))]
    factor_: FloatProperty(
        name='multiplyer', description='scaling factor', default=1.0, update=updateNode)

    separate: BoolProperty(
        name='separate', description='Separate UV coords', default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "vertices")
        self.inputs.new('SvVerticesSocket', "centers")
        self.inputs.new('SvStringsSocket', "multiplier").prop_name = "factor_"
        self.outputs.new('SvVerticesSocket', "vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'separate')

    def process(self):
        # inputs
        vers = self.inputs['vertices'].sv_get()
        vecs = self.inputs['centers'].sv_get(default=[[[0.0, 0.0, 0.0]]])
        mult = self.inputs['multiplier'].sv_get()

        # outputs
        if self.outputs[0].is_linked:
            sca = sv_recursive_transformations(self.scaling, vers, vecs, mult, self.separate)
            self.outputs['vertices'].sv_set(sca)

    def scaling(self, v, c, multiplier):
        # print(c,v,m)
        return [(Vector(c) + multiplier * (Vector(v) - Vector(c)))[:]]


def register():
    bpy.utils.register_class(SvScaleNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvScaleNodeMK2)
