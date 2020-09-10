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
from bpy.props import BoolProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, zip_long_repeat
from sverchok.utils.pulga_physics_core_2 import SvAttractorsForce

class SvPulgaAttractorsForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Define Boundaries
    Tooltip: System Limits
    """
    bl_idname = 'SvPulgaAttractorsForceNode'
    bl_label = 'Pulga Attractors Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_CIRCLE_SVG'

    force : FloatProperty(
        name='Strength', description='Attractors Force magnitude',
        default=0.0, precision=3, update=updateNode)
    clamp : FloatProperty(
        name='Clamp', description='Attractors maximum influence distance',
        default=0.0, precision=3, update=updateNode)
    decay_power : FloatProperty(
        name='Decay', description='Decay with distance 0 = no decay, 1 = linear, 2 = quadratic...',
        default=0.0, precision=3, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvStringsSocket', "Force").prop_name = 'force'
        self.inputs.new('SvStringsSocket', "Clamp").prop_name = 'clamp'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay_power'


        self.outputs.new('SvPulgaForceSocket', "Force")



    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        loc = self.inputs["Location"].sv_get(deepcopy=False)
        force = self.inputs["Force"].sv_get(deepcopy=False)
        clamp = self.inputs["Clamp"].sv_get(deepcopy=False)
        decay_power = self.inputs["Decay"].sv_get(deepcopy=False)


        forces_out = []

        forces_out = []
        for force in zip_long_repeat(loc, force, clamp, decay_power):

            forces_out.append(SvAttractorsForce(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAttractorsForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAttractorsForceNode)
