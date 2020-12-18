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
from bpy.props import BoolProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvAttractorsForce

class SvPulgaAttractorsForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Attraction Points
    Tooltip: Attractor/Repeller points with distance limit
    """
    bl_idname = 'SvPulgaAttractorsForceNode'
    bl_label = 'Pulga Attractors Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_ATTRACTORS_FORCE'

    replacement_nodes = [('SvPulgaAttractorsForceNodeMk2', None, None)]
    
    strength: FloatProperty(
        name='Strength', description='Attractors Force magnitude',
        default=1.0, precision=3, update=updateNode)
    max_distance: FloatProperty(
        name='Max Distance', description='Attractors maximum influence distance',
        default=10.0, precision=3, update=updateNode)
    decay_power: FloatProperty(
        name='Decay', description='Decay with distance 0 = no decay, 1 = linear, 2 = cubic...',
        default=0.0, precision=3, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvStringsSocket', "Strength").prop_name = 'strength'
        self.inputs.new('SvStringsSocket', "Max. Distance").prop_name = 'max_distance'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay_power'


        self.outputs.new('SvPulgaForceSocket', "Force")



    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        loc = self.inputs["Location"].sv_get(deepcopy=False)
        strength = self.inputs["Strength"].sv_get(deepcopy=False)
        max_distance = self.inputs["Max. Distance"].sv_get(deepcopy=False)
        decay_power = self.inputs["Decay"].sv_get(deepcopy=False)


        forces_out = []

        forces_out = []
        for force in zip_long_repeat(loc, strength, max_distance, decay_power):

            forces_out.append(SvAttractorsForce(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAttractorsForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAttractorsForceNode)
