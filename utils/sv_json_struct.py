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
from sverchok.utils.handle_blender_data import BPYPointers, BPYProperty
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.core import BPY_NodeTreeInterfaceSocket

if TYPE_CHECKING:
    from sverchok.utils.sv_json_import import FailsLog


"""
Terminology:

Structure - anything more complex than just a value,
for example pointer type can keep several values like its type and name.
Also structures can include other ones.
Similar to Blender struct object
https://docs.blender.org/api/current/bpy.types.bpy_struct.html#bpy.types.bpy_struct

Data block ro block - this is top structures in their hierarchy,
for example a node tree is a data block but all inner structures (nodes, links, sockets) are not.
https://docs.blender.org/api/current/bpy.types.ID.html#bpy.types.ID.copy
"""


class StructFactory:
    """This is collection of struct classes
    The idea is to put all structs into the class which should be used during import/export of a tree
    other structures can use other ones to include their in the process
    For example there could be several classes which can build a node differently
    before starting of the serialization process we should choose which node struct to use
    then a tree structure can use the node structure that we chose"""

    # it's possible to use version factory in the code to make the code more specific
    # if struct_factories.link.version == 0.2:
    def __init__(self, factories: List[Type[Struct]]):
        self._factory_names = {
            StrTypes.TREE: 'tree',
            StrTypes.NODE: 'node',
            StrTypes.SOCK: 'sock',
            StrTypes.INTERFACE: 'interface',
            StrTypes.LINK: 'link',
            StrTypes.PROP: 'prop',
            StrTypes.MATERIAL: 'material',
            StrTypes.COLLECTION: 'collection',
            StrTypes.IMAGE: 'image',
            StrTypes.TEXTURE: 'texture',
        }

        self.tree: Optional[Type[Struct]] = None
        self.node: Optional[Type[Struct]] = None
        self.sock: Optional[Type[Struct]] = None
        self.interface: Optional[Type[Struct]] = None
        self.link: Optional[Type[Struct]] = None
        self.prop: Optional[Type[Struct]] = None
        self.material: Optional[Type[Struct]] = None
        self.collection: Optional[Type[Struct]] = None
        self.image: Optional[Type[Struct]] = None
        self.texture: Optional[Type[Struct]] = None

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
    def grab_from_module(cls) -> StructFactory:
        """Grab all factories in the module"""
        factory_classes = []
        module_classes = inspect.getmembers(sys.modules[__name__],
                                            lambda member: inspect.isclass(member) and member.__module__ == __name__)
        for class_name, module_class in module_classes:
            if hasattr(module_class, 'type') and isinstance(module_class.type, StrTypes):
                factory_classes.append(module_class)
        return cls(factory_classes)


class StrTypes(Enum):
    """All structures should have their type (except file structures =D)
    the type helps to identify their purpose
    for example for exporting nodes only structures with NODE type can be used"""

    TREE = auto()
    NODE = auto()
    SOCK = auto()
    INTERFACE = auto()  # node groups sockets
    LINK = auto()
    PROP = auto()
    MATERIAL = auto()
    COLLECTION = auto()
    IMAGE = auto()
    TEXTURE = auto()

    def get_bpy_pointer(self) -> BPYPointers:
        mapping = {
            StrTypes.TREE: BPYPointers.NODE_TREE,
            StrTypes.NODE: BPYPointers.NODE,
            StrTypes.MATERIAL: BPYPointers.MATERIAL,
            StrTypes.COLLECTION: BPYPointers.COLLECTION,
            StrTypes.IMAGE: BPYPointers.IMAGE,
            StrTypes.TEXTURE: BPYPointers.TEXTURE,
        }
        if self not in mapping:
            raise TypeError(f'Given StrType: {self} is not a data block')
        return mapping[self]

    @classmethod
    def get_type(cls, block_type: BPYPointers) -> StrTypes:
        mapping = {
            BPYPointers.NODE_TREE: StrTypes.TREE,
            BPYPointers.NODE: StrTypes.NODE,
            BPYPointers.MATERIAL: StrTypes.MATERIAL,
            BPYPointers.COLLECTION: StrTypes.COLLECTION,
            BPYPointers.IMAGE: StrTypes.IMAGE,
            BPYPointers.TEXTURE: StrTypes.TEXTURE,
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


OldName, NewName, OwnerName = str, str, str
OldNewNames = Dict[Tuple[StrTypes, OwnerName, OldName], NewName]


class Struct(ABC):
    """All structures should include a dictionary with description of the structure organization,
    methods for exporting and importing related to their purpose data
    It's possible to override version inside children classes but
    in this case its version should be kept in its dictionary
    And the way to figure it out which structure should be used is not implemented for such case.
    So if new version is required it should be changed in this class
    this information can be used in a file structure to find appropriate other structures

    Example:
    class FileStruct:
        def build(tree):
            if self._struct["export_version"] < 1.1:
                factories.node = NodeStruct
            else:
                factories.node = NewNodeStruct

    Or version can be used like this:
    class NodeStruct:
        def build(node, factories, imported):
            if self.version < 1.1:
                node.load_from_json(self._struct["advance_properties"]
            else:
                pass
    but in this case FileStruct should implement this - Struct.version = self._struct["export_version"] (hmm... )
    """
    # I was trying to make API of all abstract method the same between child classes but it looks it's not possible
    # for example to build a node we can send to method a tree where the node should be duilded
    version = 1.0
    type: StrTypes = None  # should be overridden

    @abstractmethod
    def __init__(self, name: Optional[str], logger: FailsLog, struct: dict = None):
        ...

    @abstractmethod
    def export(self, data_block, struct_factories: StructFactory, dependencies: List[Tuple[BPYPointers, str]]) -> dict:
        ...

    @abstractmethod
    def build(self, obj, factories: StructFactory, imported_structs: OldNewNames):
        ...

    def read_bl_type(self) -> str:
        """typically should return bl_idname of the structure"""
        return None


class FileStruct(Struct):
    """Export/import of all or only select nodes of a tree"""
    def __init__(self, name=None, logger: FailsLog = None, struct: dict = None):
        default_struct = {
            "export_version": str(self.version),
            "main_tree": {
                "nodes": dict(),
                "links": []
            }
        }
        self._struct: Dict[str, Any] = struct or default_struct
        self.logger: FailsLog = logger

    def export(self):
        # I would expect this method import the whole Sverchok data in a file
        raise NotImplementedError

    def export_tree(self, tree, use_selection=False):
        if tree.bl_idname != 'SverchCustomTreeType':
            raise TypeError(f'Only exporting main trees is supported, {tree.bl_label} is given')

        struct_factories = StructFactory.grab_from_module()  # todo to args?
        dependencies: List[Tuple[BPYPointers, str]] = []

        # export main tree first
        self._export_nodes(tree, struct_factories, dependencies, use_selection)

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

    def _export_nodes(self, tree, factories, dependencies, use_selection=False):
        """Structure of main tree"""
        nodes = tree.nodes if not use_selection else [n for n in tree.nodes if n.select]
        for node in nodes:
            raw_struct = factories.node(node.name, self.logger).export(node, factories, dependencies)
            self._struct["main_tree"]["nodes"][node.name] = raw_struct

        input_node_names = {node.name for node in nodes}
        for link in _ordered_links(tree):
            if link.from_node.name in input_node_names and link.to_node.name in input_node_names:
                raw_struct = factories.link(None, self.logger).export(link, factories, dependencies)
                self._struct["main_tree"]["links"].append(raw_struct)

    def build(self, *_):
        raise NotImplementedError

    def build_into_tree(self, tree):
        # it looks that recursive import should be avoided by any cost, it's too difficult to pass data
        # luckily it's possible to create all data block first
        # and then they will be available for assigning to pointer properties
        # with tree data blocks it can be a beat trickier,
        # all trees should be created and only after that field with content

        factories = StructFactory.grab_from_module()
        imported_structs: OldNewNames = dict()
        data_blocks = self._data_blocks_reader()

        # initialize trees and build other data block types
        trees_to_build = []
        for struct_type, block_name, raw_struct in data_blocks:
            with self.logger.add_fail("Initialize data block", f"Type: {struct_type.name}, Name: {block_name}"):
                if struct_type == StrTypes.TREE:
                    tree_struct = factories.tree(block_name, self.logger, raw_struct)
                    data_block = bpy.data.node_groups.new(block_name, tree_struct.read_bl_type())
                    # interface should be created before building all trees
                    tree_struct.build_interface(data_block, factories, imported_structs)
                    imported_structs[(struct_type, '', block_name)] = data_block.name
                    trees_to_build.append(tree_struct)
                else:
                    block_struct = factories.get_factory(struct_type)(block_name, self.logger, raw_struct)
                    block_struct.build(factories, imported_structs)

        # build main tree nodes
        self._build_nodes(tree, factories, imported_structs)

        # build group trees
        for tree_struct in trees_to_build:
            with self.logger.add_fail("Build node group", f"Name: {tree_struct.name}"):
                new_name = imported_structs[StrTypes.TREE, '', tree_struct.name]
                data_block = bpy.data.node_groups[new_name]
                tree_struct.build(data_block, factories, imported_structs)

        # mark old nodes
        group_trees = []
        for tree_name in [t.name for t in trees_to_build]:
            new_name = imported_structs[StrTypes.TREE, '', tree_name]
            gr_tree = bpy.data.node_groups[new_name]
            group_trees.append(gr_tree)
        for node in chain(tree.nodes, *(t.nodes for t in group_trees)):
            if old_nodes.is_old(node):
                old_nodes.mark_old(node)

    def _build_nodes(self, tree, factories, imported_structs):
        """Build nodes of the main tree, other dependencies should be already initialized"""
        with tree.init_tree():
            # first all nodes should be created without applying their inner data
            # because some nodes can have `parent` property which points into another node
            node_structs = []
            for node_name, raw_structure in self._struct["main_tree"]["nodes"].items():
                with self.logger.add_fail("Init node (main tree)", f"Name: {node_name}"):
                    node_struct = factories.node(node_name, self.logger, raw_structure)

                    # register optional node classes
                    if old_nodes.is_old(node_struct.read_bl_type()):
                        old_nodes.register_old(node_struct.read_bl_type())

                    # add node an save its new name
                    node = tree.nodes.new(node_struct.read_bl_type())
                    node.name = node_name
                    imported_structs[(StrTypes.NODE, tree.name, node_name)] = node.name
                    node_structs.append(node_struct)

            for node_struct in node_structs:
                with self.logger.add_fail("Build node (main tree)", f"Name {node_struct.name}"):
                    new_name = imported_structs[(StrTypes.NODE, tree.name, node_struct.name)]
                    node = tree.nodes[new_name]
                    node_struct.build(node, factories, imported_structs)

            for raw_struct in self._struct["main_tree"]["links"]:
                with self.logger.add_fail("Build link (main tree)", f"Struct: {raw_struct}"):
                    factories.link(None, self.logger, raw_struct).build(tree, factories, imported_structs)

    def _data_blocks_reader(self):
        struct_type: StrTypes
        for struct_type_name, structures in self._struct.items():
            if struct_type_name in (it.name for it in StrTypes):
                with self.logger.add_fail("Reading data blocks", f"Type: {struct_type_name}"):
                    for block_name, block_struct in structures.items():
                        yield StrTypes[struct_type_name], block_name, block_struct


class NodePresetFileStruct(Struct):
    """Export/import one node properties and sockets"""
    def __init__(self, name=None, logger=None, structure=None):
        default_struct = {
            "export_version": str(self.version),
            "node": dict(),
        }
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, node):
        factories = StructFactory.grab_from_module()
        dependencies: List[Tuple[BPYPointers, str]] = []

        struct = factories.node(node.name, self.logger)
        self._struct["node"][node.name] = struct.export(node, factories, dependencies)

        while dependencies:
            block_type, block_name = dependencies.pop()
            struct_type = StrTypes.get_type(block_type)
            if struct_type.name not in self._struct:
                self._struct[struct_type.name] = dict()
            if block_name not in self._struct[struct_type.name]:
                factory = factories.get_factory(struct_type)
                data_block = block_type.collection[block_name]
                structure = factory(block_name, self.logger).export(data_block, factories, dependencies)
                self._struct[struct_type.name][block_name] = structure

        return self._struct

    def build(self, node):
        tree = node.id_data
        with tree.init_tree():

            factories = StructFactory.grab_from_module()
            imported_structs: OldNewNames = dict()
            trees_to_build = []

            # initialize trees and build other data block types
            for struct_type, block_name, raw_struct in self._data_blocks_reader():
                if struct_type == StrTypes.TREE:  # in case it was group node
                    tree_struct = factories.tree(block_name, self.logger, raw_struct)
                    data_block = bpy.data.node_groups.new(block_name, tree_struct.read_bl_type())
                    tree_struct.build_interface(data_block, factories, imported_structs)
                    imported_structs[(struct_type, '', block_name)] = data_block.name
                    trees_to_build.append(tree_struct)
                else:
                    # all data block except node trees
                    block_struct = factories.get_factory(struct_type)(block_name, self.logger, raw_struct)
                    block_struct.build(factories, imported_structs)

            for tree_struct in trees_to_build:
                new_name = imported_structs[StrTypes.TREE, '', tree_struct.name]
                data_block = bpy.data.node_groups[new_name]
                tree_struct.build(data_block, factories, imported_structs)

            # now it's time to update the node, we have to save its links first because they will be removed
            links = []
            for link in _ordered_links(tree):
                if link.from_node.name == node.name or link.to_node.name == node.name:
                    link_struct = factories.link(None, self.logger)
                    link_struct.export(link, factories, [])
                    links.append(link_struct)

            # recreate node from scratch, this need for resetting all its properties to default
            node_name, raw_struct = next(iter(self._struct["node"].items()))
            node_struct = factories.node(node_name, self.logger, raw_struct)
            location = node.location[:]  # without copying it looks like gives straight references to memory
            tree.nodes.remove(node)
            node = tree.nodes.new(node_struct.read_bl_type())
            node.name = node_name
            node.select = True
            tree.nodes.active = node
            imported_structs[StrTypes.NODE, tree.name, node_name] = node.name

            # all nodes should be as if they was imported with new names before linking
            for node in tree.nodes:
                imported_structs[StrTypes.NODE, tree.name, node.name] = node.name

            # in case the node is inside group tree it should be also imported with its sockets
            # to be able connect links to group out/in nodes
            imported_structs[StrTypes.TREE, '', tree.name] = tree.name
            for sock in chain(tree.inputs, tree.outputs):
                imported_structs[StrTypes.INTERFACE, tree.name, sock.identifier] = sock.identifier

            # import the node and rebuild the links if possible
            node_struct.build(node, factories, imported_structs)
            node.location = location  # return to initial position, it has to be after node build
            for link_struct in links:
                try:
                    link_struct.build(tree, factories, imported_structs)
                except LookupError:  # the node seems has different sockets
                    pass
            # how it should work with group node links is not clear
            # because they are bound to identifiers of the group tree input outputs
            # for now breaking links will be considered as desired behaviour

        node.process_node(bpy.context)
        return node

    def _data_blocks_reader(self):
        struct_type: StrTypes
        for struct_type_name, structures in self._struct.items():
            if struct_type_name in (it.name for it in StrTypes):
                with self.logger.add_fail("Reading data blocks", f"Type: {struct_type_name}"):
                    for block_name, block_struct in structures.items():
                        yield StrTypes[struct_type_name], block_name, block_struct


class TreeStruct(Struct):
    """Export/import node, links, tree properties, tree sockets"""
    type = StrTypes.TREE

    def __init__(self, name: str, logger: FailsLog, structure: dict = None):
        default_structure = {
            "nodes": dict(),
            "links": [],
            "inputs": dict(),
            "outputs": dict(),
            "properties": dict(),
            "bl_idname": "",
        }
        self._struct = structure or default_structure
        self.name = name
        self.logger = logger

    def export(self, tree, factories: StructFactory, dependencies) -> dict:
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

        for prop_name in tree.keys():
            prop = BPYProperty(tree, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:
                    self._struct["properties"][prop.name] = raw_struct

        self._struct["bl_idname"] = tree.bl_idname

        if not self._struct["properties"]:
            del self._struct["properties"]

        return self._struct

    def build(self, tree, factories: StructFactory, imported_structs: OldNewNames):
        """Reads and generates nodes, links, dependent data blocks"""
        with tree.init_tree():
            # first all nodes should be created without applying their inner data
            # because some nodes can have `parent` property which points into another node
            node_structs = []
            for node_name, raw_structure in self._struct["nodes"].items():
                with self.logger.add_fail("Init node", f"Tree: {tree.name}, Node: {node_name}"):
                    node_struct = factories.node(node_name, self.logger, raw_structure)

                    # register optional node classes
                    if old_nodes.is_old(node_struct.read_bl_type()):
                        old_nodes.register_old(node_struct.read_bl_type())

                    # add node an save its new name
                    node = tree.nodes.new(node_struct.read_bl_type())
                    node.name = node_name
                    imported_structs[(StrTypes.NODE, tree.name, node_name)] = node.name
                    node_structs.append(node_struct)

            for node_struct in node_structs:
                with self.logger.add_fail("Build node", f"Tree: {tree.name}, Node: {node_struct.name}"):
                    new_name = imported_structs[(StrTypes.NODE, tree.name, node_struct.name)]
                    node = tree.nodes[new_name]
                    node_struct.build(node, factories, imported_structs)

            for raw_struct in self._struct["links"]:
                with self.logger.add_fail("Build link", f"Tree: {tree.name}, Struct: {raw_struct}"):
                    factories.link(None, self.logger, raw_struct).build(tree, factories, imported_structs)

            for prop_name, prop_value in self._struct.get("properties", dict()).items():
                with self.logger.add_fail("Setting tree property", f'Tree: {node.id_data.name}, prop: {prop_name}'):
                    factories.prop(prop_name, self.logger, prop_value).build(tree, factories, imported_structs)

    def build_interface(self, tree, factories, imported_structs):
        for sock_name, raw_struct in self._struct["inputs"].items():
            with self.logger.add_fail("Create tree in socket", f"Tree: {tree.name}, Sock: {sock_name}"):
                factories.interface(sock_name, self.logger, raw_struct).build(tree.inputs, factories, imported_structs)

        for sock_name, raw_struct in self._struct["outputs"].items():
            with self.logger.add_fail("Create tree out socket", f"Tree: {tree.name}, Sock: {sock_name}"):
                factories.interface(sock_name, self.logger, raw_struct).build(tree.outputs, factories, imported_structs)

    def read_bl_type(self):
        return self._struct["bl_idname"]


class NodeStruct(Struct):
    """Export/import node properties, attributes, sockets. 
    It can call save_to_json and load_from_json methods of a node if one has them
    The methods will get empty dictionary for storing advanced properties"""
    type = StrTypes.NODE

    def __init__(self, name: str, logger: FailsLog, structure: dict = None):
        default_structure = {
            "attributes": {
                "location": (0, 0),
                "height": None,
                "width": None,
                "label": '',
                "hide": False,
                "color": (0, 0, 0),
                "use_custom_color": False,
                "parent": None,
            },
            "properties": dict(),
            "advanced_properties": dict(),
            "inputs": dict(),
            "outputs": dict(),
            "bl_idname": ""
        }
        self._struct = structure or default_structure
        self.name = name
        self.logger = logger

    def export(self, node, factories: StructFactory, dependencies) -> dict:
        # add_mandatory_attributes
        self._struct['bl_idname'] = node.bl_idname
        self._struct["attributes"]['location'] = recursive_framed_location_finder(node, node.location[:])

        _set_optional(self._struct["attributes"], 'height', node.height, node.height != 100.0)
        _set_optional(self._struct["attributes"], 'width', node.width, node.width != 140.0)
        _set_optional(self._struct["attributes"], "label", node.label)
        _set_optional(self._struct["attributes"], "hide", node.hide)
        _set_optional(self._struct["attributes"], "use_custom_color", node.use_custom_color)
        _set_optional(self._struct["attributes"], "color", node.color[:], node.use_custom_color)
        if node.parent:  # the node is inside of a frame node
            prop = BPYProperty(node, "parent")
            raw_struct = factories.prop("parent", self.logger).export(prop, factories, dependencies)
            self._struct["attributes"]["parent"] = raw_struct
        else:
            del self._struct["attributes"]["parent"]

        # add non default node properties
        for prop_name in node.keys():
            prop = BPYProperty(node, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:
                    self._struct["properties"][prop.name] = raw_struct

        _set_optional(self._struct, "properties", self._struct["properties"])

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

        _set_optional(self._struct, "inputs", self._struct["inputs"])
        _set_optional(self._struct, "outputs", self._struct["outputs"])

        if hasattr(node, 'save_to_json'):
            node.save_to_json(self._struct["advanced_properties"])

        _set_optional(self._struct, "advanced_properties", self._struct["advanced_properties"])

        return self._struct

    def build(self, node, factories: StructFactory, imported_data: OldNewNames):
        for attr_name, attr_value in self._struct["attributes"].items():
            with self.logger.add_fail("Setting node attribute",
                                      f'Tree: {node.id_data.name}, Node: {node.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(node, factories, imported_data)

        for prop_name, prop_value in self._struct.get("properties", dict()).items():
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
        if node.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}:
            node.inputs.clear()
        for sock_identifier, raw_struct in self._struct.get("inputs", dict()).items():
            with self.logger.add_fail("Add in socket",
                                      f"Tree: {node.id_data.name}, Node {node.name}, Sock: {sock_identifier}"):
                factories.sock(sock_identifier, self.logger, raw_struct).build(node.inputs, factories, imported_data)

        if node.bl_idname not in {'NodeGroupInput', 'NodeGroupOutput'}:
            node.outputs.clear()
        for sock_identifier, raw_struct in self._struct.get("outputs", dict()).items():
            with self.logger.add_fail("Add out socket",
                                      f"Tree: {node.id_data.name}, Node {node.name}, Sock: {sock_identifier}"):
                factories.sock(sock_identifier, self.logger, raw_struct).build(node.outputs, factories, imported_data)

        if hasattr(node, 'load_from_json'):
            with self.logger.add_fail("Setting advance node properties",
                                      f'Tree: {node.id_data.name}, Node: {node.name}'):
                node.load_from_json(self._struct.get("advanced_properties", dict()), self.version)

    def read_bl_type(self):
        return self._struct['bl_idname']


class SocketStruct(Struct):
    """Export/import socket properties, attributes"""
    type = StrTypes.SOCK

    def __init__(self, identifier, logger: FailsLog, structure: dict = None):
        # socket names can't be used here because sockets can have the same names (unlike trees or nodes)
        default_struct = {
            "bl_idname": "",
            "name": "",
            "tree": "",  # util information for group nodes about the name of their node tree
            "attributes": {
                "hide": False,
            },
            "properties": dict(),
        }
        self.identifier = identifier
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, socket, factories, dependencies):
        self._struct['bl_idname'] = socket.bl_idname
        self._struct['name'] = socket.name

        _set_optional(self._struct, 'tree', socket.node.node_tree.name if hasattr(socket.node, 'node_tree') else '')
        _set_optional(self._struct["attributes"], 'hide', socket.hide)
        _set_optional(self._struct, "attributes", self._struct["attributes"])

        for prop_name in socket.keys():
            prop = BPYProperty(socket, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:
                    self._struct["properties"][prop.name] = raw_struct
        _set_optional(self._struct, "properties", self._struct["properties"])

        return self._struct

    def build(self, sockets, factories, imported_structs):
        name = self._struct['name']
        group_tree_name = self._struct.get('tree')

        # check whether the socket is of group tree
        if group_tree_name is not None:
            # identifier of the socket should be always the same as identifier of the interface socket of the group tree
            # otherwise it will be recreated by Blender update system and its links (and properties?) will be lost
            new_node_tree_name = imported_structs[StrTypes.TREE, '', group_tree_name]
            identifier = imported_structs[StrTypes.INTERFACE, new_node_tree_name, self.identifier]
        else:
            identifier = self.identifier

        # create the socket in the method because identifier(name) is hidden is shown only inside the class
        socket = sockets.new(self.read_bl_type(), name, identifier=identifier)

        for attr_name, attr_value in self._struct.get("attributes", dict()).items():
            with self.logger.add_fail(
                    "Setting socket attribute",  # socket.node can be None sometimes 0_o
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(socket, factories, imported_structs)

        for prop_name, prop_value in self._struct.get("properties", dict()).items():
            with self.logger.add_fail(  # I think when socket is just created socket.node is None due Blender limitation
                    "Setting socket property",
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, prop: {prop_name}'):
                factories.prop(prop_name, self.logger, prop_value).build(socket, factories, imported_structs)

    def read_bl_type(self) -> str:
        with self.logger.add_fail("Reading socket bl_idname"):
            return self._struct['bl_idname']


class InterfaceStruct(Struct):
    """Export/import interface socket properties, attributes"""
    type = StrTypes.INTERFACE

    def __init__(self, identifier, logger: FailsLog, structure=None):
        default_struct = {
            "bl_idname": "",
            "name": "",
            "attributes": {
                "hide_value": False,
            },
            "properties": dict(),
        }
        self.identifier = identifier
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, socket, factories, dependencies):
        self._struct['bl_idname'] = socket.bl_idname
        self._struct['name'] = socket.name

        _set_optional(self._struct["attributes"], 'hide_value', socket.hide_value)
        _set_optional(self._struct, "attributes", self._struct["attributes"])

        for prop_name in socket.keys():
            prop = BPYProperty(socket, prop_name)
            if prop.is_valid and prop.is_to_save:
                raw_struct = factories.prop(prop.name, self.logger).export(prop, factories, dependencies)
                if raw_struct is not None:
                    self._struct["properties"][prop.name] = raw_struct
        _set_optional(self._struct, "properties", self._struct["properties"])

        return self._struct

    def build(self, sockets, factories, imported_structs):
        name = self._struct["name"]
        # create the socket in the method because identifier is hidden is shown only inside the class
        interface_class = BPY_NodeTreeInterfaceSocket.bl_rna_get_subclass_py(self.read_bl_type())
        socket_type = interface_class.bl_socket_idname
        socket = sockets.new(socket_type, name)  # the method gives its own identifier
        imported_structs[self.type, socket.id_data.name, self.identifier] = socket.identifier

        for attr_name, attr_value in self._struct.get("attributes", dict()).items():
            with self.logger.add_fail(
                    "Setting interface socket attribute",
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, attr: {attr_name}'):
                factories.prop(attr_name, self.logger, attr_value).build(socket, factories, imported_structs)

        for prop_name, prop_value in self._struct.get("properties", dict()).items():
            with self.logger.add_fail(
                    "Setting interface socket property",
                    f'Tree: {socket.id_data.name}, socket: {socket.name}, prop: {prop_name}'):
                factories.prop(prop_name, self.logger, prop_value).build(socket, factories, imported_structs)

    def read_bl_type(self) -> str:
        with self.logger.add_fail("Reading interface socket bl_idname"):
            return self._struct['bl_idname']


class LinkStruct(Struct):
    """Export/import link relationships"""
    type = StrTypes.LINK

    def __init__(self, name=None, logger: FailsLog = None, structure: dict = None):
        default_struct = {
            "from_node": "",
            "from_socket": "",  # identifier
            "from_tree": "",
            "to_node": "",
            "to_socket": "",   # identifier
            "to_tree": "",
        }
        self._struct = structure or default_struct
        self.logger = logger

    def export(self, link, *_):
        self._struct["from_node"] = link.from_node.name
        self._struct["from_socket"] = link.from_socket.identifier
        if hasattr(link.from_node, 'node_tree'):
            _set_optional(self._struct, 'from_tree', link.from_node.node_tree.name)
        elif link.from_node.bl_idname == 'NodeGroupInput':
            _set_optional(self._struct, "from_tree", link.id_data.name)
        else:
            _set_optional(self._struct, "from_tree", "")
        self._struct["to_node"] = link.to_node.name
        self._struct["to_socket"] = link.to_socket.identifier
        if hasattr(link.to_node, 'node_tree'):
            _set_optional(self._struct, "to_tree", link.to_node.node_tree.name)
        elif link.to_node.bl_idname == 'NodeGroupOutput':
            _set_optional(self._struct, "to_tree", link.id_data.name)
        else:
            _set_optional(self._struct, "to_tree", "")
        return self._struct

    def build(self, tree, factories: StructFactory, imported_structs: OldNewNames):
        from_node_name = self._struct["from_node"]
        from_sock_identifier = self._struct["from_socket"]
        from_tree = self._struct.get("from_tree")
        to_node_name = self._struct["to_node"]
        to_sock_identifier = self._struct["to_socket"]
        to_tree = self._struct.get("to_tree")

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

    def _search_socket(self, node, socket_identifier: str, sock_type):
        with self.logger.add_fail(f"Building link, trying to find socket {socket_identifier}"):
            for sock in node.inputs if sock_type == "INPUT" else node.outputs:
                if sock.identifier == socket_identifier:
                    return sock
            raise LookupError


class PropertyStruct(Struct):
    """Export/import properties. It includes specific about managing of Blender properties
    All properties are supported.
    Structure of the class can be just a value or usual dictionary (in case of a pointer property)"""
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
                return self._export_collection_values(prop, dependencies)
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
                # default values should be persistent per Sverchok releases - no need to save
                if prop.value != prop.default_value:
                    return prop.value
                else:
                    return None

    def build(self, obj, factories: StructFactory, imported_structs: OldNewNames):
        prop = BPYProperty(obj, self.name)

        # this is structure (pointer property)
        if isinstance(self._struct, dict):
            pointer_type = BPYPointers[self._struct["type"]]
            old_obj_name = self._struct["value"]
            if pointer_type == BPYPointers.NODE:
                new_name = imported_structs[(StrTypes.get_type(pointer_type), obj.id_data.name, old_obj_name)]
                # this should work in case obj is a node or socket
                # but in other cases probably extra information should be kept in the property structure
                data_block = obj.id_data.nodes[new_name]
            else:
                new_name = imported_structs[(StrTypes.get_type(pointer_type), '', old_obj_name)]
                data_block = pointer_type.collection[new_name]
            setattr(obj, self.name, data_block)

        # this is collection property
        elif prop.type == 'COLLECTION':
            self._set_collection_values(obj, factories, imported_structs)

        # this is property
        elif prop.is_valid:
            prop.value = self._struct

        # this is attribute
        else:
            setattr(obj, self.name, self._struct)

    def _export_collection_values(self, col_prop, dependencies):
        collection = []
        for item in col_prop.collection_to_list():
            item_props = dict()
            for prop in item:
                raw_struct = PropertyStruct(prop.name, self.logger).export(prop, None, dependencies)
                if raw_struct is not None:
                    item_props[prop.name] = raw_struct 
            collection.append(item_props)
        return collection

    def _set_collection_values(self, obj, factories, imported_structs):
        """Assign Python data to collection property"""
        collection = getattr(obj, self.name)
        # it is possible that collection is not empty in case a node added something into it during initialization
        # but the property always consider the collection property to be empty
        collection.clear()
        for item_index, item_values in enumerate(self._struct):
            # Some collections can be empty, in this case they should be expanded to be able to get new values
            if item_index == len(collection):
                item = collection.add()
            else:
                item = collection[item_index]

            for prop_name, prop_value in item_values.items():
                factories.prop(prop_name, self.logger, prop_value).build(item, factories, imported_structs)


class MaterialStruct(Struct):
    """Default structure for materials. Include only its name for now.
    If a Blender file does not posses the material the empty material will be generated"""
    # this structure can be more complex if we want to save state of the material tree
    type = StrTypes.MATERIAL

    def __init__(self, name, logger=None, structure=None):
        default_struct = {}
        self.name = name
        self.logger = logger
        self._struct = structure or default_struct

    def export(self, mat, factories, dependencies):
        # probably something will be added here in the future
        return self._struct

    def build(self, factories, imported_structs):
        material = bpy.data.materials.get(self.name)
        if material is None:
            material = bpy.data.materials.new(self.name)
        imported_structs[(StrTypes.MATERIAL, '', self.name)] = material.name


class CollectionStruct(Struct):
    """Default structure for collections. It includes only its name for now.
    If a Blender file does not posses the collection the empty collection will be generated"""
    type = StrTypes.COLLECTION

    def __init__(self, name, logger=None, struct=None):
        default_struct = {}
        self.name = name
        self.logger = logger
        self._struct = struct or default_struct

    def export(self, collection, factories, dependencies):
        return self._struct

    def build(self, factories, imported_structs):
        collection = bpy.data.collections.get(self.name)
        if collection is None:
            collection = bpy.data.collections.new(self.name)
            bpy.context.scene.collection.children.link(collection)
        imported_structs[(StrTypes.COLLECTION, '', self.name)] = collection.name


class ImageStruct(Struct):
    """Default image structure. It will only try to find whether the image in a Blender file"""
    type = StrTypes.IMAGE

    def __init__(self, name, logger=None, struct=None):
        default_struct = {}
        self.name = name
        self.logger = logger
        self._struct = struct or default_struct

    def export(self, image, factories, dependencies):
        return self._struct

    def build(self, factories, imported_structs):
        # the file should have the image already
        # it could be convenient if importer could generate empty images if necessary
        image = bpy.data.images.get(self.name)
        if image is not None:
            imported_structs[(StrTypes.IMAGE, '', self.name)] = image.name


class TextureStruct(Struct):
    """Default texture structure. It will try to find existing texture in a Blender file"""
    type = StrTypes.TEXTURE

    def __init__(self, name, logger=None, struct=None):
        default_struct = {}
        self.name = name
        self.logger = logger
        self._struct = struct or default_struct

    def export(self, texture, factories, dependencies):
        return self._struct

    def build(self, factories, imported_structs):
        # it could be convenient if importer could generate empty textures if necessary
        texture = bpy.data.textures.get(self.name)
        if texture is not None:
            imported_structs[(StrTypes.TEXTURE, '', self.name)] = texture.name


def _ordered_links(tree) -> Generator[bpy.types.NodeLink]:
    """Returns all links in whole tree where links always are going in order from top input socket to bottom"""
    for node in tree.nodes:
        for input_socket in node.inputs:
            for link in input_socket.links:
                yield link


def _set_optional(data: dict, key, value, condition=None):
    if condition if condition is not None else value:
        data[key] = value
    else:
        del data[key]
