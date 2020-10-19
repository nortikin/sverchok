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
from bpy.props import FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvObstaclesBVHForce

class SvPulgaObstacleForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Colliding Obstacles
    Tooltip: Objects that collide with particles
    """
    bl_idname = 'SvPulgaObstacleForceNode'
    bl_label = 'Pulga Obstacles Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_OBSTACLES_FORCE'

    magnitude: FloatProperty(
        name='Magnitude', description='Drag Force Constant',
        default=0.0, precision=3, update=updateNode)

    absorption: FloatProperty(
        name='Absorption', description='Obstacles Velocity and acceleration absortion. 0 = hard surface, 1 = soft surface',
        default=0.1, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Pols")
        self.inputs.new('SvStringsSocket', "Absorption").prop_name = 'absorption'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        magnitude = self.inputs["Vertices"].sv_get(deepcopy=False)
        pols = self.inputs["Pols"].sv_get(deepcopy=False)
        absorption = self.inputs["Absorption"].sv_get(deepcopy=False)

        forces_out = []

        forces_out = []
        for force in zip_long_repeat(magnitude, pols, absorption):
            forces_out.append(SvObstaclesBVHForce(*force))



        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaObstacleForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaObstacleForceNode)
