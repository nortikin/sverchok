# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


"""
The module includes tools of automatization of creating nodes and get data from their sockets
"""

from functools import wraps
from itertools import cycle
from operator import setitem
from typing import NamedTuple, Any, List, Generator

from bpy.types import Node


class SocketProperties(NamedTuple):
    name: str
    socket_type: str
    prop_name: str = ''
    custom_draw: str = ''
    deep_copy: bool = True
    vectorize: bool = True
    default: Any = object()
    mandatory: bool = False


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

    def check_input_data(self, process):
        @wraps(process)
        def wrapper(node: Node):
            if self.has_required_data(node):
                return process(node)
            else:
                self.pass_data(node)
        return wrapper

    def has_required_data(self, node: Node) -> bool:
        return all([sock.is_linked for sock, prop in zip(node.inputs, self._sockets) if prop.mandatory])

    def pass_data(self, node: Node):
        # just pass data unchanged in case if given data is not sufficient for starting process
        for in_sock, prop in zip(node.inputs, self._sockets):
            try:
                out_socket = node.outputs[prop.name]
                if in_sock.is_linked:
                    out_socket.sv_set(in_sock.sv_get(deepcopy=False))
                else:
                    # current update system want clean socket
                    out_socket.sv_set([[]])
            except KeyError:
                continue

    def get_data(self, node: Node) -> Generator[list, None, None]:
        # extract data from sockets
        data = [s.sv_get(default=p.default, deepcopy=p.deep_copy) for s, p in zip(node.inputs, self._sockets)]
        max_layers_number = max([len(sd) for sd in data])
        data = [cycle(sd) if p.vectorize else sd for sd, p in zip(data, self._sockets)]
        for i, *data_layer in zip(range(max_layers_number, *data)):
            yield data_layer


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
