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
from bpy.props import FloatVectorProperty, BoolProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvVortexForce

class SvPulgaVortexForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Attraction Points
    Tooltip: Attractor/Repeller points with distance limit
    """
    bl_idname = 'SvPulgaVortexForceNode'
    bl_label = 'Pulga Vortex Force'
    bl_icon = 'FORCE_VORTEX'

    loc: FloatVectorProperty(
        name='Location', description='Vortex Location',
        size=3, default=(0, 0, 0), update=updateNode)
    direction: FloatVectorProperty(
        name='Direction', description='Vortex direction',
        size=3, default=(0, 0, 1), update=updateNode)
    rotation_strength: FloatProperty(
        name='Rotation Strength', description='Multiplier of the rotation force',
        default=1.0, precision=3, update=updateNode)
    inflow_strength: FloatProperty(
        name='Inflow Strength', description='Multiplier of the inflow force (towards the line)',
        default=1.0, precision=3, update=updateNode)
    forward_strength: FloatProperty(
        name='Forward Strength', description='Multiplier of the forward force (in the direction of the line)',
        default=1.0, precision=3, update=updateNode)
    max_distance: FloatProperty(
        name='Max Distance', description='Vortex maximum influence distance',
        default=10.0, precision=3, update=updateNode)
    decay_power: FloatProperty(
        name='Decay', description='Decay with distance 0 = no decay, 1 = linear, 2 = cubic...',
        default=0.0, precision=3, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location").prop_name = 'loc'
        self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'direction'
        self.inputs.new('SvStringsSocket', "Rotation Strength").prop_name = 'rotation_strength'
        self.inputs.new('SvStringsSocket', "Inflow Strength").prop_name = 'inflow_strength'
        self.inputs.new('SvStringsSocket', "Forward Strength").prop_name = 'forward_strength'
        self.inputs.new('SvStringsSocket', "Max. Distance").prop_name = 'max_distance'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay_power'


        self.outputs.new('SvPulgaForceSocket', "Force")



    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return

        loc = self.inputs["Location"].sv_get(deepcopy=False)
        direction = self.inputs["Direction"].sv_get(deepcopy=False)
        rotation_strength = self.inputs["Rotation Strength"].sv_get(deepcopy=False)
        inflow_strength = self.inputs["Inflow Strength"].sv_get(deepcopy=False)
        forward_strength = self.inputs["Forward Strength"].sv_get(deepcopy=False)
        max_distance = self.inputs["Max. Distance"].sv_get(deepcopy=False)
        decay_power = self.inputs["Decay"].sv_get(deepcopy=False)


        forces_out = []
        for force in zip_long_repeat(loc, direction, rotation_strength, inflow_strength, forward_strength, max_distance, decay_power):

            forces_out.append(SvVortexForce(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaVortexForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaVortexForceNode)
