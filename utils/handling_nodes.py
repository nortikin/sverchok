# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


"""
The module includes tools of automatization of creating nodes and get data from their sockets
"""

from operator import setitem
from typing import NamedTuple, Any, List

from bpy.types import Node


class SocketProperties(NamedTuple):
    name: str
    socket_type: str
    prop_name: str = ''
    custom_draw: str = ''
    deep_copy: bool = True
    vectorize: bool = True
    default: Any = object()


class NodeInputs:
    def __init__(self):
        self._sockets: List[SocketProperties] = []

    def __setattr__(self, key, value):
        if isinstance(value, SocketProperties):
            self._sockets.append(value)

        object.__setattr__(self, key, value)

    def add_sockets(self, node: Node):
        [node.inputs.new(p.socket_type, p.name) for p in self._sockets]
        [setattr(s, 'prop_name', p.prop_name) for s, p in zip(node.inputs, self._sockets)]
        [setattr(s, 'custom_draw', p.custom_draw) for s, p in zip(node.inputs, self._sockets)]


class NodeOutputs:
    def __init__(self):
        self._sockets: List[SocketProperties] = []

    def __setattr__(self, key, value):
        if isinstance(value, SocketProperties):
            self._sockets.append(value)

        object.__setattr__(self, key, value)

    def add_sockets(self, node: Node):
        [node.outputs.new(p.socket_type, p.name) for p in self._sockets]
        [setattr(s, 'custom_draw', p.custom_draw) for s, p in zip(node.inputs, self._sockets)]


class NodeProperties:
    def __init__(self):
        self._properties = dict()

    def __setattr__(self, key, value):
        if isinstance(value, tuple):
            # it should detect bpy.props...
            self._properties[key] = value

        object.__setattr__(self, key, value)

    def add_properties(self, node_annotations: dict):
        [setitem(node_annotations, name, prop) for name, prop in self._properties.items()]
