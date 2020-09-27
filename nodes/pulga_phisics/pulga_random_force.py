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
from sverchok.data_structure import match_long_repeat as mlr
from sverchok.utils.pulga_physics_core_2 import SvRandomForce

class SvPulgaRandomForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvPulgaRandomForceNode'
    bl_label = 'Pulga Random Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_RANDOM_FORCE'

    random_seed : IntProperty(
        name='Seed', description='Random seed number',
        default=0, min=0, update=updateNode)
    force : FloatProperty(
        name='Strength Force', description='Random force magnitude',
        default=0.0, precision=3, step=1e-1, update=updateNode)
    random_variation : FloatProperty(
        name='Variation', description='Random force variation',
        default=0.0, min=0, max=1, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'force'
        self.inputs.new('SvStringsSocket', "Variation").prop_name = 'random_variation'
        self.inputs.new('SvStringsSocket', "Seed").prop_name = 'random_seed'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        forces_in = self.inputs["Magnitude"].sv_get(deepcopy=False)
        random_variation = self.inputs["Variation"].sv_get(deepcopy=False)
        random_seed = self.inputs["Seed"].sv_get(deepcopy=False)
        forces_out = []
        for force in zip(forces_in, random_variation, random_seed):
            forces_out.append(SvRandomForce(*force))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaRandomForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaRandomForceNode)
