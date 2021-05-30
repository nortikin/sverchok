# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

import inspect
import sys
from abc import abstractmethod, ABC
from enum import Enum, auto
from itertools import chain
from typing import Type, Generator, TYPE_CHECKING, Dict, Tuple, Optional, List, Any

import bpy
from sverchok import old_nodes
from sverchok.utils import dummy_nodes
from sverchok.utils.handle_blender_data import BPYPointers, BPYProperty
from sverchok.utils.sv_node_utils import recursive_framed_location_finder

if TYPE_CHECKING:
    from sverchok.utils.sv_json_import import FailsLog


class StructFactory:
    # it's possible to use version factory in the code to make the code more specific
    # if struct_factories.link.version == 0.2:
    def __init__(self, factories: List[Type[Struct]]):
        self._factory_names = {
            StrTypes.TREE: 'tree',
            StrTypes.NODE: 'node',
            StrTypes.SOCK: 'sock',
            StrTypes.INTERFACE: 'interface',
            StrTypes.LINK: 'link',
            StrTypes.PROP: 'prop'
        }

        self.tree: Optional[Type[Struct]] = None
        self.node: Optional[Type[Struct]] = None
        self.sock: Optional[Type[Struct]] = None
        self.interface: Optional[Type[Struct]] = None
        self.link: Optional[Type[Struct]] = None
        self.prop: Optional[Type[Struct]] = None

        for factory in factories:
            if factory.type in self._factory_names:
                factory_name = self._factory_names[factory.type]
                setattr(self, factory_name, factory)
            else:
                raise TypeError(f'Factory with type: {factory.type}'
                                f' is not among supported: {self._factory_names.keys()}')

    def get_factory(self, struct_type: StrTypes) -> Type[Struct]:
        if struct_type in self._factory_names:
            factory_name = self._factory_names[struct_type]
            return getattr(self, factory_name)
        else:
            raise TypeError(f'Given struct type: {struct_type} is not among supported {self._factory_names.keys()}')

    @classmethod
    def __match_factories(cls, version: float) -> StructFactory:  # todo for future automatization?
        """Choose factories which are most appropriate for given version"""
        struct_factories = cls([])
        module_classes = inspect.getmembers(sys.modules[__name__],
                                            lambda member: inspect.isclass(member) and member.__module__ == __name__)
        for module_class in module_classes:
            pass


class StrTypes(Enum):
    FILE = auto()
    TREE = auto()
    NODE = auto()
    SOCK = auto()
    INTERFACE = auto()  # node groups sockets
    LINK = auto()
    PROP = auto()

    def get_bpy_pointer(self) -> BPYPointers:
        mapping = {
            StrTypes.TREE: BPYPointers.NODE_TREE,
            StrTypes.NODE: BPYPointers.NODE,
        }
        if self not in mapping:
            raise TypeError(f'Given StrType: {self} is not a data block')
        return mapping[self]

    @classmethod
    def get_type(cls, block_type: BPYPointers) -> StrTypes:
        mapping = {
            BPYPointers.NODE_TREE: StrTypes.TREE,
            BPYPointers.NODE: StrTypes.NODE,
        }
        if block_type not in mapping:
            raise TypeError(f'Given block type: {block_type} is not among supported: {mapping.keys()}')
        return mapping[block_type]

    @classmethod
    def is_supported_block(cls, block_type: BPYPointers) -> bool:
        try:
            cls.get_type(block_type)
            return True
        except TypeError:
            return False


class Struct(ABC):
    # I was trying to make API of all abstract method the same between child classes but it looks it's not possible
    # for example to build a node we can send to method a tree where the node should be duilded
    version = 1.0  # override the property if necessary
    type: StrTypes = None  # should be overridden

    @abstractmethod
    def __init__(self, name: Optional[str], logger: FailsLog, struct: dict = None):
        ...

    @abstractmethod
    def export(self, data_block, struct_factories: StructFactory, dependencies: List[Tuple[BPYPointers, str]]) -> dict:
        ...

    @abstractmethod
    def build(self, *args):
        ...

    @abstractmethod
    def read(self):
        ...

    def read_bl_type(self) -> str:
        """typically should return bl_idname of the structure"""
        return None

    def read_collection(self, collection: dict):
        for name, structure in collection.items():
            with self.logger.add_fail("Reading collection"):
                yield name, structure


class FileStruct(Struct):
    type = StrTypes.FILE

    def __init__(self, name=None, logger: FailsLog = None, struct: dict = None):
        self._struct: Dict[str, Any] = struct or {"export_version": str(self.version)}
        self.logger: FailsLog = logger

    def export(self):
        # I would expect this method import the whole Sverchok data in a file
        raise NotImplementedError

    def export_tree(self, tree, use_selection=False):
        if tree.bl_idname != 'SverchCustomTreeType':
            raise TypeError(f'Only exporting main trees is supported, {tree.bl_label} is given')
        self._struct["main_tree"] = dict()
        struct_factories = StructFactory(
            [TreeStruct, NodeStruct, SocketStruct, InterfaceStruct, LinkStruct, PropertyStruct])  # todo to args?
        dependencies: List[Tuple[BPYPointers, str]] = []

        # export main tree first
        factory = struct_factories.get_factory(StrTypes.TREE)
        struct = factory(tree.name, self.logger)
        if use_selection:
            raw_struct = struct.export_nodes([n for n in tree.nodes if n.select], struct_factories, dependencies)
        else:
            raw_struct = struct.export(tree, struct_factories, dependencies)
        self._struct["main_tree"][tree.name] = raw_struct

        # it looks good place for exporting dependent data blocks because probably we do not always want to export them
        # from this place we have more control over it
        while dependencies:
            block_type, block_name = dependencies.pop()
            struct_type = StrTypes.get_type(block_type)
            if struct_type.name not in self._struct:
                self._struct[struct_type.name] = dict()
            if block_name not in self._struct[struct_type.name]:
                factory = struct_factories.get_factory(struct_type)
                data_block = block_type.collection[block_name]
                structure = factory(block_name, self.logger).export(data_block, struct_factories, dependencies)
                self._struct[struct_type.name][block_name] = structure

        return self._struct

    def build(self, *_):
        raise NotImplementedError

    def build_into_tree(self, tree):  # todo add protection from exporting inside node groups
        # it looks that recursive import should be avoided by any cost, it's too difficult to pass data
        # luckily it's possible to create all data block first
        # and then they will be available for assigning to pointer properties
        # with tree data blocks it can be a beat trickier,
        # all trees should be created and only after that field with content

        with tree.throttle_update():  # todo it is required only for current update system can be deleted later??

            factories = StructFactory(
                [TreeStruct, NodeStruct, SocketStruct, InterfaceStruct, LinkStruct, PropertyStruct])
            imported_structs = OldNewNames()
            trees_to_build = []
            version, main_tree, data_blocks = self.read()

            # initialize trees and build other data block types
            for struct_type, block_name, raw_struct in chain(main_tree, data_blocks):
                if struct_type == StrTypes.TREE:
                    tree_struct = factories.tree(block_name, self.logger, raw_struct)
                    if not trees_to_build:
                        # this is first tree and it should be main, does not need create anything
                        data_block = tree
                    else:
                        # this is node group tree, should be created?
                        data_block = bpy.data.node_groups.new(block_name, tree_struct.read_bl_type())
                        # interface should be created before building all trees
                        tree_struct.build_interface(data_block, factories, imported_structs)
                    imported_structs[(struct_type, '', block_name)] = data_block.name
                    trees_to_build.append(tree_struct)
                else:
                    # all data block except node trees
                    block_type = struct_type.get_bpy_pointer()
                    data_block = block_type.collection.new(block_name)
                    imported_structs[(struct_type, '', block_name)] = data_block.name
                    factories.get_factory(struct_type)(block_name, self.logger, raw_struct).build()

            # todo before building trees should be registered old and dummy nodes if necessary

            for tree_struct in trees_to_build:
                # build all trees
                new_name = imported_structs[StrTypes.TREE, '', tree_struct.name]
                data_block = bpy.data.node_groups[new_name]
                tree_struct.build(data_block, factories, imported_structs)

    def read(self):
        with self.logger.add_fail("Reading version of the file"):
            version = float(self._struct["export_version"])

        main_tree_struct = self._struct.get("main_tree")
        main_tree_reader = ((StrTypes.TREE, name, raw_struct) for name, raw_struct in main_tree_struct.items())

        return version, main_tree_reader, self._data_blocks_reader()

    def _data_blocks_reader(self):  # todo add logger?
        struct_type: StrTypes
        for struct_type_name, structures in self._struct.items():
            if struct_type_name in (it.name for it in StrTypes):
                for block_name, block_struct in structures.items():
                    yield StrTypes[struct_type_name], block_name, block_struct


