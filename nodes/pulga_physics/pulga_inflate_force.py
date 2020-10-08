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
from sverchok.utils.pulga_physics_modular_core import SvInflateForce

class SvPulgaInflateForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Pump up polygons
    Tooltip: Push vertices along polygons normal
    """
    bl_idname = 'SvPulgaInflateForceNode'
    bl_label = 'Pulga Inflate Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_INFLATE_FORCE'


    force : FloatProperty(
        name='Strength', description='push geometry along the normals proportional to polygon area',
        default=1.0, precision=3, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Polygons")
        self.inputs.new('SvStringsSocket', "Magnitude").prop_name = 'force'


        self.outputs.new('SvPulgaForceSocket', "Force")

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        pols_in = self.inputs["Polygons"].sv_get(deepcopy=False)
        force_in = self.inputs["Magnitude"].sv_get(deepcopy=False)

        forces_out = []

        for force_params in zip_long_repeat(pols_in, force_in):

            forces_out.append(SvInflateForce(*force_params))
        self.outputs[0].sv_set([forces_out])




def register():
    bpy.utils.register_class(SvPulgaInflateForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaInflateForceNode)
