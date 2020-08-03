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
from typing import NamedTuple, Any, List, Generator, Union, Type

from bpy.types import Node


class WrapNode:
    def __init__(self):
        self.props = NodeProperties()
        self.inputs = NodeInputs()
        self.outputs = NodeOutputs()

    def set_sv_init_method(self, node_class: Type[Node]):
        def sv_init(node, context):
            self.inputs.add_sockets(node)
            self.outputs.add_sockets(node)
        node_class.sv_init = sv_init

    def decorate_process_method(self, node_class: Type[Node]):

        def decorate_process(process):
            @wraps(node_class.process)
            def wrapper(node: Node):
                if self.inputs.has_required_data(node):
                    return process(node)
                else:
                    self.inputs.pass_data(node)
            return wrapper
        node_class.process = decorate_process(node_class.process)


def initialize_node(wrap_node: WrapNode):

    def wrapper(node_class: Type[Node]):
        wrap_node.props.add_properties(node_class.__annotations__)
        wrap_node.set_sv_init_method(node_class)
        wrap_node.decorate_process_method(node_class)
        return node_class

    return wrapper


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
    """
    It contains properties of input sockets of a node
    properties should be added in up down order by assigning SocketProperties object to an attribute
    like this: node_inputs.verts = SocketProperties("Verts", 'SvVerticesSocket')
    don't add any other attributes neither other then SocketProperties neither outside the class or inside
    __setattr__ and __getattribute__ method won't let it
    """
    def add_sockets(self, node: Node):
        # initialization sockets in a node
        [node.inputs.new(p.socket_type, p.name) for p in self._sockets]
        [setattr(s, 'prop_name', p.prop_name) for s, p in zip(node.inputs, self._sockets)]
        [setattr(s, 'custom_draw', p.custom_draw) for s, p in zip(node.inputs, self._sockets)]

    def check_input_data(self, process):
        # decorator for process function
        @wraps(process)
        def wrapper(node: Node):
            if self.has_required_data(node):
                return process(node)
            else:
                self.pass_data(node)
        return wrapper

    def __init__(self):
        object.__setattr__(self, '_sockets', [])
        object.__setattr__(self, '_socket_attr_names', set())

    @property
    def sockets(self):
        return self._sockets

    @property
    def socket_attr_names(self):
        return self._socket_attr_names

    def __setattr__(self, key, value):
        # only used for adding new sockets
        if isinstance(value, SocketProperties):
            # socket attribute contains only index to data in the sockets list
            object.__setattr__(self, key, len(self.sockets))
            self.sockets.append(value)
            self.socket_attr_names.add(key)
        else:
            raise TypeError("Only SocketProperties type can be assigned to a attribute")

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, '_socket_attr_names'):  # Name intersections ???
            return object.__getattribute__(self, name)

        if object.__getattribute__(self, '_current_layer') is None:
            raise AttributeError("The values of sockets can't be read outside 'invoke layers' context manager")
        # todo

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

    @staticmethod
    def set_data(node: Node, data: list):
        # data should be joined by layers, each layer should be consistent to output sockets
        [s.sv_set(d) for s, d in zip(node.outputs, zip(*data))]


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
