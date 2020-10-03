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
from sverchok.data_structure import (zip_long_repeat, updateNode)
from sverchok.utils.pulga_physics_core_2 import SvWorldForce, SvFieldForce
from sverchok.utils.field.vector import SvVectorField

class SvPulgaVectorForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Directional Force
    Tooltip: Applies Force defined as a Vector or a Vector Field
    """
    bl_idname = 'SvPulgaVectorForceNode'
    bl_label = 'Pulga Vector Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_VECTOR_FORCE'

    force: FloatVectorProperty(
        name='Force',
        description='Force direction, if will also accept a Vector Field',
        size=3,
        default=(0, 0, 1),
        update=updateNode)
    magnitude: FloatProperty(
        name='Strength',
        description='Force multiplayer',
        default=1,
        update=updateNode)
    mass_proportional: BoolProperty(
        name='Proportional to Mass',
        description='Multiply Force with mass (like Gravity force)',
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Force").prop_name = 'force'
        self.inputs.new('SvStringsSocket', "Strength").prop_name = 'magnitude'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        layout.prop(self, "mass_proportional")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return

        forces_in = self.inputs["Force"].sv_get(deepcopy=False)
        strength_in = self.inputs["Strength"].sv_get(deepcopy=False)

        if isinstance(forces_in[0], SvVectorField):
            force_class = SvFieldForce
        else:
            force_class = SvWorldForce
        forces_out = []

        for force, strength in zip_long_repeat(forces_in, strength_in):
            forces_out.append(force_class(force, strength, self.mass_proportional))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaVectorForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaVectorForceNode)
