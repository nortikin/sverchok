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
from sverchok.utils.pulga_physics_core_2 import SvPinForce

class SvPulgaPinForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvPulgaPinForceNode'
    bl_label = 'Pulga Pin Force'
    bl_icon = 'PINNED'


    fixed_len: FloatProperty(name='Length', description='Force', default=0.0, update=updateNode)
    pin_type: EnumProperty(name='Axis', description='Constrained', items=enum_item_4(['XYZ', 'XY','XZ', 'YZ', 'X','Y', 'Z']), default='XYZ', update=updateNode)
    force: FloatVectorProperty(name='Force', description='Force', size=3, default=(0.0,0,0), update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Pins")
        self.inputs.new('SvStringsSocket', "Pin Type").prop_name = 'pin_type'
        self.inputs.new('SvVerticesSocket', "Pins Goal")

        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        # indices, pin_type, pins_goal_pos,use_pins_goal
        pins_in = self.inputs["Pins"].sv_get(deepcopy=False)
        pin_type = self.inputs["Pin Type"].sv_get(deepcopy=False)
        pins_goal_pos = self.inputs["Pins Goal"].sv_get(deepcopy=False, default=[[]])
        forces_out = []
        use_pin_goal = self.inputs["Pins Goal"].is_linked
        for force_params in zip(*mlr([pins_in, pin_type, pins_goal_pos])):

            forces_out.append(SvPinForce(*force_params, use_pin_goal))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaPinForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaPinForceNode)
