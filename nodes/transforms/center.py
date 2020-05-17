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
from bpy.props import EnumProperty, FloatProperty, FloatVectorProperty, BoolProperty
import numpy as np
from numpy import pi
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, numpy_list_match_func, no_space
from sverchok.utils.sv_itertools import recurse_f_level_control

def center(verts):
    '''
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    returns the verts centred arround [0,0,0]
    '''
    verts_out = []
    averages = []
    for vec in verts:

        avr = list(map(sum, zip(*vec)))
        avr = [n/len(vec) for n in avr]
        vec = [[v[0]-avr[0], v[1]-avr[1], v[2]-avr[2]] for v in vec]
        averages.append(avr)
        verts_out.append(vec)

    return verts_out, averages

def center_np(verts, output_numpy):
    '''
    verts: list as [vertex, vertex, ...], being each vertex [float, float, float].
    returns the verts centred arround [0,0,0]
    '''
    verts_out = []
    averages = []
    for vec in verts:
        vec_np = np.array(vec)
        avr = np.sum(vec_np, axis=0)/len(vec)
        vec_np -= avr[np.newaxis, :]
        averages.append(avr if output_numpy else avr.tolist())
        verts_out.append(vec_np if output_numpy else vec_np.tolist())

    return verts_out, averages

def center_of_many(verts):
    '''
    verts: list as [[vertex, vertex, ...],[vertex,...]], being each vertex [float, float, float].
    returns the verts centred arround [0,0,0] calculating the mean of all lists
    '''

    verts_ungrouped = [v for vec in verts for v in vec]
    average = list(map(sum, zip(*verts_ungrouped)))
    average = [n/len(verts_ungrouped) for n in average]
    vec = [[[v[0]-average[0], v[1]-average[1], v[2]-average[2]] for v in vec] for vec in verts]

    return vec, [average]

def repack_vertices(verts_ungrouped, lens, output_numpy):
    out_verts=[]
    idx = 0
    if output_numpy:
        for g in lens:
            out_verts.append(verts_ungrouped[idx: idx + g, :])
            idx += g
    else:
        for g in lens:
            out_verts.append(verts_ungrouped[idx: idx + g, :].tolist())
            idx += g
    return out_verts

def center_of_many_np(verts, output_numpy):
    '''
    verts: list as [[vertex, vertex, ...],[vertex,...]], being each vertex [float, float, float].
    returns the verts centred arround [0,0,0] calculating the mean of all lists
    '''
    np_verts = np.array(verts)
    lens = list(map(len, verts))
    print("shape", lens)
    verts_ungrouped = np.array([v for vec in verts for v in vec])
    average = np.sum(verts_ungrouped, axis=0)/len(verts_ungrouped)
    verts_ungrouped -= average[np.newaxis, :]
    # verts_ungrouped = np_verts.reshape(-1,3)


    # return [vec if output_numpy else vec.tolist() for vec in np_verts], [average if output_numpy else average.tolist()]
    return repack_vertices(verts_ungrouped, lens, output_numpy), [average if output_numpy else average.tolist()]

def center_of_many_func(params, constant, matching_f):
    implementation, output_numpy = constant
    if implementation == 'NumPy':
        return center_of_many_np(params[0], output_numpy)

    return center_of_many(params[0])

def center_func(params, constant, matching_f):
    implementation, output_numpy = constant
    if implementation == 'NumPy':
        return center_np(params[0], output_numpy)

    return center(params[0])


class SvCenterNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Center geometry
    Tooltip: Move geometry to world origin or calculate mean of geometry

    """

    bl_idname = 'SvCenterNode'
    bl_label = 'Center'
    bl_icon = 'PIVOT_BOUNDBOX'

    implementation_modes = [
        ("NumPy", "NumPy", "NumPy", 0),
        ("Python", "Python", "Python", 1)]

    implementation: EnumProperty(
        name='Implementation', items=implementation_modes,
        description='Choose calculation method (See Documentation)',
        default="NumPy", update=updateNode)

    output_numpy: BoolProperty(
        name='Output NumPy',
        description='Output NumPy arrays',
        default=False, update=updateNode)

    center_of_group: BoolProperty(
        name='Center of many',
        description='Center of group of objects',
        default=False, update=updateNode)

    def sv_init(self, context):

        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvVerticesSocket', 'Center')


    def draw_buttons(self, context, layout):
        layout.prop(self, 'center_of_group', expand=False, text='Center of many')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'center_of_group', expand=False, text='Center of many')
        layout.prop(self, "implementation", expand=True)
        if self.implementation == 'NumPy':
            layout.prop(self, "output_numpy", expand=True)

    def rclick_menu(self, context, layout):
        layout.prop(self, 'center_of_group', expand=False, text='Center of many')
        layout.prop_menu_enum(self, "implementation", text="Implementation")
        if self.implementation == 'NumPy':
            layout.prop(self, "output_numpy", expand=True)

    def process(self):
        inputs, outputs = self.inputs, self.outputs

        if not outputs[0].is_linked:
            return

        result = []

        params = inputs[0].sv_get(default=[[]], deepcopy=False)
        ops = [self.implementation, self.output_numpy]
        if self.center_of_group:
            result = recurse_f_level_control([params], ops, center_of_many_func, list_match_func["REPEAT"], [4])
        else:
            result = recurse_f_level_control([params], ops, center_func, list_match_func["REPEAT"], [3])


        self.outputs[0].sv_set(result[0])
        self.outputs[1].sv_set(result[1])

classes = [SvCenterNode]
register, unregister = bpy.utils.register_classes_factory(classes)
