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
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvAttractorsForce, SvAttractorsLineForce, SvAttractorsPlaneForce

class SvPulgaAttractorsForceNodeMk2(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Attraction Points
    Tooltip: Attractor/Repeller points with distance limit
    """
    bl_idname = 'SvPulgaAttractorsForceNodeMk2'
    bl_label = 'Pulga Attractors Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_ATTRACTORS_FORCE'

    strength: FloatProperty(
        name='Strength', description='Attractors Force magnitude',
        default=1.0, precision=3, update=updateNode)
    max_distance: FloatProperty(
        name='Max Distance', description='Attractors maximum influence distance',
        default=10.0, precision=3, update=updateNode)
    decay_power: FloatProperty(
        name='Decay', description='Decay with distance 0 = no decay, 1 = linear, 2 = cubic...',
        default=0.0, precision=3, update=updateNode)

    def update_sockets(self, context):
        self.inputs['Direction'].hide_safe = self.mode not in ['Line', 'Plane']
        if self.mode == 'Line':
            self.inputs['Direction'].label = 'Direction'
        else:
            self.inputs['Direction'].label = 'Normal'
        updateNode(self, context)
    mode: EnumProperty(
        name='Mode',
        items=enum_item_4(['Point', 'Line', 'Plane']),
        default='Point',
        update=update_sockets
    )


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Location")
        self.inputs.new('SvVerticesSocket', "Direction")
        self.inputs["Direction"].hide_safe = True
        self.inputs.new('SvStringsSocket', "Strength").prop_name = 'strength'
        self.inputs.new('SvStringsSocket', "Max. Distance").prop_name = 'max_distance'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay_power'


        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        loc = self.inputs["Location"].sv_get(deepcopy=False)
        strength = self.inputs["Strength"].sv_get(deepcopy=False)
        max_distance = self.inputs["Max. Distance"].sv_get(deepcopy=False)
        decay_power = self.inputs["Decay"].sv_get(deepcopy=False)


        forces_out = []

        forces_out = []
        if self.mode == 'Point':
            for force in zip_long_repeat(loc, strength, max_distance, decay_power):

                forces_out.append(SvAttractorsForce(*force))
        else:
            direction = self.inputs["Direction"].sv_get(deepcopy=False)
            force_class = SvAttractorsLineForce if self.mode == 'Line' else SvAttractorsPlaneForce
            for force in zip_long_repeat(loc, direction, strength, max_distance, decay_power):

                forces_out.append(force_class(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAttractorsForceNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvPulgaAttractorsForceNodeMk2)
