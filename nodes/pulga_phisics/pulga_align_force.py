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
from bpy.props import EnumProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4
from sverchok.dependencies import scipy
from sverchok.utils.pulga_physics_core_2 import SvAlignForce

class SvPulgaAlignForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Velocity Alignation
    Tooltip: Take part of the velocity of the near particles
    """
    bl_idname = 'SvPulgaAlignForceNode'
    bl_label = 'Pulga Align Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_CIRCLE_SVG'


    magnitude: FloatProperty(
        name='Magnitude', description='Drag Force Constant',
        default=0.0, precision=3, update=updateNode)
    radius: FloatProperty(
        name='Radius', description='Drag Force Constant',
        default=0.0, precision=3, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'magnitude'
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'


        self.outputs.new('SvPulgaForceSocket', "Force")


    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        magnitude = self.inputs["Magnitude"].sv_get(deepcopy=False)
        radius = self.inputs["Radius"].sv_get(deepcopy=False)


        forces_out = []

        forces_out = []

        for force in zip(magnitude, radius):

            forces_out.append(SvAlignForce(*force))


        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaAlignForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaAlignForceNode)
