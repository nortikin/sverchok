# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
import sverchok.utils.handling_nodes as hn


node = hn.WrapNode()

node.props.value = hn.NodeProperties(bpy.props.FloatProperty(name='Value'))

node.inputs.values = hn.SocketProperties(name='Values', socket_type=hn.SockTypes.STRINGS, prop=node.props.value,
                                         deep_copy=False)
node.inputs.data = hn.SocketProperties(name='Data', socket_type=hn.SockTypes.STRINGS, deep_copy=False, mandatory=True)

node.outputs.closest_values = hn.SocketProperties(name='Closest values', socket_type=hn.SockTypes.STRINGS)
node.outputs.closest_indexes = hn.SocketProperties(name='Closest indexes', socket_type=hn.SockTypes.STRINGS)


@hn.initialize_node(node)
class SvFindClosest(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvFindClosest'
    bl_label = 'Find closest'
    bl_icon = 'VIEWZOOM'

    def process(self):
        extended_data = np.array(node.inputs.data + [-np.inf, np.inf])
        sorting_indexes = np.argsort(extended_data)
        right_indexes = np.searchsorted(extended_data, node.inputs.values, sorter=sorting_indexes)
        left_indexes = right_indexes - 1
        left_distance = node.inputs.values - extended_data[sorting_indexes[left_indexes]]
        left_distance = np.where(left_distance < 0, -left_distance, left_distance)
        right_distance = extended_data[sorting_indexes[right_indexes]] - node.inputs.values
        right_distance = np.where(right_distance < 0, -right_distance, right_distance)
        result_indexes = np.where(left_distance < right_distance, left_indexes, right_indexes)
        node.outputs.closest_indexes = sorting_indexes[result_indexes].tolist()
        node.outputs.closest_values = extended_data[node.outputs.closest_indexes].tolist()