class TreeStruct(Struct):
    type = StrTypes.TREE

    def __init__(self, name: str, logger: FailsLog, structure: dict = None):
        default_structure = {
            "nodes": dict(),
            "links": [],
            "inputs": dict(),
            "outputs": dict(),
            "bl_idname": "",
        }
        self._struct = structure or default_structure
        self.name = name
        self.logger = logger

    def export(self, tree, factories: StructFactory, dependencies) -> dict:
        # todo export tree properties, for all trees? only for group trees?
        for node in tree.nodes:
            raw_struct = factories.node(node.name, self.logger).export(node, factories, dependencies)
            self._struct['nodes'][node.name] = raw_struct

        for link in _ordered_links(tree):
            self._struct["links"].append(factories.link(None, self.logger).export(link, factories, dependencies))

        for socket in tree.inputs:
            raw_struct = factories.interface(socket.name, self.logger).export(socket, factories, dependencies)
            self._struct["inputs"][socket.identifier] = raw_struct

        for socket in tree.outputs:
            raw_struct = factories.interface(socket.name, self.logger).export(socket, factories, dependencies)
            self._struct["outputs"][socket.identifier] = raw_struct

        self._struct["bl_idname"] = tree.bl_idname
        return self._struct

    def export_nodes(self, nodes, factories: StructFactory, dependencies) -> dict:
        tree = nodes[0].id_data
        for node in nodes:
            if node.id_data != tree:
                raise TypeError(f"Given node from different trees: {tree.name} and {node.id_data.name}")
            raw_struct = factories.node(node.name, self.logger).export(node, factories, dependencies)
            self._struct["nodes"][node.name] = raw_struct

        input_node_names = {node.name for node in nodes}
        for link in _ordered_links(tree):
            if link.from_node.name in input_node_names and link.to_node.name in input_node_names:
                self._struct["links"].append(factories.link(None, self.logger).export(link, factories, dependencies))

        for socket in tree.inputs:
            raw_struct = factories.interface(socket.name, self.logger).export(socket, factories, dependencies)
            self._struct["inputs"][socket.identifier] = raw_struct

        for socket in tree.outputs:
            raw_struct = factories.interface(socket.name, self.logger).export(socket, factories, dependencies)
            self._struct["outputs"][socket.identifier] = raw_struct

        self._struct["bl_idname"] = tree.bl_idname
        return self._struct

    def build(self, tree, factories: StructFactory, imported_structs: OldNewNames):
        """Reads and generates nodes, links, dependent data blocks"""
        nodes, links = self.read()

        # first all nodes should be created without applying their inner data
        # because some nodes can have `parent` property which points into another node
        node_structs = []
        for node_name, raw_structure in nodes:
            node_struct = factories.node(node_name, self.logger, raw_structure)

            # register optional node classes
            if old_nodes.is_old(node_struct.read_bl_type()):
                old_nodes.register_old(node_struct.read_bl_type())
            if dummy_nodes.is_dependent(node_struct.read_bl_type()):
                dummy_nodes.register_dummy(node_struct.read_bl_type())

            # add node an save its new name
            node = tree.nodes.new(node_struct.read_bl_type())
            node.name = node_name
            imported_structs[(StrTypes.NODE, tree.name, node_name)] = node.name
            node_structs.append(node_struct)

        for node_struct in node_structs:
            new_name = imported_structs[(StrTypes.NODE, tree.name, node_struct.name)]
            node = tree.nodes[new_name]
            node_struct.build(node, factories, imported_structs)

        for raw_struct in links:
            factories.link(None, self.logger, raw_struct).build(tree, factories, imported_structs)

    def read(self):
        with self.logger.add_fail("Reading nodes"):
            nodes_struct = self._struct["nodes"]
            nodes_reader = self.read_collection(nodes_struct)

        with self.logger.add_fail("Reading links"):
            links_struct = self._struct["links"]
            links_reader = (link_struct for link_struct in links_struct)

        return nodes_reader, links_reader

    def build_interface(self, tree, factories, imported_structs):
        inputs, outputs = self.read_interface_data()
        # create tree sockets
        with self.logger.add_fail("Create tree socket"):
            for sock_name, raw_struct in inputs:
                factories.interface(sock_name, self.logger, raw_struct).build(tree.inputs, factories, imported_structs)

        with self.logger.add_fail("Create tree socket"):
            for sock_name, raw_struct in outputs:
                factories.interface(sock_name, self.logger, raw_struct).build(tree.outputs, factories, imported_structs)

    def read_interface_data(self):
        with self.logger.add_fail("Reading inputs"):
            input_struct = self._struct["inputs"]
            input_reader = self.read_collection(input_struct)

        with self.logger.add_fail("Reading outpus"):
            outputs_struct = self._struct["outputs"]
            output_reader = self.read_collection(outputs_struct)
        return input_reader, output_reader

    def read_bl_type(self):
        return self._struct["bl_idname"]


