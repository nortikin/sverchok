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
from bpy.props import EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import SvAlignForce
from sverchok.dependencies import scipy, Cython

class SvPulgaAlignForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Velocity Alignation
    Tooltip: Take part of the velocity of the near particles
    """
    bl_idname = 'SvPulgaAlignForceNode'
    bl_label = 'Pulga Align Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_ALIGN_FORCE'


    strength: FloatProperty(
        name='Strength', description='Drag Force Constant',
        default=0.1, precision=3, update=updateNode)
    decay: FloatProperty(
        name='Decay', description='0 = no decay, 1 = linear, 2 = quadratic...',
        default=1.0, precision=3, update=updateNode)
    max_distance: FloatProperty(
        name='Max. Distance', description='Maximun distance',
        default=10.0, precision=3, update=updateNode)
    mode: EnumProperty(
        name='Mode',
        description='Algorithm used for calculation',
        items=enum_item_4(['Brute Force', 'Kd-tree']),
        default='Kd-tree', update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Strength").prop_name = 'strength'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay'
        self.inputs.new('SvStringsSocket', "Max. Distance").prop_name = 'max_distance'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        if scipy is not None and Cython is not None:
            layout.prop(self, 'mode')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        strength = self.inputs["Strength"].sv_get(deepcopy=False)
        decay = self.inputs["Decay"].sv_get(deepcopy=False)
        max_distance = self.inputs["Max. Distance"].sv_get(deepcopy=False)
        use_kdtree = self.mode in "Kd-tree" and scipy is not None and Cython is not None

        forces_out = []

        for force in zip_long_repeat(strength, decay, max_distance):

            forces_out.append(SvAlignForce(*force, use_kdtree=use_kdtree))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAlignForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAlignForceNode)
