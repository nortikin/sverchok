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
from bpy.props import EnumProperty, BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvEdgesAngleForce, SvPolygonsAngleForce

class SvPulgaAngleForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Angles at edges
    Tooltip: Force the keeps angles between edges
    """
    bl_idname = 'SvPulgaAngleForceNode'
    bl_label = 'Pulga Angle Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_ANGLES_FORCE'

    fixed_angle: FloatProperty(
        name='Rest Angle', description='Specify spring rest angle, 0 to calculate it from initial position',
        default=0.0, update=updateNode)
    stiffness: FloatProperty(
        name='Stiffness', description='Springs stiffness constant',
        default=0.1, precision=4,
        update=updateNode)
    def update_sockets(self, context):
        self.inputs[0].label = self.mode
    mode: EnumProperty(
        name='Mode',
        items=enum_item_4(['Edges', 'Polygons']),
        default='Edges',
        update=update_sockets
    )

    mass_dependent: BoolProperty(name='mass_dependent', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Edge_Pol")
        self.inputs[0].label = 'Edges'
        self.inputs.new('SvStringsSocket', "Stiffness").prop_name = 'stiffness'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'fixed_angle'


        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')
    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        springs_in = self.inputs["Edge_Pol"].sv_get(deepcopy=False)
        stiffness_in = self.inputs["Stiffness"].sv_get(deepcopy=False)
        lengths_in = self.inputs["Angle"].sv_get(deepcopy=False)

        forces_out = []
        use_fix_len = self.inputs["Angle"].is_linked
        for force_params in zip_long_repeat(springs_in, stiffness_in, lengths_in):
            if self.mode =='Edges':
                forces_out.append(SvEdgesAngleForce(*force_params, use_fix_len))
            else:
                forces_out.append(SvPolygonsAngleForce(*force_params, use_fix_len))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAngleForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAngleForceNode)
