# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
The module includes tools of automatization of creating nodes and handling process method
Example of usage:


node = WrapNode()

node.props.x = NodeProperties(bpy.props.FloatProperty(update=updateNode))
node.props.y = NodeProperties(bpy.props.FloatProperty(update=updateNode))

node.inputs.verts = SocketProperties(name='Vertices', socket_type=SockTypes.VERTICES, mandatory=True)
node.inputs.faces = SocketProperties(name='Faces', socket_type=SockTypes.STRINGS)
node.inputs.x_axis = SocketProperties(name='X axis', socket_type=SockTypes.STRINGS, prop=node.props.x)
node.inputs.y_axis = SocketProperties(name='Y axis', socket_type=SockTypes.STRINGS, prop=node.props.y)

node.outputs.verts = SocketProperties(name='Vertices', socket_type=SockTypes.VERTICES)
node.outputs.faces = SocketProperties(name='Faces', socket_type=SockTypes.STRINGS)


@initialize_node(node)
class SvTestNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = 'SvTestNode'
    bl_label = 'Test node'

    def process(self):
        node.outputs.faces = node.inputs.faces
        node.outputs.verts = [(v[0] + x, v[1] + y, v[2]) for v, x, y in zip(
                              node.inputs.verts, cycle(node.inputs.x_axis), cycle(node.inputs.y_axis))]


