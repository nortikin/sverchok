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

import ast
from itertools import product
from mathutils.noise import seed_set, random
import bpy
from bpy.props import FloatVectorProperty, IntVectorProperty, IntProperty, BoolProperty, StringProperty, EnumProperty


from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import dataCorrect, updateNode


class SvGenesHolderReset(bpy.types.Operator):

    bl_idname = "node.number_genes_reset"
    bl_label = "Number Genes Reset"

    idtree: bpy.props.StringProperty(default='')
    idname: bpy.props.StringProperty(default='')

    def execute(self, context):
        node = bpy.data.node_groups[self.idtree].nodes[self.idname]
        if node.number_type == 'vector':
            input_name = 'Vertices'
        else:
            input_name = 'Numbers'

        if node.inputs[input_name].is_linked:
            node.fill_from_input()
        else:
            seed_set(node.r_seed)
            node.fill_empty_dict()
        updateNode(node, context)
        return {'FINISHED'}

class SvGenesHolderNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Store Number List
    Tooltip: Stores a Vector List that can be modified by the Evolver Node
    """
    bl_idname = 'SvGenesHolderNode'
    bl_label = 'Genes Holder'
    bl_icon = 'RNA'

    def update_dict(self, context):
        if self.number_type == 'vector' and self.inputs['Vertices'].hide_safe:
            self.inputs['Vertices'].hide_safe = False
            self.inputs['Bounding Box'].hide_safe = False
            self.inputs['Numbers'].hide_safe = True
            self.outputs['Numbers'].hide_safe = True
            self.outputs['Vertices'].hide_safe = False
        elif not self.number_type == 'vector' and self.inputs['Numbers'].hide_safe:
            self.inputs['Vertices'].hide_safe = True
            self.inputs['Bounding Box'].hide_safe = True
            self.inputs['Numbers'].hide_safe = False
            self.outputs['Numbers'].hide_safe = False
            self.outputs['Vertices'].hide_safe = True

        if self.mode == 'order' and self.number_type == 'vector':
            self.inputs['Bounding Box'].hide_safe = True
        self.fill_memory()
        updateNode(self, context)

    r_seed: IntProperty(
        name='Count', description="Random Seed", default=3, update=update_dict)

    gene_count: IntProperty(
        name='Count', description="Number of elements", default=3, update=update_dict)

    number_options = [(k, k.title(), '', i) for i, k in enumerate(["int", "float", "vector"])]
    number_type: EnumProperty(
        name='Number Type',
        items=number_options,
        default='float',
        update=update_dict
    )

    int_limits: IntVectorProperty(
        name='Int Limits', description="Minimum values",
        default=(-10, 10),
        size=2, update=updateNode)

    float_limits: FloatVectorProperty(
        name='Float Limits', description="Maximum values",
        default=(-10, 10),
        size=2, update=updateNode)

    v_min_list: FloatVectorProperty(
        name='Max', description="Minimum values",
        default=(-1, -1, -1),
        size=3, update=updateNode)
    v_max_list: FloatVectorProperty(
        name='Max', description="Maximum values",
        default=(1, 1, 1),
        size=3, update=updateNode)
    mode_options = [(k, k.title(), '', i) for i, k in enumerate(["order", "range"])]
    mode: EnumProperty(
        name='Number Type',
        items=mode_options,
        default='range',
        update=update_dict
    )
    from_bbox: BoolProperty(default=False)
    from_input: BoolProperty(default=False)

    node_mem = {}
    memory: StringProperty(default="")

    def draw_number_buttons(self, col):
        if not self.inputs["Numbers"].is_linked:
            col.prop(self, "gene_count")
        if self.mode == 'range':
            if self.number_type == 'int':
                col.prop(self, 'int_limits', index=0, text='Min')
                col.prop(self, 'int_limits', index=1, text='Max')
            else:
                col.prop(self, 'float_limits', index=0, text='Min')
                col.prop(self, 'float_limits', index=1, text='Max')

    def draw_vector_buttons(self, col):

        if not self.inputs["Vertices"].is_linked:
            col.prop(self, "gene_count")
        if self.mode == 'order':
            return
        if not self.inputs["Bounding Box"].is_linked:
            titles = ["Min", "Max"]
            prop = ['v_min_list', 'v_max_list']

            for i in range(2):
                col.label(text=titles[i])
                row2 = col.row(align=True)
                for j in range(3):
                    row2 .prop(self, prop[i], index=j, text='XYZ'[j])

    def draw_buttons(self, context, layout):


        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "number_type", expand=True)
        row2 = col.row(align=True)
        row2.prop(self, "mode", expand=True)

        if self.number_type == 'vector':
            self.draw_vector_buttons(col)
        else:
            self.draw_number_buttons(col)

        self.wrapper_tracked_ui_draw_op(layout, "node.number_genes_reset", icon='RNA', text="RESET")

    def sv_init(self, context):
        self.width = 240

        self.inputs.new('SvStringsSocket', 'Numbers')
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvVerticesSocket', 'Bounding Box')
        self.inputs['Vertices'].hide_safe = True
        self.inputs['Bounding Box'].hide_safe = True
        self.outputs.new('SvStringsSocket', 'Numbers')
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs['Vertices'].hide_safe = True

    def write_memory_prop(self, data):
        '''write values to string property'''
        self.memory = ''.join(str(data))

    def check_memory_prop(self):
        tx = self.memory
        if len(tx) > 1:
            return ast.literal_eval(tx)
        return []

    def fill_empty_vect_dict(self):
        vects = []
        for i in range(self.gene_count):
            v = []
            for j in range(3):
                v_range = self.v_max_list[j] - self.v_min_list[j]
                v.append(self.v_min_list[j]+ random()*v_range)
            vects.append(v)
        self.node_mem[self.node_id] = vects
        self.write_memory_prop(vects)

    def fill_empty_nums_dict(self):
        nums = []
        list_limits = self.get_list_limits()
        n_range = list_limits[1] - list_limits[0]
        for i in range(self.gene_count):
            num = list_limits[0] + random()*n_range
            if self.number_type == 'int':
                num = int(num)
            nums.append(num)
        self.node_mem[self.node_id] = nums
        self.write_memory_prop(nums)

    def fill_empty_dict(self):
        if self.number_type == 'vector':
            self.fill_empty_vect_dict()
        else:
            self.fill_empty_nums_dict()

    def fill_num_mem(self):
        if self.node_id in self.node_mem:
            nums = self.node_mem[self.node_id]
        else:
            nums = []
        if len(nums) < self.gene_count:
            list_limits = self.get_list_limits()
            n_range = list_limits[1] - list_limits[0]
            for i in range(self.gene_count -len(nums)):
                num = list_limits[0] + random()*n_range
                if self.number_type == 'int':
                    num = int(num)
                nums.append(num)
        elif len(nums) > self.gene_count:
            nums = nums[:self.gene_count]
        self.node_mem[self.node_id] = nums
        self.write_memory_prop(nums)

    def fill_vect_mem(self):
        if self.node_id in self.node_mem:
            vects = self.node_mem[self.node_id]
        else:
            vects = []
        if len(vects) < self.gene_count:
            for i in range(self.gene_count -len(vects)):
                v = []
                for j in range(3):
                    v_range = self.v_max_list[j] - self.v_min_list[j]
                    v.append(self.v_min_list[j] + random()*v_range)
                vects.append(v)
        elif len(vects) > self.gene_count:
            vects = vects[:self.gene_count]
        self.node_mem[self.node_id] = vects
        self.write_memory_prop(vects)

    def fill_memory(self):
        if self.number_type == 'vector':
            self.fill_vect_mem()
        else:
            self.fill_num_mem()

    def fill_from_data(self, data):
        self.node_mem[self.node_id] = data
        self.write_memory_prop(data)

    def get_list_limits(self):
        if self.number_type == 'vector':
            return [self.v_min_list[:], self.v_max_list[:]]

        return self.int_limits if self.number_type == 'int' else self.float_limits

    def fill_vectors_from_input(self):
        if self.mode == 'order':
            vecs = self.inputs["Vertices"].sv_get(deepcopy=True)[0]
            self.gene_count = len(vecs)
            self.node_mem[self.node_id] = vecs
            self.write_memory_prop(vecs)
            return

        vecs = self.inputs["Vertices"].sv_get(deepcopy=False)[0]
        vecs_clipped = []
        self.gene_count = len(vecs)
        for v in vecs:
            v_clip = []
            for j in range(3):
                v_clip.append(max(min(v[j], self.v_max_list[j]), self.v_min_list[j]) )
            vecs_clipped.append(v_clip)
        self.node_mem[self.node_id] = vecs_clipped
        self.write_memory_prop(vecs_clipped)

    def fill_numbers_from_input(self):
        if self.mode == 'order':
            nums = self.inputs["Numbers"].sv_get(deepcopy=True)[0]
            self.gene_count = len(nums)
            self.node_mem[self.node_id] = nums
            self.write_memory_prop(nums)
            return

        nums = self.inputs["Numbers"].sv_get(deepcopy=False)[0]
        self.gene_count = len(nums)
        nums_clipped = []
        list_limits = self.get_list_limits()
        for num in nums:
            num_clip = max(min(num, list_limits[1]), list_limits[0])
            nums_clipped.append(num_clip)

        self.node_mem[self.node_id] = nums_clipped
        self.write_memory_prop(nums_clipped)

    def fill_from_input(self):
        if self.number_type == 'vector':
            self.fill_vectors_from_input()
        else:
            self.fill_numbers_from_input()

    def reset_limits_from_bbox(self):
        vec = self.inputs["Bounding Box"].sv_get(deepcopy=False)[0]
        maxmin = list(zip(map(max, *vec), map(min, *vec)))
        for j in range(3):
            self.v_max_list[j] = maxmin[j][0]
            self.v_min_list[j] = maxmin[j][1]

    def vector_mode_update(self):
        if self.inputs["Bounding Box"].is_linked and not self.from_bbox:
            self.from_bbox = True
            self.reset_limits_from_bbox()
        elif not self.inputs["Bounding Box"].is_linked and self.from_bbox:
            self.from_bbox = False

        if self.inputs["Vertices"].is_linked and not self.from_input:
            self.from_input = True
            self.fill_from_input()

        elif not self.inputs["Vertices"].is_linked and self.from_input:
            self.from_input = False

    def number_mode_update(self):
        if self.inputs["Numbers"].is_linked and not self.from_input:
            self.from_input = True
            self.fill_from_input()

        elif not self.inputs["Numbers"].is_linked and self.from_input:
            self.from_input = False

    def sv_update(self):
        if self.number_type == 'vector':
            self.vector_mode_update()
        else:
            self.number_mode_update()


    def process(self):
        # if not self.inputs['Vertices'].is_linked:
            # return
        if self.node_id in self.node_mem:
            genes_out = self.node_mem[self.node_id]
        else:
            text_memory = self.check_memory_prop()
            if text_memory:
                self.node_mem[self.node_id] = text_memory
                genes_out = self.node_mem[self.node_id]
            else:
                seed_set(self.r_seed)
                self.fill_empty_dict()
                genes_out = self.node_mem[self.node_id]

        if self.number_type == 'vector':
            self.outputs['Vertices'].sv_set([genes_out])
        else:
            self.outputs['Numbers'].sv_set([genes_out])


classes = [SvGenesHolderNode, SvGenesHolderReset]
register, unregister = bpy.utils.register_classes_factory(classes)
