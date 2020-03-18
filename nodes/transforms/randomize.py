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

import random

import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

import numpy as np

def randomize(vertices, random_x, random_y, random_z, seed, output_numpy=False):
    np.random.seed(seed)
    np_verts = np.array(vertices)
    random.seed(seed)
    x_r = np.random.uniform(
        low=[-random_x, -random_y, -random_z],
        high=[random_x, random_y, random_z],
        size=np_verts.shape)

    return (np_verts + x_r) if output_numpy else (np_verts + x_r).tolist()

class SvRandomizeVerticesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Random Displacement
    Tooltip: Randomize input vertices locations.

    """

    bl_idname = 'SvRandomizeVerticesNode'
    bl_label = 'Randomize'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_RANDOMIZE_INPUT_VERTICES'

    random_x_: FloatProperty(
        name='X amplitude', description='Amplitude of randomization along X axis',
        default=0.0, min=0.0, update=updateNode)

    random_y_: FloatProperty(
        name='Y amplitude', description='Amplitude of randomization along Y axis',
        default=0.0, min=0.0, update=updateNode)

    random_z_: FloatProperty(
        name='Z amplitude', description='Amplitude of randomization along Z axis',
        default=0.0, min=0.0, update=updateNode)

    random_seed_: IntProperty(
        name='Seed', description='Random seed', default=0, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "RandomX").prop_name = "random_x_"
        self.inputs.new('SvStringsSocket', "RandomY").prop_name = "random_y_"
        self.inputs.new('SvStringsSocket', "RandomZ").prop_name = "random_z_"
        self.inputs.new('SvStringsSocket', "Seed").prop_name = "random_seed_"

        self.outputs.new('SvVerticesSocket', "Vertices")
    def rclick_menu(self, context, layout):
        layout.prop(self, "output_numpy", toggle=True)

    def process(self):
        # inputs
        if not (self.inputs['Vertices'].is_linked and self.outputs['Vertices'].is_linked):
            return

        vertices = self.inputs['Vertices'].sv_get(deepcopy=False)
        random_x = self.inputs['RandomX'].sv_get(deepcopy=False)[0]
        random_y = self.inputs['RandomY'].sv_get(deepcopy=False)[0]
        random_z = self.inputs['RandomZ'].sv_get(deepcopy=False)[0]
        seed = self.inputs['Seed'].sv_get()[0]

        if self.outputs['Vertices'].is_linked:

            parameters = match_long_repeat([vertices, random_x, random_y, random_z, seed])

            result = [randomize(vs, rx, ry, rz, se, output_numpy=self.output_numpy) for vs, rx, ry, rz, se in zip(*parameters)]

            self.outputs['Vertices'].sv_set(result)

def register():
    bpy.utils.register_class(SvRandomizeVerticesNode)


def unregister():
    bpy.utils.unregister_class(SvRandomizeVerticesNode)