def register(): bpy.utils.register_class(SvTestNode), def untegister(): bpy.utils.unregister_class(SvTestNode)
"""


from collections import defaultdict
from contextlib import contextmanager
from copy import copy
from enum import Enum
from functools import wraps
from typing import NamedTuple, Any, Type, Dict, Union, ValuesView, Callable

import bpy
from bpy.types import Node

from sverchok.data_structure import updateNode


class WrapNode:
    # instancing the class for crating properties and sockets
    def __init__(self):
        self.props = NodeProps(self)
        self.inputs = NodeInputs(self)
        self.outputs = NodeOutputs(self)

        self.bl_node: Union[Node, None] = None
        self.layer_number: Union[int, None] = None
        self.is_in_read_mode: bool = False

    def set_sv_init_method(self, node_class: Type[Node]):
        def sv_init(node, context):
            # the problem here is that it looks like Blender can't ketch any error from here if it is
            self.outputs.add_sockets(node)
            self.inputs.add_sockets(node)
            with self.read_data_mode(node):
                self.inputs.hide_sockets(node)
                self.outputs.hide_sockets(node)
        node_class.sv_init = sv_init

    def decorate_process_method(self, node_class: Type[Node]):

        def decorate_process(process):
            @wraps(node_class.process)
            def wrapper(node: Node):
                if self.inputs.has_required_data(node):
                    with self.read_data_mode(node):
                        for _ in self.layers_iterator():
                            process(node)
                        self.outputs.set_data_to_bl_sockets()
                else:
                    self.pass_data(node)
            return wrapper
        node_class.process = decorate_process(node_class.process)

    @contextmanager
    def read_data_mode(self, bl_node: Node):
        """
        it switch the class in reading mode what indicates that it is used by node instance
        it should be used for reading node properties and sockets data
        """
        self.bl_node = bl_node
        self.outputs.clear()  # otherwise a node can keep outdated number of objects(layer) and their data
        self.is_in_read_mode = True
        try:
            yield
        finally:
            self.is_in_read_mode = False

    def layers_iterator(self):
        # standard vectorization system
        max_layers_number = max([len(s.sv_get(default=[[]], deepcopy=False)) for s in self.bl_node.inputs])
        for layer_index in range(max_layers_number):
            self.layer_number = layer_index
            yield layer_index

    def pass_data(self, node: Node):
        # just pass data unchanged in case if given data is not sufficient for starting process
        # I have found this very useful in some case
        for in_sock, prop in zip(node.inputs, self.inputs.sockets_props):
            try:
                out_socket = node.outputs[prop.name]
                if in_sock.is_linked:
                    out_socket.sv_set(in_sock.sv_get(deepcopy=False))
                else:
                    # current update system want clean socket
                    out_socket.sv_set([[]])
            except KeyError:
                continue


def initialize_node(wrap_node: WrapNode):
    # class decorator for automatization sockets and property creation
    # also it automates vectorization system at this moment
    def wrapper(node_class: Type[Node]):
        wrap_node.props.add_properties(node_class.__annotations__)
        wrap_node.set_sv_init_method(node_class)
        if hasattr(node_class, 'process'):
            wrap_node.decorate_process_method(node_class)
        return node_class

    return wrapper


class SockTypes(Enum):
    STRINGS = "SvStringsSocket"
    VERTICES = "SvVerticesSocket"
    QUATERNION = "SvQuaternionSocket"
    COLOR = "SvColorSocket"
    MATRIX = "SvMatrixSocket"
    DUMMY = "SvDummySocket"
    SEPARATOR = "SvSeparatorSocket"
    OBJECT = "SvObjectSocket"
    TEXT = "SvTextSocket"
    DICTIONARY = "SvDictionarySocket"
    FILE_PATH = "SvFilePathSocket"
    SOLID = "SvSolidSocket"

    def get_name(self) -> str:
        return self.value


class NodeProperties(NamedTuple):
    bpy_props: tuple  # tuple is whet all bpy.props actually returns
    name: str = ''  # not mandatory, the name will be overridden by attribute name

    def replace_name(self, new_name):
        props = list(self)
        props[1] = new_name
        return type(self)(*props)


class SocketProperties(NamedTuple):
    name: str
    socket_type: SockTypes
    prop: NodeProperties = None
    custom_draw: str = ''
    deep_copy: bool = True
    vectorize: bool = True
    default: Any = [[]]
    mandatory: bool = False
    show_function: Callable[..., bool] = None


class NodeInputs:
    """
    It contains properties of input sockets of a node
    properties should be added in up down order by assigning SocketProperties object to an attribute
    like this: node_inputs.verts = SocketProperties("Verts", ....)
    it can contains two different types of attributes, have a look at NodeOutputs class description
    """
    def __init__(self, wrap_node: WrapNode):
        self.sockets: Dict[str, SocketProperties] = dict()
        self.wrap_node: WrapNode = wrap_node

    @property
    def sockets_props(self) -> ValuesView[SocketProperties]:
        return self.sockets.values()

    def __setattr__(self, key, value):
        if isinstance(value, SocketProperties):
            # new sockets is added
            self.sockets[key] = value
        elif key != 'sockets' and key in self.sockets:
            # handled data is added to socket probably from process method
            raise AttributeError(f"Attribute={key} is of socket type. Only SocketProperty can be assigned or nothing")
        else:
            # normal attributes or methods are adding
            object.__setattr__(self, key, value)

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, 'sockets'):
            # it is normal attribute
            return object.__getattribute__(self, name)
        elif not self.wrap_node.is_in_read_mode:
            # it is socket attribute and it is outside of process method
            return object.__getattribute__(self, 'sockets')[name]
        else:
            # it is socket attribute and it is inside process method
            return self._get_socket_data(name)

    def add_sockets(self, node: Node):
        # initialization sockets in a node
        [node.inputs.new(p.socket_type.get_name(), p.name) for p in self.sockets.values()]
        [setattr(s, 'prop_name', p.prop.name) for s, p in zip(node.inputs, self.sockets.values()) if p.prop]
        [setattr(s, 'custom_draw', p.custom_draw) for s, p in zip(node.inputs, self.sockets.values())]

    def has_required_data(self, node: Node) -> bool:
        # all mandatory are linked, but are there any data??
        return all([sock.is_linked for sock, prop in zip(node.inputs, self.sockets.values()) if prop.mandatory])

    def hide_sockets(self, node: Node):
        """Should be used for hiding sockets during node initialization or switching node parameter"""
        if not self.wrap_node.is_in_read_mode:
            raise RuntimeError(f"Can't hide sockets of the node={node.name} not in read mode")
        for sock, sock_prop in zip(node.inputs, self.sockets_props):
            if sock_prop.show_function is not None:
                sock.hide_safe = not sock_prop.show_function()

    def _get_socket_data(self, socket_name: str):
        # get socket attribute, inside loop
        socket_props = self.sockets[socket_name]
        bl_socket = self.wrap_node.bl_node.inputs[socket_props.name]
        socket_data = bl_socket.sv_get(deepcopy=False, default=socket_props.default)
        try:
            layer_data = socket_data[self.wrap_node.layer_number]
        except IndexError:
            layer_data = socket_data[-1]
        return copy(layer_data) if socket_props.deep_copy else layer_data


class NodeOutputs:
    """
    it has two different attribute types
    first are normal attributes and second attributes representing sockets
    they handled differently in set and get attributes methods
    socket attributes can also represent different data dependent on context
    usually they returns properties of a socket
    but in context of the process method they dill with actual data of a socket
    """
    def __init__(self, wrap_node: WrapNode):
        self.sockets: Dict[str, SocketProperties] = dict()  # should be initialize first !!!
        self.wrap_node: WrapNode = wrap_node
        self.socket_data: Dict[str, list] = defaultdict(list)

    @property
    def sockets_props(self) -> ValuesView[SocketProperties]:
        return self.sockets.values()

    def __setattr__(self, key, value):
        if isinstance(value, SocketProperties):
            # new sockets is added
            self.sockets[key] = value
        elif key != 'sockets' and key in self.sockets:
            # handled data is added to socket probably from process method
            self._add_socket_data(key, value)
        else:
            # normal attributes or methods are adding
            object.__setattr__(self, key, value)

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, 'sockets'):
            # it is normal attribute
            return object.__getattribute__(self, name)
        elif not self.wrap_node.is_in_read_mode:
            # it is socket attribute and it is outside of process method
            return object.__getattribute__(self, 'sockets')[name]
        else:
            # it is socket attribute and it is inside process method
            return self._get_socket_data(name)

    def add_sockets(self, node: Node):
        # initialization sockets in a node
        [node.outputs.new(p.socket_type.get_name(), p.name) for p in self.sockets_props]
        [setattr(s, 'custom_draw', p.custom_draw) for s, p in zip(node.inputs, self.sockets_props)]

    def set_data_to_bl_sockets(self):
        [s.sv_set(self.socket_data[name]) for s, name in zip(self.wrap_node.bl_node.outputs, self.sockets)]

    def clear(self):
        self.socket_data.clear()

    def hide_sockets(self, node: Node):
        """Should be used for hiding sockets during node initialization or switching node parameter"""
        if not self.wrap_node.is_in_read_mode:
            raise RuntimeError(f"Can't hide sockets of the node={node.name} not in read mode")
        for sock, sock_prop in zip(node.outputs, self.sockets_props):
            if sock_prop.show_function is not None:
                sock.hide_safe = not sock_prop.show_function()

    def _add_socket_data(self, socket_name: str, data):
        # add data of current layer to socket, existing data will be overridden
        if not self.wrap_node.is_in_read_mode:
            raise RuntimeError(f"Data can't be added to socket={socket_name} outside process method")
        socket_data = self.socket_data[socket_name]
        socket_layers_number = len
        while socket_layers_number(socket_data) <= self.wrap_node.layer_number:
            socket_data.append([])
        socket_data[self.wrap_node.layer_number] = data

    def _get_socket_data(self, socket_name: str):
        # get data of current layer from socket
        if not self.wrap_node.is_in_read_mode:
            raise AttributeError(f"Data can't be read from socket={socket_name} outside process method")
        socket_data = self.socket_data[socket_name]
        try:
            return socket_data[self.wrap_node.layer_number]
        except IndexError:
            raise AttributeError(f"Nothing was assigned to the socket={socket_name} "
                                 f"on current layer index={self.wrap_node.layer_number}")


class NodeProps:
    # the node has node property attributes and normal attributes
    def __init__(self, wrap_node: WrapNode):
        self.properties: Dict[str, NodeProperties] = dict()  # should be init first
        self.wrap_node: WrapNode = wrap_node

    def __setattr__(self, key, value):
        if isinstance(value, NodeProperties):
            # node property attribute
            self.properties[key] = value
        elif key != 'properties' and key in self.properties:
            # assigning to node property something what is node property
            return AttributeError(f"Attribute={key} is of node property type. "
                                  f"Only NodeProperty can be assigned or nothing")
        else:
            # normal attributes or methods are adding
            object.__setattr__(self, key, value)

    def __getattribute__(self, name):
        if name not in object.__getattribute__(self, 'properties'):
            # it is normal attribute
            return object.__getattribute__(self, name)
        elif not self.wrap_node.is_in_read_mode:
            # it is node property attribute and it is outside of process method
            return object.__getattribute__(self, 'properties')[name]
        else:
            # it is node property attribute and it is inside process method
            return getattr(self.wrap_node.bl_node, name)

    def add_properties(self, node_annotations: dict):
        """Assign properties to annotation dictionary of a node, update function will be assigned automatically"""
        def update_node(node, context):
            with self.wrap_node.read_data_mode(node):
                # without this manager sockets wont be able to read properties of a node instance
                self.wrap_node.inputs.hide_sockets(node)
                self.wrap_node.outputs.hide_sockets(node)
                updateNode(node, context)

        for name, prop in self.properties.items():

            bpy_prop, bpy_prop_arguments = prop.bpy_props
            bpy_prop_arguments['update'] = update_node
            rebuild_bpy_prop = blender_properties[bpy_prop](**bpy_prop_arguments)

            node_annotations[name] = rebuild_bpy_prop


blender_properties = {
    # properties are functions which return tuples with themselves as first argument
    # it should help to rebuild properties with new arguments
    bpy.props.BoolProperty()[0]: bpy.props.BoolProperty,
    bpy.props.BoolVectorProperty()[0]: bpy.props.BoolVectorProperty,
    bpy.props.CollectionProperty()[0]: bpy.props.CollectionProperty,
    bpy.props.EnumProperty()[0]: bpy.props.EnumProperty,
    bpy.props.FloatProperty()[0]: bpy.props.FloatProperty,
    bpy.props.FloatVectorProperty()[0]: bpy.props.FloatVectorProperty,
    bpy.props.IntProperty()[0]: bpy.props.IntProperty,
    bpy.props.IntVectorProperty()[0]: bpy.props.IntVectorProperty,
    bpy.props.PointerProperty()[0]: bpy.props.PointerProperty,
    bpy.props.StringProperty()[0]: bpy.props.StringProperty
}