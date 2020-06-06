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
from mathutils.noise import seed_set, random
import bpy
from bpy.props import FloatVectorProperty, IntProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode


class SvVectorGenesNode(bpy.types.Node, SverchCustomTreeNode):
    '''Bounding box'''
    bl_idname = 'SvVectorGenesNode'
    bl_label = 'Vector Genes'
    bl_icon = 'NONE'
    sv_icon = 'SV_BOUNDING_BOX'
    def update_sockets(self, context):
        bools = [self.min_list, self.max_list, self.size_list]
        dims = int(self.dimensions[0])
        for i in range(3):
            for j in range(3):
                out_index = 4 + j + 3*i
                hidden = self.outputs[out_index].hide_safe
                if bools[i][j] and j < dims:
                    if hidden:
                        self.outputs[out_index].hide_safe = False
                else:
                    self.outputs[out_index].hide_safe = True

            updateNode(self, context)
    def update_dict(self, context):
        self.fill_vect_mem()
        updateNode(self, context)
    r_seed: IntProperty(
        name='Count', description="Show Minimum values sockets", default=3, update=update_dict)
    vector_count: IntProperty(
        name='Count', description="Show Minimum values sockets", default=3, update=update_dict)
    min_list: FloatVectorProperty(
        name='Max', description="Show Maximun values sockets", size=3, update=updateNode)
    max_list: FloatVectorProperty(
        name='Max', description="Show Maximun values sockets", size=3, update=updateNode)

    implentation_modes = [
        ("2D", "2D", "Outputs Rectangle over XY plane", 0),
        ("3D", "3D", "Outputs standard bounding box", 1)]

    node_mem = {}


    def draw_buttons(self, context, layout):

        col = layout.column(align=True)
        col.prop(self, "vector_count")
        titles = ["Min", "Max", "Size"]
        prop = ['min_list', 'max_list']

        for i in range(2):
            row = col.row(align=True)
            row.label(text=titles[i])
            row2 = row.row(align=True)
            for j in range(3):
                row2 .prop(self, prop[i], index=j, text='XYZ'[j])

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices')

        son('SvVerticesSocket', 'Vertices')

    def fill_empty_dict(self):
        vects = []

        for i in range(self.vector_count):
            v = []
            for j in range(3):
                v_range=self.max_list[j] -self.min_list[j]
                v.append(self.min_list[j]+ random()*v_range)
            vects.append(v)
        self.node_mem[self.node_id] = vects

    def fill_vect_mem(self):
        # seed_set(self.r_seed)
        if self.node_id in self.node_mem:
            vects = self.node_mem[self.node_id]
        else:
            vects = []
        if len(vects) < self.vector_count:
            for i in range(self.vector_count -len(vects)):
                v = []
                for j in range(3):
                    v_range = self.max_list[j] - self.min_list[j]
                    v.append(self.min_list[j] + random()*v_range)
                vects.append(v)
        elif len(vects) > self.vector_count:
            vects = vects[:self.vector_count]
        self.node_mem[self.node_id] = vects
    def process(self):
        # if not self.inputs['Vertices'].is_linked:
            # return
        if self.node_id in self.node_mem:
            verts_out = self.node_mem[self.node_id]
        else:
            self.fill_empty_dict()
            verts_out = self.node_mem[self.node_id]

        self.outputs['Vertices'].sv_set([verts_out])




def register():
    bpy.utils.register_class(SvVectorGenesNode)


def unregister():
    bpy.utils.unregister_class(SvVectorGenesNode)
