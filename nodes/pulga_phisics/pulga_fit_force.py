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
from bpy.props import BoolProperty, IntProperty, FloatProperty, FloatVectorProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4
from sverchok.utils.pulga_physics_core_2 import SvFitForce

class SvPulgaFitForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Grow / Shrink
    Tooltip: Shrink if collide with others / Grow if does not
    """
    bl_idname = 'SvPulgaFitForceNode'
    bl_label = 'Pulga Fit Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_CIRCLE_SVG'

    force : FloatProperty(
        name='Magnitude', description='Shrink if collide with others / Grow if does not ',
        default=0.0, update=updateNode)
    min_rad : FloatProperty(
        name='Min. Radius', description='Do not shrink under this value',
        default=0.1, precision=3, update=updateNode)
    max_rad : FloatProperty(
        name='Max. Radius', description='Do not grow over this value',
        default=1.0, precision=3, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'force'
        self.inputs.new('SvStringsSocket', "Min Radius").prop_name = 'min_rad'
        self.inputs.new('SvStringsSocket', "Max Radius").prop_name = 'max_rad'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        forces_in = self.inputs["Magnitude"].sv_get(deepcopy=False)
        min_rad_in = self.inputs["Min Radius"].sv_get(deepcopy=False)
        max_rad_in = self.inputs["Max Radius"].sv_get(deepcopy=False)
        forces_out = []

        for force in zip(forces_in, min_rad_in, max_rad_in):
            forces_out.append(SvFitForce(*force))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaFitForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaFitForceNode)
