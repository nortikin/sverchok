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
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4
from sverchok.utils.pulga_physics_core_2 import SvCollisionForce
from sverchok.dependencies import scipy, Cython
class SvPulgaSelfCollisionForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Collide verts
    Tooltip: Collision forces between vertices
    """
    bl_idname = 'SvPulgaSelfCollisionForceNode'
    bl_label = 'Pulga Collision Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_COLLISION_FORCE'

    force: FloatProperty(
        name='Strength', description='Collision forces between vertices',
        default=0.0, precision=4, step=1e-2, update=updateNode)
    mode: EnumProperty(
        name='Mode',
        description='Algorithm used for calculation',
        items=enum_item_4(['Brute Force', 'Kd-tree']),
        default='Kd-tree', update=updateNode)


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'force'

        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        if scipy is not None and Cython is not None:
            layout.prop(self, 'mode')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        forces_in = self.inputs["Magnitude"].sv_get(deepcopy=False)

        forces_out = []
        use_kdtree = self.mode in "Kd-tree" and scipy is not None and Cython is not None
        for force in forces_in:
            forces_out.append(SvCollisionForce(force, use_kdtree=use_kdtree))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaSelfCollisionForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaSelfCollisionForceNode)
