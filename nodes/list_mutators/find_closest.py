# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import repeat_last
import sverchok.utils.handling_nodes as hn


node = hn.WrapNode()

node.props.value = hn.NodeProperties(bpy.props.FloatProperty(name='Value'))
node.props.mode = hn.NodeProperties(bpy.props.EnumProperty(items=[(m, m, '') for m in ('single', 'range')]))
node.props.range = hn.NodeProperties(bpy.props.FloatProperty(default=0.1))

node.inputs.values = hn.SocketProperties(
    name='Values', socket_type=hn.SockTypes.STRINGS, prop=node.props.value, deep_copy=False)
node.inputs.data = hn.SocketProperties(name='Data', socket_type=hn.SockTypes.STRINGS, deep_copy=False, mandatory=True)
node.inputs.range = hn.SocketProperties(
    name='Range', socket_type=hn.SockTypes.STRINGS, prop=node.props.range, deep_copy=False,
    show_function=lambda: True if node.props.mode == 'range' else False)

node.outputs.closest_values = hn.SocketProperties(name='Closest values', socket_type=hn.SockTypes.STRINGS)
node.outputs.closest_indexes = hn.SocketProperties(name='Closest indexes', socket_type=hn.SockTypes.STRINGS)


@hn.initialize_node(node)
class SvFindClosestValue(bpy.types.Node, SverchCustomTreeNode):
    """Triggers: find search closest"""
    bl_idname = 'SvFindClosestValue'
    bl_label = 'Find closest value'
    bl_icon = 'VIEWZOOM'

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)

    def process(self):
        if not all([node.inputs.values, node.inputs.data]):
            # it would be better to place such checking into class decorator but too lazy
            node.outputs.closest_values, node.outputs.closest_indexes = [], []
            return

        extended_data = np.array(node.inputs.data + [-np.inf, np.inf])
        sorting_indexes = np.argsort(extended_data)

        if node.props.mode == 'range':
            if not node.inputs.range:
                node.outputs.closest_values, node.outputs.closest_indexes = [], []
                return

            len_input = max([len(node.inputs.values), len(node.inputs.range)])
            values = np.fromiter(repeat_last(node.inputs.values), float, count=len_input)
            range_values = np.fromiter(repeat_last(node.inputs.range), float, count=len_input)
            l_values = values - range_values
            l_indexes = np.searchsorted(extended_data, l_values, side='right', sorter=sorting_indexes)
            r_values = values + range_values
            r_indexes = np.searchsorted(extended_data, r_values, side='right', sorter=sorting_indexes)
            closest_indexes = [[sorting_indexes[i] for i in range(l, r)] for l, r in zip(l_indexes, r_indexes)]
            node.outputs.closest_indexes = closest_indexes
            node.outputs.closest_values = [extended_data[ci].tolist() for ci in closest_indexes]
        else:
            right_indexes = np.searchsorted(extended_data, node.inputs.values, sorter=sorting_indexes)
            left_indexes = right_indexes - 1
            left_distance = node.inputs.values - extended_data[sorting_indexes[left_indexes]]
            left_distance = np.where(left_distance < 0, -left_distance, left_distance)
            right_distance = extended_data[sorting_indexes[right_indexes]] - node.inputs.values
            right_distance = np.where(right_distance < 0, -right_distance, right_distance)
            result_indexes = np.where(left_distance < right_distance, left_indexes, right_indexes)
            node.outputs.closest_indexes = sorting_indexes[result_indexes].tolist()
            node.outputs.closest_values = extended_data[node.outputs.closest_indexes].tolist()
