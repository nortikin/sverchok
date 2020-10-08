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

from math import sin, cos, pi, degrees, radians
from mathutils import Matrix
import bpy
from bpy.props import FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvDragForce

class SvPulgaDragForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Resistance from environment
    Tooltip: Movement resistance from environment
    """
    bl_idname = 'SvPulgaDragForceNode'
    bl_label = 'Pulga Drag Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_DRAG_FORCE'

    magnitude: FloatProperty(
        name='Magnitude', description='Drag Force Constant',
        default=0.5, precision=3, update=updateNode)

    exponent: FloatProperty(name='Exponent', description='Velocity exponent (2 = accurate)', default=1.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'magnitude'
        self.inputs.new('SvStringsSocket', "Exponent").prop_name = 'exponent'

        self.outputs.new('SvPulgaForceSocket', "Force")



    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        magnitude = self.inputs["Magnitude"].sv_get(deepcopy=False)
        exponent = self.inputs["Exponent"].sv_get(deepcopy=False)

        forces_out = []

        forces_out = []
        for force in zip_long_repeat(magnitude, exponent):

            forces_out.append(SvDragForce(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaDragForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaDragForceNode)
