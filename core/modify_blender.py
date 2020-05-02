# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
This module will init some extra attributes for some Blender internal objects
It need for consistent work of Sverchok
"""

import time

import bpy


def node_id(self):
    # this attribute is for reroutes nodes
    if not self.n_id:
        self.n_id = str(hash(self) ^ hash(time.monotonic()))
    return self.n_id


def socket_id(self):
    # this attribute for reroute sockets
    """Id of socket used by data_cache"""
    return str(hash(self.node.node_id + self.identifier))


# todo add link attribute


bpy.types.NodeReroute.n_id = bpy.props.StringProperty(default="")
bpy.types.NodeReroute.node_id = property(node_id)
bpy.types.NodeSocketColor.socket_id = property(socket_id)
