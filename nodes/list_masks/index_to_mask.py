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
from itertools import cycle

import numpy as np

import bpy
from bpy.props import IntProperty, BoolProperty
from sverchok.data_structure import updateNode, fixed_iter

from sverchok.node_tree import SverchCustomTreeNode


class SvIndexToMaskNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Create mask list from index '''
    bl_idname = 'SvIndexToMaskNode'
    bl_label = 'Index To Mask'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INDEX_TO_MASK'

    def data_to_mask_update(self, context):
        self.inputs['Mask size'].hide_safe = self.data_to_mask
        self.inputs['Data masking'].hide_safe = not self.data_to_mask
        updateNode(self, context)

    data_to_mask: BoolProperty(name="Data masking", description="Use data to define mask length", default=False,
                                update=data_to_mask_update)

    is_topo_mask: BoolProperty(
        name="Topo mask", default=False, update=updateNode,
        description="data consists of verts or polygons / edges. "
                    "Otherwise the two vertices will be masked as [[[T, T, T], [F, F, F]]] instead of [[T, F]]")

    output_numpy: BoolProperty(
        name="Output NumPy", default=False, update=updateNode,
        description="Output Numpy arrays in stead of regular python lists")

    # socket properties
    index: IntProperty(name="Index", update=updateNode)
    mask_size: IntProperty(name='Mask Length', default=10, min=2, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "Index").prop_name = "index"
        self.inputs.new("SvStringsSocket", "Mask size").prop_name = "mask_size"
        self.inputs.new("SvStringsSocket", "Data masking").hide_safe = True
        self.outputs.new("SvStringsSocket", "Mask")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "data_to_mask", toggle=True)
        if self.data_to_mask:
            col.prop(self, "is_topo_mask", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'output_numpy')

    def rclick_menu(self, context, layout):
        layout.prop(self, 'output_numpy')

    def process(self):
        # upgrade old nodes
        if 'mask size' in self.inputs:
            self.inputs['mask size'].name = 'Mask size'
        if 'data to mask' in self.inputs:
            self.inputs['data to mask'].name = 'Data masking'
        if 'mask' in self.outputs:
            self.outputs['mask'].name = 'Mask'

        index = self.inputs["Index"].sv_get(deepcopy=False, default=[])
        mask_size = self.inputs['Mask size'].sv_get(deepcopy=False, default=[None])
        data_to_mask = self.inputs['Data masking'].sv_get(deepcopy=False,
                                                          default=[] if self.data_to_mask else [None])

        obj_num = max(len(d) for d in [index, mask_size, data_to_mask])
        masks = []
        for ind, mask, data in zip(fixed_iter(index, obj_num), fixed_iter(mask_size, obj_num),
                                   fixed_iter(data_to_mask, obj_num)):
            if not self.data_to_mask:
                mask = mask[0] if mask is not None else 0
                mask = np.zeros(int(mask), dtype=bool)
            else:
                if self.is_topo_mask:
                    mask = np.zeros(len(data), dtype=bool)
                else:
                    # inconsistent mode with Sverchok data structure, should be reconsidered in MK2 version
                    mask = np.zeros_like(data, dtype=bool)

            mask[ind] = True
            masks.append(mask)

        if self.output_numpy:
            self.outputs['Mask'].sv_set(masks)
        else:
            self.outputs['Mask'].sv_set([m.tolist() for m in masks])


register, unregister = bpy.utils.register_classes_factory([SvIndexToMaskNode])
