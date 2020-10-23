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
from bpy.props import EnumProperty, IntProperty, FloatProperty, BoolProperty
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes
from sverchok.utils.sv_itertools import recurse_f_level_control

def random_vector(params, constant, matching_f):
    '''
    params are count, seed and  scale as Level 1 list [float, float, float]
    desired_levels = [1, 1, 1]
    constant are the function options (data that does not need to be matched)
    matching_f stands for list matching formula to use
    '''
    result = []
    output_numpy = constant
    params = matching_f(params)

    for count, seed, scale in zip(*params):
        int_seed = int(round(seed))

        np.random.seed(int_seed)
        rand_v = np.random.uniform(low=-1, high=1, size=[int(max(1, count)), 3])
        rand_v_mag = np.linalg.norm(rand_v, axis=1)
        if output_numpy:
            result.append(scale * rand_v/rand_v_mag[:, np.newaxis])
        else:
            result.append((scale * rand_v/rand_v_mag[:, np.newaxis]).tolist())

    return result

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

    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)

    correct_output_modes = [
        ('NONE', 'None', 'Leave at multi-object level (Advanced)', 0),
        ('FLAT', 'Flat Output', 'Flat to object level', 2),
    ]
    correct_output: EnumProperty(
        name="Simplify Output",
        description="Behavior on different list lengths, object level",
        items=correct_output_modes, default="FLAT",
        update=updateNode)
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
        layout.prop_menu_enum(self, "correct_output")

    def draw_buttons_ext(self, context, layout):
        '''draw buttons on the N-panel'''
        layout.prop(self, 'output_numpy')

    def process(self):

        if not self.outputs['Random'].is_linked:
            return

        params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]

        matching_f = list_match_func[self.list_match]
        desired_levels = [1, 1, 1]
        ops = self.output_numpy
        concatenate = 'APPEND' if self.correct_output == 'NONE' else "EXTEND"

        result = recurse_f_level_control(params, ops, random_vector, matching_f, desired_levels, concatenate=concatenate)

        self.outputs[0].sv_set(result)




def register():
    bpy.utils.register_class(RandomVectorNodeMK3)


def unregister():
    bpy.utils.unregister_class(RandomVectorNodeMK3)
