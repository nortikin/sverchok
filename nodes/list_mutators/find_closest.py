# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

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