class NodeStruct(Struct):
    type = StrTypes.NODE

    def __init__(self, name: str, logger: FailsLog, structure: dict = None):
        default_structure = {
            "attributes": dict(),
            "properties": dict(),
            "inputs": dict(),
            "outputs": dict(),
            "bl_idname": ""
        }
        self._struct = structure or default_structure
        self.name = name
        self.logger = logger
        self._attributes = {
            "height": None,
            "width": None,
            "label": '',
            "hide": False,
            "location": (0, 0),
            "color": (0, 0, 0),
            "use_custom_color": False,
            "parent": None
        }

    def export(self, node, factories: StructFactory, dependencies) -> dict:
        # add_mandatory_attributes
        self._struct['bl_idname'] = node.bl_idname
        self._struct["attributes"]['height'] = node.height
        self._struct["attributes"]['width'] = node.width
        self._struct["attributes"]['label'] = node.label
        self._struct["attributes"]['hide'] = node.hide
        self._struct["attributes"]['location'] = recursive_framed_location_finder(node, node.location[:])

        # optional attributes
        if node.use_custom_color:
            self._struct["attributes"]['color'] = node.color[:]
            self._struct["attributes"]['use_custom_color'] = True
        if node.parent:  # the node is inside of a frame node
            prop = BPYProperty(node, "parent")
            raw_struct = factories.prop("parent", self.logger).export(prop, factories, dependencies)
            self._struct["attributes"]["parent"] = raw_struct

        # add non default node properties
        for prop_name in node.keys():
            prop = BPYProperty(node, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:  # todo check every where
                    self._struct["properties"][prop.name] = raw_struct

        # all sockets should be kept in a file because it's possible to create UI
        # where sockets would be defined by pressing buttons for example like in the node group interface.
        # there is no sense of exporting information about sockets of group input and output nodes
        # they are totally controlled by Blender update system.
        if node.bl_idname not in ['NodeGroupInput', 'NodeGroupOutput']:
            for socket in node.inputs:
                raw_struct = factories.sock(socket.identifier, self.logger).export(socket, factories, dependencies)
                self._struct["inputs"][socket.identifier] = raw_struct

            for socket in node.outputs:
                raw_struct = factories.sock(socket.identifier, self.logger).export(socket, factories, dependencies)
                self._struct["outputs"][socket.identifier] = raw_struct

        if hasattr(node, 'save_to_json'):
            node.save_to_json(self._struct)

        return self._struct

    def build(self, node, factories: StructFactory, imported_data: OldNewNames):
        # todo it would be nice? to add context to logger of what is currently is being created (not only here)
        attributes, properties, inputs, outputs = self.read()
        for attr_name, attr_value in attributes:
            with self.logger.add_fail("Setting node attribute",
                                      f'Tree: {node.id_data.name}, Node: {node.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(node, factories, imported_data)

        for prop_name, prop_value in properties:
            with self.logger.add_fail("Setting node property",
                                      f'Tree: {node.id_data.name}, Node: {node.name}, prop: {prop_name}'):
                factories.prop(prop_name, self.logger, prop_value).build(node, factories, imported_data)

        # does not trust to correctness of socket collections created by an init method.
        # clearing sockets calls update methods of the node and the tree.
        # the methods are called again each time new socket is added.
        # if group node has sockets with identifiers which are not the same as identifiers of group tree sockets
        # then when first node will be added to the group tree (or any other changes in the group tree)
        # it will cause replacing of all sockets with wrong identifiers in the group node.
        # clearing and adding sockets of Group input and Group output nodes
        # immediately cause their rebuilding by Blender, so JSON file does not save information about their sockets.
        node.inputs.clear()
        for sock_identifier, raw_struct in inputs:
            with self.logger.add_fail(f"Add socket: {sock_identifier} to node {node.name}"):
                factories.sock(sock_identifier, self.logger, raw_struct).build(node.inputs, factories, imported_data)

        node.outputs.clear()
        for sock_identifier, raw_struct in outputs:
            with self.logger.add_fail(f"Add socket: {sock_identifier} ot node {node.name}"):
                factories.sock(sock_identifier, self.logger, raw_struct).build(node.outputs, factories, imported_data)

        if hasattr(node, 'load_from_json'):
            with self.logger.add_fail("Setting advance node properties",
                                      f'Tree: {node.id_data.name}, Node: {node.name}'):
                node.load_from_json(self._struct, self.version)

    def read(self):
        """Reads node attributes from node structure, returns (attr_name, value)"""
        with self.logger.add_fail("Reading node attributes"):
            attrs_struct = self._struct["attributes"]
            attributes = self.read_collection(attrs_struct)

        with self.logger.add_fail("Reading node properties"):
            props_struct = self._struct["properties"]
            properties = self.read_collection(props_struct)

        with self.logger.add_fail("Reading input sockets"):
            input_struct = self._struct["inputs"]
            inputs = self.read_collection(input_struct)

        with self.logger.add_fail("Reading output sockets"):
            output_struct = self._struct["outputs"]
            outputs = self.read_collection(output_struct)

        return attributes, properties, inputs, outputs

    def read_bl_type(self):
        return self._struct['bl_idname']


class SocketStruct(Struct):
    type = StrTypes.SOCK

    def __init__(self, identifier, logger: FailsLog, structure: dict = None):
        # socket names can't be used here because sockets can have the same names (unlike trees or nodes)
        default_struct = {
            "bl_idname": "",
            "name": "",
            "tree": "",  # util information for group nodes about the name of their node tree
            "attributes": dict(),
            "properties": dict(),
        }
        self.identifier = identifier
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, socket, factories, dependencies):
        self._struct['bl_idname'] = socket.bl_idname
        self._struct['name'] = socket.name
        if hasattr(socket.node, 'node_tree'):
            self._struct['tree'] = socket.node.node_tree.name
        else:
            del self._struct['tree']
        self._struct['attributes']['hide'] = socket.hide

        for prop_name in socket.keys():
            prop = BPYProperty(socket, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:
                    self._struct["properties"][prop.name] = raw_struct

        return self._struct

    def build(self, sockets, factories, imported_structs):
        name, group_tree_name, attributes, properties = self.read()

        # check whether the socket is of group tree
        if group_tree_name is not None:
            # identifier of the socket should be always the same as identifier of the interface socket of the group tree
            # otherwise it will be recreated by Blender update system and its links (and properties?) will be lost
            new_node_tree_name = imported_structs[StrTypes.TREE, '', group_tree_name]
            identifier = imported_structs[StrTypes.INTERFACE, new_node_tree_name, self.identifier]
        else:
            identifier = self.identifier

        # create the socket in the method because identifier is hidden is shown only inside the class
        socket = sockets.new(self.read_bl_type(), name, identifier=identifier)

        for attr_name, attr_value in attributes:
            with self.logger.add_fail(
                    "Setting socket attribute",  # socket.node can be None sometimes 0_o
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(socket, factories, imported_structs)

        for prop_name, prop_value in properties:
            with self.logger.add_fail(  # I think when socket is just created socket.node is None due Blender limitation
                    "Setting socket property",
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, prop: {prop_name}'):
                factories.prop(prop_name, self.logger, prop_value).build(socket, factories, imported_structs)

    def read(self):
        with self.logger.add_fail("Reading socket attributes"):
            attrs_struct = self._struct["attributes"]
            attributes = self.read_collection(attrs_struct)
            name = self._struct['name']
            tree = self._struct.get('tree')

        with self.logger.add_fail("Reading socket properties"):
            props_struct = self._struct["properties"]
            properties = self.read_collection(props_struct)

        return name, tree, attributes, properties

    def read_bl_type(self) -> str:
        with self.logger.add_fail("Reading socket bl_idname"):
            return self._struct['bl_idname']


class InterfaceStruct(Struct):
    type = StrTypes.INTERFACE

    def __init__(self, identifier, logger: FailsLog, structure=None):
        default_struct = {
            "bl_idname": "",
            "name": "",
            "properties": dict(),
            "attributes": dict()
        }
        self.identifier = identifier
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, socket, factories, dependencies):
        self._struct['bl_idname'] = socket.bl_idname
        self._struct['name'] = socket.name

        for prop_name in socket.keys():
            prop = BPYProperty(socket, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                self._struct["properties"][prop.name] = raw_struct

        return self._struct

    def build(self, sockets, factories, imported_structs):
        attributes, properties, name = self.read()

        # create the socket in the method because identifier is hidden is shown only inside the class
        with self.logger.add_fail("Create interface socket"):
            interface_class = bpy.types.NodeSocketInterface.bl_rna_get_subclass_py(self.read_bl_type())
            socket_type = interface_class.bl_socket_idname
            socket = sockets.new(socket_type, name)  # the method gives its own identifier
            imported_structs[self.type, socket.id_data.name, self.identifier] = socket.identifier

        for attr_name, attr_value in attributes:
            with self.logger.add_fail(
                    "Setting interface socket attribute",  # socket.node can be None sometimes 0_o
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(socket, factories, imported_structs)

        for prop_name, prop_value in properties:
            with self.logger.add_fail(
                    "Setting interface socket property",
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, prop: {prop_name}'):
                factories.prop(prop_name, self.logger, prop_value).build(socket, factories, imported_structs)

    def read(self):
        with self.logger.add_fail("Reading interface socket attributes"):
            attrs_struct = self._struct["attributes"]
            attributes = self.read_collection(attrs_struct)
            name = self._struct["name"]

        with self.logger.add_fail("Reading interface socket properties"):
            props_struct = self._struct["properties"]
            properties = self.read_collection(props_struct)

        return attributes, properties, name

    def read_bl_type(self) -> str:
        with self.logger.add_fail("Reading interface socket bl_idname"):
            return self._struct['bl_idname']


class LinkStruct(Struct):
    type = StrTypes.LINK

    def __init__(self, name=None, logger: FailsLog = None, structure: dict = None):
        default_struct = {
            "from_node": "",
            "from_socket": "",  # identifier
            "to_node": "",
            "to_socket": ""}  # identifier
        self._struct = structure or default_struct
        self.logger = logger

    def export(self, link, *_):
        self._struct["from_node"] = link.from_node.name
        self._struct["from_socket"] = link.from_socket.identifier
        if hasattr(link.from_node, 'node_tree'):
            self._struct["from_tree"] = link.from_node.node_tree.name
        elif link.from_node.bl_idname == 'NodeGroupInput':
            self._struct["from_tree"] = link.id_data.name
        self._struct["to_node"] = link.to_node.name
        self._struct["to_socket"] = link.to_socket.identifier
        if hasattr(link.to_node, 'node_tree'):
            self._struct["to_tree"] = link.to_node.node_tree.name
        elif link.to_node.bl_idname == 'NodeGroupOutput':
            self._struct["to_tree"] = link.id_data.name
        return self._struct

    def build(self, tree, factories: StructFactory, imported_structs: OldNewNames):
        from_node_name, from_sock_identifier, from_tree, to_node_name, to_sock_identifier, to_tree = self.read()

        # all nodes can has different names
        from_node_new_name = imported_structs[(factories.node.type, tree.name, from_node_name)]
        to_node_new_name = imported_structs[(factories.node.type, tree.name, to_node_name)]
        from_node = tree.nodes[from_node_new_name]
        to_node = tree.nodes[to_node_new_name]

        # sockets of group_nodes can have different identifiers, unlike other sockets
        # this should certainly be called after nodes get their properties
        if from_tree is not None:
            # new identifiers are bound to group trees where they was born
            new_node_tree_name = imported_structs[StrTypes.TREE, '', from_tree]
            from_sock_identifier = imported_structs[StrTypes.INTERFACE, new_node_tree_name, from_sock_identifier]
        if to_tree is not None:
            new_node_tree_name = imported_structs[StrTypes.TREE, '', to_tree]
            to_sock_identifier = imported_structs[StrTypes.INTERFACE, new_node_tree_name, to_sock_identifier]

        from_socket = self._search_socket(from_node, from_sock_identifier, "OUTPUT")
        to_socket = self._search_socket(to_node, to_sock_identifier, "INPUT")
        if from_socket and to_socket:
            tree.links.new(to_socket, from_socket)

    def read(self):
        with self.logger.add_fail("Read socket data"):
            return self._struct["from_node"], self._struct["from_socket"], self._struct.get("from_tree"), \
                   self._struct["to_node"], self._struct["to_socket"], self._struct.get("to_tree")

    def _search_socket(self, node, socket_identifier: str, sock_type):
        with self.logger.add_fail(f"Building link, trying to find socket {socket_identifier}"):
            for sock in node.inputs if sock_type == "INPUT" else node.outputs:
                if sock.identifier == socket_identifier:
                    return sock
            raise LookupError


class PropertyStruct(Struct):
    type = StrTypes.PROP

    def __init__(self, name: str, logger: FailsLog, structure: dict = None):
        default_struct = {
            "type": "",
            "value": ""
        }
        self._struct = structure if structure is not None else default_struct
        self.name = name
        self.logger = logger

    def export(self, prop: BPYProperty, _, dependencies):
        """It can return just value like float, bool etc or a structure"""
        if prop.is_valid and prop.is_to_save:
            if prop.type == 'COLLECTION':
                return self._handle_collection_prop(prop, dependencies)
            if prop.type == 'POINTER':
                # skip empty and unsupported pointers
                if prop.value is not None and StrTypes.is_supported_block(prop.pointer_type):
                    self._struct["type"] = prop.pointer_type.name
                    self._struct["value"] = prop.value
                    if prop.data_collection is not None:  # skipping nodes
                        dependencies.append((prop.pointer_type, prop.value))
                    return self._struct
                else:
                    return None
            else:
                return prop.value

    def build(self, obj, factories: StructFactory, imported_structs: OldNewNames):
        with self.logger.add_fail("Assigning value", f"Name: {self.name}"):
            prop = BPYProperty(obj, self.name)

            # this is structure (pointer property)
            if isinstance(self._struct, dict):
                pointer_type, old_obj_name = self.read()
                if pointer_type == BPYPointers.NODE:
                    new_name = imported_structs[(StrTypes.get_type(pointer_type), obj.id_data.name, old_obj_name)]
                    # this should work in case obj is a node or socket
                    # but in other cases probably extra information should be kept in the property structure
                    data_block = obj.id_data.nodes[new_name]
                else:
                    new_name = imported_structs[(StrTypes.get_type(pointer_type), '', old_obj_name)]
                    data_block = pointer_type.collection[new_name]
                setattr(obj, self.name, data_block)

            # this is property
            elif prop.is_valid:
                prop.value = self._struct

            # this is attribute
            else:
                setattr(obj, self.name, self._struct)

    def read(self) -> Tuple[BPYPointers, str]:
        with self.logger.add_fail(f"Reading property (value): {self.name}"):
            pointer_type = BPYPointers[self._struct["type"]]
            old_obj_name = self._struct["value"]
            return pointer_type, old_obj_name

    def _handle_collection_prop(self, col_prop, dependencies):
        collection = []
        for item in col_prop.collection_to_list():
            item_props = dict()
            for prop in item:
                raw_struct = PropertyStruct(prop.name, self.logger).export(prop, None, dependencies)
                if raw_struct is not None:
                    item_props[prop.name] = raw_struct 
            collection.append(item_props)
        return collection


class OldNewNames:  # todo can't this be regular dictionary?
    """This class should solve problem of old new names, when created object with one name get another one"""
    Old, New, Owner = str, str, str

    def __init__(self):
        self._old_new_names: Dict[Tuple[StrTypes, OldNewNames.Owner, OldNewNames.Old], OldNewNames.New] = dict()

    def __contains__(self, type_old_name: Tuple[StrTypes, OldNewNames.Owner, OldNewNames.Old]):
        return type_old_name in self._old_new_names

    def __getitem__(self, type_old_name: Tuple[StrTypes, OldNewNames.Owner, OldNewNames.Old]):
        return self._old_new_names[type_old_name]

    def __setitem__(self, type_old_name: Tuple[StrTypes, OldNewNames.Owner, OldNewNames.Old], name: OldNewNames.New):
        self._old_new_names[type_old_name] = name


def _ordered_links(tree) -> Generator[bpy.types.NodeLink]:
    """Returns all links in whole tree where links always are going in order from top input socket to bottom"""
    for node in tree.nodes:
        for input_socket in node.inputs:
            for link in input_socket.links:
                yield link
