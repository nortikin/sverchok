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
import numpy as np
from bpy.props import IntProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)
from sverchok.utils.handling_nodes import NodeProperties, SockTypes, SocketProperties, initialize_node, WrapNode


node = WrapNode()

node.props.data_to_mask = NodeProperties(
    bpy_props=BoolProperty(
        name="Data masking",
        description="Use data to define mask length",
        default=False))
node.props.is_topo_mask = NodeProperties(
    bpy_props=BoolProperty(
        name="Topo mask",
        description="data consists of verts or polygons / edges. "
                    "Otherwise the two vertices will be masked as [[[T, T, T], [F, F, F]]] instead of [[T, F]]",
        default=False))
node.props.index = NodeProperties(bpy_props=IntProperty(name="Index"))
node.props.mask_size = NodeProperties(bpy_props=IntProperty(name='Mask Length', default=10, min=2))

node.inputs.index = SocketProperties(
    name="Index",
    socket_type=SockTypes.STRINGS,
    prop=node.props.index,
    deep_copy=False)
node.inputs.mask_size = SocketProperties(
    name="Mask size",
    socket_type=SockTypes.STRINGS,
    prop=node.props.mask_size,
    deep_copy=False,
    show_function=lambda: not node.props.data_to_mask)
node.inputs.data_to_mask = SocketProperties(
    name="Data masking",
    socket_type=SockTypes.STRINGS,
    deep_copy=False,
    mandatory=True,
    show_function=lambda: node.props.data_to_mask)

node.outputs.mask = SocketProperties(name="Mask", socket_type=SockTypes.STRINGS)


@initialize_node(node)
class SvIndexToMaskNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Create mask list from index '''
    bl_idname = 'SvIndexToMaskNode'
    bl_label = 'Index To Mask'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INDEX_TO_MASK'

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "data_to_mask", toggle=True)
        if self.data_to_mask:
            col.prop(self, "is_topo_mask", toggle=True)

    def process(self):
        print("!!!!!!!!!!!!!!!!!!")
        # Inds, MaSi, Dat = self.inputs
        # OM = self.outputs[0]
        # if OM.is_linked:
        #     out = []
        #     I = Inds.sv_get()
        #     if not self.data_to_mask:
        #         for Ind, Size in zip(I, safc(I, MaSi.sv_get()[0])):
        #             Ma = np.zeros(Size, dtype= np.bool)
        #             Ma[Ind] = 1
        #             out.append(Ma.tolist())
        #     else:
        #         Ma = np.zeros_like(Dat.sv_get(), dtype= np.bool)
        #         if not self.complex_data:
        #             for m, i in zip(Ma, safc(Ma, I)):
        #                 m[i] = 1
        #                 out.append(m.tolist())
        #         else:
        #             for m, i in zip(Ma, safc(Ma, I)):
        #                 m[i] = 1
        #                 out.append(m[:, 0].tolist())
        #     OM.sv_set(out)


def register():
    bpy.utils.register_class(SvIndexToMaskNode)


def unregister():
    bpy.utils.unregister_class(SvIndexToMaskNode)
