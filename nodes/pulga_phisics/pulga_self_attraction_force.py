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
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import match_long_repeat as mlr, updateNode
from sverchok.utils.pulga_physics_core_2 import SvAttractionForce

class SvPulgaSelfAttractionForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: gravity among vertices
    Tooltip: Attraction between vertices
    """
    bl_idname = 'SvPulgaSelfAttractionForceNode'
    bl_label = 'Pulga Self Attraction Force'
    bl_icon = 'MOD_PHYSICS'
    # sv_icon = 'SV_CIRCLE_SVG'

    force : FloatProperty(
        name='Strength', description='Attraction between vertices',
        default=0.0, precision=4, step=1e-2, update=updateNode)
    decay : FloatProperty(
        name='Decay', description='0 = no decay, 1 = linear, 2 = quadratic...',
        default=0.0, precision=3, update=updateNode)
    max_distance : FloatProperty(
        name='Max Distance', description='Maximun distance',
        default=0.0, precision=3, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'force'
        self.inputs.new('SvStringsSocket', "Decay").prop_name = 'decay'
        self.inputs.new('SvStringsSocket', "Max Distance").prop_name = 'max_distance'


        self.outputs.new('SvPulgaForceSocket', "Force")


    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        forces_in = self.inputs["Magnitude"].sv_get(deepcopy=False)
        decay_in = self.inputs["Decay"].sv_get(deepcopy=False)
        max_distance = self.inputs["Max Distance"].sv_get(deepcopy=False)

        forces_out = []
        for force_params in zip(forces_in, decay_in, max_distance):
            forces_out.append(SvAttractionForce(*force_params))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaSelfAttractionForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaSelfAttractionForceNode)
