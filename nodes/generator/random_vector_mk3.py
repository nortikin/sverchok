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

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat


class RandomVectorNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: rv Random unit Vec
    Tooltip: Generate Random Vectors of defined magnitude.
    """
    bl_idname = 'RandomVectorNodeMK3'
    bl_label = 'Random Vector'
    bl_icon = 'RNDCURVE'

    count_inner: IntProperty(
        name='Count', description='random', default=1, min=1,
        options={'ANIMATABLE'}, update=updateNode)

    scale: FloatProperty(
        name='Scale', description='scale for vectors', default=1.0,
        options={'ANIMATABLE'}, update=updateNode)

    seed: IntProperty(
        name='Seed', description='random seed', default=1,
        options={'ANIMATABLE'}, update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'count_inner'
        self.inputs.new('SvStringsSocket', "Seed").prop_name = 'seed'
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.outputs.new('SvVerticesSocket', "Random")

    def rclick_menu(self, context, layout):
        layout.prop(self, "output_numpy", toggle=True)

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'output_numpy')

    def process(self):

        count_socket = self.inputs['Count']
        seed_socket = self.inputs['Seed']
        scale_socket = self.inputs['Scale']
        random_socket = self.outputs['Random']
        if not random_socket.is_linked:
            return
        # inputs
        count = count_socket.sv_get(deepcopy=False)[0]
        seed = seed_socket.sv_get(deepcopy=False)[0]
        scale = scale_socket.sv_get(deepcopy=False, default=[])[0]

        # outputs

        random_out = []
        params = match_long_repeat([count, seed, scale])

        for c, s, sc in zip(*params):
            int_seed = int(round(s))

            np.random.seed(int_seed)
            rand_v = np.random.uniform(low=-1, high=1, size=[int(max(1, c)), 3])
            rand_v_mag = np.linalg.norm(rand_v, axis=1)
            if self.output_numpy:
                random_out.append(sc * rand_v/rand_v_mag[:, np.newaxis])
            else:
                random_out.append((sc * rand_v/rand_v_mag[:, np.newaxis]).tolist())

        random_socket.sv_set(random_out)



def register():
    bpy.utils.register_class(RandomVectorNodeMK3)


def unregister():
    bpy.utils.unregister_class(RandomVectorNodeMK2)
