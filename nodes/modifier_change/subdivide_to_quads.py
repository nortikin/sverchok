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

from itertools import product
import numpy as np
import bpy
from bpy.props import IntProperty, BoolVectorProperty, FloatProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.mesh.subdivide import subdiv_mesh_to_quads_np
from sverchok.data_structure import dataCorrect, updateNode
from sverchok.utils.dictionary import SvDict

def check_numpy(new_dict, old_dict):
    for key in old_dict:
        if not isinstance(old_dict[key], np.ndarray):
            new_dict[key] = new_dict[key].tolist()
    return new_dict

class SvSubdivideToQuadsNode(bpy.types.Node, SverchCustomTreeNode, SvRecursiveNode):
    """
    Triggers: Mesh Subdivision Surface
    Tooltip: Subdivide polygon to quads, similar to subdivision surface modifier.
    """
    bl_idname = 'SvSubdivideToQuadsNode'
    bl_label = 'Subdivide to Quads'
    bl_icon = 'MOD_SUBSURF'

    iterations: IntProperty(
        name='Iterations',
        description="Subdivision Iterations",
        default=1, min=1, soft_max=7,
        update=updateNode)
    displace_normal: FloatProperty(
        name='Normal Displace',
        description="Displacement along normal (value per iteration)",
        default=0, update=updateNode)
    random_f: FloatProperty(
        name='Center Random',
        description="Random Displacement on face plane (value per iteration)", default=0, update=updateNode)
    rand_nomal: FloatProperty(
        name='Normal Random', description="Random Displacement along normal (value per iteration)", default=0, update=updateNode)
    random_seed: IntProperty(
        name='Random Seed', description="Random Seed", default=0, update=updateNode)
    smooth_f: FloatProperty(
        name='Smooth', description="Smooth Factor (value per iteration)", default=0, update=updateNode)

    out_np: BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays",
        default=(False, False, False, False),
        size=4, update=updateNode)


    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'list_match')
        layout.label(text="Output Numpy:")
        r = layout.column(align=True)
        for i in range(4):
            r.prop(self, "out_np", index=i, text=self.outputs[i].name, toggle=True)

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "list_match", text="List Match")
        layout.label(text="Output Numpy:")
        for i in range(4):
            layout.prop(self, "out_np", index=i, text=self.outputs[i].name, toggle=True)

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices').is_mandatory = True
        self.sv_new_input('SvStringsSocket', 'Polygons', is_mandatory=True, nesting_level=3)
        self.sv_new_input('SvStringsSocket', 'Iterations',
            prop_name='iterations',
            pre_processing='ONE_ITEM')
        self.sv_new_input('SvStringsSocket', 'Along Normal',
            prop_name='displace_normal')
        self.sv_new_input('SvStringsSocket', 'Random',
            prop_name='random_f')
        self.sv_new_input('SvStringsSocket', 'Random Normal',
            prop_name='rand_nomal')
        self.sv_new_input('SvStringsSocket', 'Random Seed',
            prop_name='random_seed',
            pre_processing='ONE_ITEM')
        self.sv_new_input('SvStringsSocket', 'Smooth',
            prop_name='smooth_f')
        self.sv_new_input('SvDictionarySocket', 'Vert Data Dict', nesting_level=1)
        self.sv_new_input('SvDictionarySocket', 'Face Data Dict', nesting_level=1)

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvStringsSocket', 'Polygons')
        son('SvStringsSocket', 'Vert Map')
        son('SvDictionarySocket', 'Vert Data Dict')
        son('SvDictionarySocket', 'Face Data Dict')


    def process_data(self, params):
        result = [[] for s in self.outputs]
        output_edges = self.outputs['Edges'].is_linked
        ouput_vert_map = self.outputs['Vert Map'].is_linked
        for sub_params in zip(*params):
            output = subdiv_mesh_to_quads_np(*sub_params,
                                             output_edges=output_edges,
                                             output_vert_map=ouput_vert_map)

            if isinstance(sub_params[8], SvDict):
                vert_data = SvDict(check_numpy(output[4], sub_params[8]))
                vert_data.inputs = sub_params[8].inputs.copy()
                result[4].append(vert_data)

            if isinstance(sub_params[9], SvDict):
                face_data = SvDict(output[5])
                face_data.inputs = sub_params[9].inputs.copy()
                result[5].append(face_data)

            for o, s, keep_numpy in zip(output[:4], result, self.out_np):
                s.append(o if keep_numpy else o.tolist())

        return result



def register():
    bpy.utils.register_class(SvSubdivideToQuadsNode)


def unregister():
    bpy.utils.unregister_class(SvSubdivideToQuadsNode)
