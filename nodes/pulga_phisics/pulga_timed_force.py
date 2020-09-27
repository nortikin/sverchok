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
from sverchok.data_structure import match_long_repeat as mlr, zip_long_repeat
from sverchok.utils.pulga_physics_core_2 import SvTimedForce

class SvPulgaTimedForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse SVG
    Tooltip: Svg circle/ellipse shape, the shapes will be wrapped in SVG Groups
    """
    bl_idname = 'SvPulgaTimedForceNode'
    bl_label = 'Pulga Timed Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_TIMED_FORCE'

    start: IntProperty(name='Start', description='Force', default=0, update=updateNode)
    end: IntProperty(name='End', description='Force', default=0, update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvPulgaForceSocket', "Force")
        self.inputs.new('SvStringsSocket', "Start").prop_name = 'start'
        self.inputs.new('SvStringsSocket', "End").prop_name = 'end'

        self.outputs.new('SvPulgaForceSocket', "Force")


    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        forces_in = self.inputs["Force"].sv_get(deepcopy=False)
        start_in = self.inputs["Start"].sv_get(deepcopy=False)
        end_in = self.inputs["End"].sv_get(deepcopy=False)
        forces_out = []
        for forces in zip_long_repeat(forces_in, start_in, end_in):
            f_s = []
            for force in zip_long_repeat(*forces):
                f_s.append(SvTimedForce(*force))
            forces_out.append(f_s)
        self.outputs[0].sv_set(forces_out)




def register():
    bpy.utils.register_class(SvPulgaTimedForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaTimedForceNode)
