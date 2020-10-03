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
from bpy.props import BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_core_2 import SvEdgesAngleForce

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

    mass_dependent: BoolProperty(name='mass_dependent', update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Springs")
        self.inputs.new('SvStringsSocket', "Stiffness").prop_name = 'stiffness'
        self.inputs.new('SvStringsSocket', "Angle").prop_name = 'fixed_angle'


        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        springs_in = self.inputs["Springs"].sv_get(deepcopy=False)
        stiffness_in = self.inputs["Stiffness"].sv_get(deepcopy=False)
        lengths_in = self.inputs["Angle"].sv_get(deepcopy=False)

        forces_out = []
        use_fix_len = self.inputs["Angle"].is_linked
        for force_params in zip_long_repeat(springs_in, stiffness_in, lengths_in):

            forces_out.append(SvEdgesAngleForce(*force_params, use_fix_len))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAngleForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAngleForceNode)
