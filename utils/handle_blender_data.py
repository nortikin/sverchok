# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from collections.abc import Iterable
from enum import Enum
from functools import singledispatch, wraps, lru_cache, cached_property
from itertools import chain
from typing import Any, List, Union, TYPE_CHECKING, Optional

import bpy
from bpy.types import NodeInputs, NodeOutputs, NodeSocket

from sverchok.data_structure import fixed_iter

if TYPE_CHECKING:
    from sverchok.core.node_group import SvGroupTree
    from sverchok.node_tree import SverchCustomTree


# ~~~~ collection property functions ~~~~~


def correct_collection_length(collection: bpy.types.bpy_prop_collection, length: int) -> None:
    """
    It takes collection property and add or remove its items so it will be equal to given length
    If item has method `remove` it will be called before its deleting
    """
    if len(collection) < length:
        for i in range(len(collection), length):
            collection.add()
    elif len(collection) > length:
        for i in range(len(collection) - 1, length - 1, -1):
            try:
                collection[i].remove_data()
            except AttributeError:
                pass
            collection.remove(i)


# ~~~~ Blender collections functions ~~~~~


def pick_create_object(obj_name: str, data_block):
    """Find object with given name, if does not exist will create new object with given data bloc"""
    block = bpy.data.objects.get(obj_name)
    if not block:
        block = bpy.data.objects.new(name=obj_name, object_data=data_block)
    return block


def pick_create_data_block(collection: bpy.types.bpy_prop_collection, block_name: str):
    """
    Will find data block with given name in given collection (bpy.data.mesh, bpy.data.materials ,...)
    Don't use with objects collection
    If block does not exist new one will be created
     """
    block = collection.get(block_name)
    if not block:
        block = collection.new(name=block_name)
    return block


def delete_data_block(data_block) -> None:
    """
    It will delete such data like objects, meshes, materials
    It won't rise any error if give block does not exist in file anymore
    """
    @singledispatch
    def del_object(bl_obj) -> None:
        raise TypeError(f"Such type={type(bl_obj)} is not supported")

    @del_object.register
    def _(bl_obj: bpy.types.Object):
        bpy.data.objects.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Mesh):
        bpy.data.meshes.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Material):
        bpy.data.materials.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Light):
        bpy.data.lights.remove(bl_obj)

    @del_object.register
    def _(bl_obj: bpy.types.Curve):
        bpy.data.curves.remove(bl_obj)

    try:
        del_object(data_block)
    except ReferenceError:
        # looks like already was deleted
        pass


def get_sv_trees():
    return [ng for ng in bpy.data.node_groups if ng.bl_idname in {'SverchCustomTreeType',}]


# ~~~~ encapsulation Blender objects ~~~~

# In general it's still arbitrary set of functionality (like module which fully consists with functions)
# But here the functions are combine with data which they handle


class BlDomains(Enum):
    # don't change the order - new items add to the end
    POINT = 'Point'
    EDGE = 'Edge'
    FACE = 'Face'
    CORNER = 'Face Corner'

    # It does not have sense to include these attributes because there is no API
    # for generating instances and applying attributes to a curve.
    # CURVE = 'Spline'
    # INSTANCE = 'Instance'


class BlObject:
    def __init__(self, obj):
        self._obj: bpy.types.Object = obj

    def set_attribute(self, values, attr_name, domain='POINT', value_type='FLOAT'):
        obj = self._obj
        attr = obj.data.attributes.get(attr_name)
        if attr is None:
            attr = obj.data.attributes.new(attr_name, value_type, domain)
        elif attr.data_type != value_type or attr.domain != domain:
            obj.data.attributes.remove(attr)
            attr = obj.data.attributes.new(attr_name, value_type, domain)

        if domain == 'POINT':
            amount = len(obj.data.vertices)
        elif domain == 'EDGE':
            amount = len(obj.data.edges)
        elif domain == 'CORNER':
            amount = len(obj.data.loops)
        elif domain == 'FACE':
            amount = len(obj.data.polygons)
        else:
            raise TypeError(f'Unsupported domain {domain}')

        if value_type in ['FLOAT', 'INT', 'BOOLEAN']:
            data = list(fixed_iter(values, amount))
        elif value_type in ['FLOAT_VECTOR', 'FLOAT_COLOR']:
            data = [co for v in fixed_iter(values, amount) for co in v]
        elif value_type == 'FLOAT2':
            data = [co for v in fixed_iter(values, amount) for co in v[:2]]
        else:
            raise TypeError(f'Unsupported type {value_type}')

        if value_type in ["FLOAT", "INT", "BOOLEAN"]:
            attr.data.foreach_set("value", data)
        elif value_type in ["FLOAT_VECTOR", "FLOAT2"]:
            attr.data.foreach_set("vector", data)
        else:
            attr.data.foreach_set("color", data)

        # attr.data.update()


class BlModifier:
    def __init__(self, modifier):
        self._mod: bpy.types.Modifier = modifier
        self.gn_tree: Optional[BlTree] = None  # cache for performance

    @property
    def node_group(self):
        return getattr(self._mod, 'node_group', None)

    @node_group.setter
    def node_group(self, node_group):
        self._mod.node_group = node_group

    def get_property(self, name):
        return getattr(self._mod, name)

    def set_property(self, name, value):
        setattr(self._mod, name, value)

    def get_tree_prop(self, name):
        return self._mod[name]

    def set_tree_prop(self, name, value):
        """Good for coping properties from one modifier to another"""
        self._mod[name] = value

    def set_tree_data(self, name, data, domain='POINT'):
        """Transfer py data to node modifier tree"""

        # transfer single value
        if not isinstance(data, (list, tuple)):
            data = [data]
        if not self.gn_tree.is_field(name) and len(data) != 1:
            data = data[:1]
        if len(data) == 1:
            value = data[0]
            self._mod[f"{name}_use_attribute"] = 0
            if isinstance(value, (list, tuple)):  # list of single vertex
                # for some reason node modifier can't apply python sequences directly
                for i, v in enumerate(value):
                    self._mod[name][i] = v
            else:
                sock = self.gn_tree.inputs[name]
                if sock.type in {'INT', 'BOOLEAN'}:
                    value = int(value)
                elif sock.type == 'VALUE':
                    value = float(value)
                elif sock.type == 'STRING':
                    value = str(value)
                self._mod[name] = value

        # transfer field
        else:
            self._mod[f"{name}_use_attribute"] = 1
            self._mod[f"{name}_attribute_name"] = name
            obj = BlObject(self._mod.id_data)
            sock = self.gn_tree.inputs[name]
            if sock.type in {'INT', 'BOOLEAN'} and not isinstance(data[0], int):
                data = [int(i) for i in data]
            bl_sock = BlSocket(sock)
            obj.set_attribute(data, name, domain, value_type=bl_sock.attribute_type)

    def remove(self):
        obj = self._mod.id_data
        obj.modifiers.remove(self._mod)
        self._mod = None

    @property
    def type(self) -> str:
        return self._mod.type

    def __eq__(self, other):
        if isinstance(other, BlModifier):
            # check type
            if self.type != other.type:
                return False

            # check properties
            for prop in (p for p in self._mod.bl_rna.properties if not p.is_readonly):
                if other.get_property(prop.identifier) != self.get_property(prop.identifier):
                    return False

            # check tree properties
            if self._mod.type == 'NODES' and self._mod.node_group:
                for tree_inp in self._mod.node_group.inputs[1:]:
                    prop_name = tree_inp.identifier
                    if self.get_tree_prop(prop_name) != other.get_tree_prop(prop_name):
                        return False
                    use_name = f"{prop_name}_use_attribute"
                    if self.get_tree_prop(use_name) != other.get_tree_prop(use_name):
                        return False
                    attr_name = f"{prop_name}_attribute_name"
                    if self.get_tree_prop(attr_name) != other.get_tree_prop(attr_name):
                        return False
                for tree_out in self._mod.node_group.outputs[1:]:
                    prop_name = f"{tree_out.identifier}_attribute_name"
                    if self.get_tree_prop(prop_name) != other.get_tree_prop(prop_name):
                        return False

            return True
        else:
            return NotImplemented


class BlTrees:
    """Wrapping around Blender tree, use with care
    it can crash if other containers are modified a lot
    https://docs.blender.org/api/current/info_gotcha.html#help-my-script-crashes-blender
    All this is True and about Blender class itself"""

    MAIN_TREE_ID = 'SverchCustomTreeType'
    GROUP_ID = 'SvGroupTree'

    def __init__(self, node_groups=None):
        self._trees = node_groups

    @classmethod
    def is_main_tree(cls, tree):
        return tree.bl_idname == cls.MAIN_TREE_ID

    @property
    def sv_trees(self) -> Iterable[Union[SverchCustomTree, SvGroupTree]]:
        """All Sverchok trees in a file or in given set of trees"""
        trees = self._trees or bpy.data.node_groups
        return (t for t in trees if t.bl_idname in [self.MAIN_TREE_ID, self.GROUP_ID])

    @property
    def sv_main_trees(self) -> Iterable[SverchCustomTree]:
        """All main Sverchok trees in a file or in given set of trees"""
        trees = self._trees or bpy.data.node_groups
        return (t for t in trees if t.bl_idname == self.MAIN_TREE_ID)

    @property
    def sv_group_trees(self) -> Iterable[SvGroupTree]:
        """All Sverchok group trees"""
        trees = self._trees or bpy.data.node_groups
        return (t for t in trees if t.bl_idname == self.GROUP_ID)


class BlTree:
    def __init__(self, tree):
        self._tree = tree
        self.inputs = {s.identifier: s for s in tree.inputs}
        self.outputs = {s.identifier: s for s in tree.outputs}

        self.is_field = lru_cache(self._is_field)  # for performance

    @cached_property
    def group_input(self):
        for node in self._tree.nodes:
            if node.bl_idname == 'NodeGroupInput':
                return node
        return None

    def _is_field(self, input_socket_identifier):
        """Check whether input tree socket expects field (diamond socket)"""
        if (group := self.group_input) is None:
            raise LookupError(f'Group input node is required '
                              f'which is not found in "{self._tree.name}" tree')
        sock = BlSocket.from_identifier(group.outputs, input_socket_identifier)
        return sock.display_shape == 'DIAMOND'


class BlNode:
    """Wrapping around ordinary node for extracting some its information"""
    DEBUG_NODES_IDS = {'SvDebugPrintNode', 'SvStethoscopeNode'}  # can be added as Mix-in class

    def __init__(self, node):
        self.data = node

    @property
    def properties(self) -> List[BPYProperty]:
        """Iterator over all node properties"""
        node_properties = self.data.bl_rna.__annotations__ if hasattr(self.data.bl_rna, '__annotations__') else []
        return [BPYProperty(self.data, prop_name) for prop_name in node_properties]

    @property
    def is_debug_node(self) -> bool:
        """Nodes which print sockets content"""
        return self.base_idname in self.DEBUG_NODES_IDS

    @property
    def base_idname(self) -> str:
        """SvStethoscopeNodeMK2 -> SvStethoscopeNode
        it won't parse more tricky variants like SvStethoscopeMK2Node which I saw exists"""
        id_name, _, version = self.data.bl_idname.partition('MK')
        try:
            int(version)
        except ValueError:
            return self.data.bl_idname
        return id_name


class BlSockets:
    def __init__(self, sockets: Union[NodeInputs, NodeOutputs]):
        self._sockets = sockets

    def copy_sockets(self, sockets_from: Iterable):
        """Copy sockets from one collection to another. Also, it can be used
        to refresh `to` collection to be equal to `from` collection and in this
        case only new socket will be added and old one removed.
        It can copy properties:
        sv socket -> sv socket
        sv interface socket -> sv socket
        """
        sockets_to = self._sockets
        # remove sockets which are not presented in from collection
        identifiers_from = {s.identifier for s in sockets_from}
        for s_to in sockets_to:
            if s_to.identifier not in identifiers_from:
                sockets_to.remove(s_to)

        # add new sockets
        sock_indexes_to = {s.identifier: i for i, s in enumerate(sockets_to)}
        for s_from in sockets_from:
            if s_from.identifier in sock_indexes_to:
                continue
            id_name = getattr(s_from, 'bl_socket_idname', s_from.bl_idname)
            s_to = sockets_to.new(id_name, s_from.name, identifier=s_from.identifier)
            sock_indexes_to[s_to.identifier] = len(sockets_to) - 1

        # fix existing sockets
        for s_from in sockets_from:
            s_to = sockets_to[sock_indexes_to[s_from.identifier]]
            id_name = getattr(s_from, 'bl_socket_idname', s_from.bl_idname)
            if id_name != s_to.bl_idname:
                s_to = s_to.replace_socket(id_name)

        # fix socket positions
        for new_pos, s_from in enumerate(sockets_from):
            current_pos = sock_indexes_to[s_from.identifier]
            if current_pos != new_pos:
                sockets_to.move(current_pos, new_pos)
                sock_indexes_to = {
                    s.identifier: i for i, s in enumerate(sockets_to)}


class BlSocket:
    _attr_types = {
        'VECTOR': 'FLOAT_VECTOR',
        'VALUE': 'FLOAT',
        'RGBA': 'FLOAT_COLOR',
        'INT': 'INT',
        'BOOLEAN': 'BOOLEAN',
    }

    _sv_types = {
        'VECTOR': 'SvVerticesSocket',
        'VALUE': 'SvStringsSocket',
        'RGBA': 'SvColorSocket',
        'INT': 'SvStringsSocket',
        'STRING': 'SvTextSocket',
        'BOOLEAN': 'SvStringsSocket',
        'OBJECT': 'SvObjectSocket',
        'COLLECTION': 'SvCollectionSocket',
        'MATERIAL': 'SvMaterialSocket',
        'TEXTURE': 'SvTextureSocket',
        'IMAGE': 'SvImageSocket',
    }

    def __init__(self, socket):
        self._sock: bpy.types.NodeSocket = socket

    def copy_properties(self, sv_sock):
        sv_sock.name = self._sock.name

        if sv_sock.bl_idname == 'SvStringsSocket':
            if self._sock.type == 'VALUE':
                sv_sock.default_property_type = 'float'
            elif self._sock.type in {'INT', 'BOOLEAN'}:
                sv_sock.default_property_type = 'int'
            else:
                return  # There is no default property for such type
            if sv_sock.default_property == 0:  # was unchanged by user
                sv_sock.default_property = self._sock.default_value
                sv_sock.use_prop = True

        elif sv_sock.bl_idname == 'SvVerticesSocket':
            if sv_sock.default_property[:] == (0, 0, 0):  # was unchanged by user
                sv_sock.default_property = self._sock.default_value
                sv_sock.use_prop = True

        elif sv_sock.bl_idname == 'SvObjectSocket':
            if sv_sock.default_property is None:  # was unchanged by user
                sv_sock.object_ref_pointer = self._sock.default_value
                sv_sock.use_prop = True

        elif hasattr(sv_sock, 'default_property'):
            sv_default = BPYProperty(sv_sock, 'default_property').default_value
            if isinstance(sv_sock.default_property, bpy.types.bpy_prop_array):
                current = sv_sock.default_property[:]
            else:
                current = sv_sock.default_property
            if sv_default != current:
                return  # the value was already changed by user
            sv_sock.default_property = self._sock.default_value
            sv_sock.use_prop = True

    @classmethod
    def from_identifier(cls, sockets, identifier):
        for s in sockets:
            if s.identifier == identifier:
                return cls(s)
        raise LookupError(f"Socket with {identifier=} was not found")

    @property
    def attribute_type(self):
        return self._attr_types[self._sock.type]

    @property
    def sverchok_type(self):
        if (sv_type := self._sv_types.get(self._sock.type)) is None:
            return 'SvStringsSocket'
        return sv_type

    @property
    def display_shape(self):
        return self._sock.display_shape


class BPYProperty:
    """Wrapper over any property to get access to advance information"""
    def __init__(self, data, prop_name: str):
        """
        Data block can be any blender data like, node, trees, sockets
        Use with caution as far it keeps straight reference to Blender object
        """
        self.name = prop_name
        self._data = data

    @property
    def is_valid(self) -> bool:
        """
        If data does not have property with given name property is invalid
        It can be so that data.keys() or data.items() can give names of properties which are not in data class any more
        Such properties cab consider as deprecated
        """
        return self.name in self._data.bl_rna.properties

    @property
    def value(self) -> Any:
        """Returns value of the property in Python format, list of dicts for collection, tuple for array"""
        if not self.is_valid:
            raise TypeError(f'Can not read "value" of invalid property "{self.name}"')
        elif self.is_array_like:
            return tuple(getattr(self._data, self.name))
        elif self.type == 'COLLECTION':
            return self._extract_collection_values()
        elif self.type == 'POINTER':  # it simply returns name of data block or None
            data_block = getattr(self._data, self.name)
            return data_block.name if data_block is not None else None
        else:
            return getattr(self._data, self.name)

    @value.setter
    def value(self, value):
        """Apply values in python format to the property"""
        if not self.is_valid:
            raise TypeError(f'Can not read "value" of invalid property "{self.name}"')
        if self.type == 'COLLECTION':
            self._set_collection_values(value)
        elif self.type == 'POINTER' and isinstance(value, str):
            setattr(self._data, self.name, self.data_collection.get(value))
        elif self.type == 'ENUM' and self.is_array_like:
            setattr(self._data, self.name, set(value))
        else:
            setattr(self._data, self.name, value)

    @property
    def type(self) -> str:
        """Type of property: STRING, FLOAT, INT, POINTER, COLLECTION"""
        if not self.is_valid:
            raise TypeError(f'Can not read "type" of invalid property "{self.name}"')
        return self._data.bl_rna.properties[self.name].type

    @property
    def pointer_type(self) -> BPYPointers:
        if self.type != 'POINTER':
            raise TypeError(f'This property is only valid for "POINTER" types, {self.type} type is given')
        return BPYPointers.get_type(self._data.bl_rna)

    @property
    def default_value(self) -> Any:
        """Returns default value, None for pointers, list of dicts of default values for collections"""
        if not self.is_valid:
            raise TypeError(f'Can not read "default_value" of invalid property "{self.name}"')
        elif self.type == 'COLLECTION':
            return self._extract_collection_values(default_value=True)
        elif self.is_array_like:
            if self.type == 'ENUM':
                return tuple(self._data.bl_rna.properties[self.name].default_flag)
            else:
                return tuple(self._data.bl_rna.properties[self.name].default_array)
        elif self.type == 'POINTER':
            return None
        else:
            return self._data.bl_rna.properties[self.name].default

    @property
    def pointer_type(self) -> BPYPointers:
        """It returns subtypes of POINTER type"""
        if self.type != 'POINTER':
            raise TypeError(f'Only POINTER property type has `pointer_type` attribute, "{self.type}" given')
        return BPYPointers.get_type(self._data.bl_rna.properties[self.name].fixed_type)

    @property
    def data_collection(self):
        """For pointer properties only, if pointer type is MESH it will return bpy.data.meshes"""
        return self.pointer_type.collection

    @property
    def is_to_save(self) -> bool:
        """False if property has option BoolProperty(options={'SKIP_SAVE'})"""
        if not self.is_valid:
            raise TypeError(f'Can not read "is_to_save" of invalid property "{self.name}"')
        return not self._data.bl_rna.properties[self.name].is_skip_save

    @property
    def is_array_like(self) -> bool:
        """True for VectorArray, FloatArray, IntArray, Enum with enum flag"""
        if not self.is_valid:
            raise TypeError(f'Can not read "is_array_like" of invalid property "{self.name}"')
        if self.type in {'BOOLEAN', 'FLOAT', 'INT'}:
            return self._data.bl_rna.properties[self.name].is_array
        elif self.type == 'ENUM':
            # Enum can return set of values, array like
            return self._data.bl_rna.properties[self.name].is_enum_flag
        else:
            # other properties does not have is_array attribute
            return False

    def unset(self):
        """Assign default value to the property"""
        self._data.property_unset(self.name)

    def filter_collection_values(self, skip_default=True, skip_save=True):
        """Convert data of collection property into python format with skipping certain properties"""
        if self.type != 'COLLECTION':
            raise TypeError(f'Method supported only "collection" types, "{self.type}" was given')
        if not self.is_valid:
            raise TypeError(f'Can not read "non default collection values" of invalid property "{self.name}"')
        items = []
        for item in getattr(self._data, self.name):
            item_props = {}

            # in some nodes collections are getting just PropertyGroup type instead of its subclasses
            # PropertyGroup itself does not have any properties
            item_properties = item.__annotations__ if hasattr(item, '__annotations__') else []
            for prop_name in chain(['name'], item_properties):  # item.items() will return only changed values
                prop = BPYProperty(item, prop_name)
                if not prop.is_valid:
                    continue
                if skip_save and not prop.is_to_save:
                    continue
                if prop.type != 'COLLECTION':
                    if skip_default and prop.default_value == prop.value:
                        continue
                    item_props[prop.name] = prop.value
                else:
                    item_props[prop.name] = prop.filter_collection_values(skip_default, skip_save)
            items.append(item_props)
        return items

    def collection_to_list(self):
        """Returns data structure like this [[p1, p2, p3], [p4, p5, p6]]
        in this example the collection has two items, each item has 3 properties"""
        if self.type != 'COLLECTION':
            raise TypeError(f'Method supported only "collection" types, "{self.type}" was given')
        if not self.is_valid:
            raise TypeError(f'Can not read "non default collection values" of invalid property "{self.name}"')

        collection = []
        for item in getattr(self._data, self.name):
            prop_list = []
            # in some nodes collections are getting just PropertyGroup type instead of its subclasses
            # PropertyGroup itself does not have any properties
            item_properties = item.__annotations__ if hasattr(item, '__annotations__') else []
            for prop_name in chain(['name'], item_properties):  # item.items() will return only changed values
                prop = BPYProperty(item, prop_name)
                prop_list.append(prop)
            collection.append(prop_list)
        return collection

    def _extract_collection_values(self, default_value: bool = False):
        """returns something like this: [{"name": "", "my_prop": 1.0}, {"name": "", "my_prop": 2.0}, ...]"""
        items = []
        for item in getattr(self._data, self.name):
            item_props = {}

            # in some nodes collections are getting just PropertyGroup type instead of its subclasses
            # PropertyGroup itself does not have any properties
            item_properties = item.__annotations__ if hasattr(item, '__annotations__') else []
            for prop_name in chain(['name'], item_properties):  # item.items() will return only changed values
                prop = BPYProperty(item, prop_name)
                if prop.is_valid:
                    item_props[prop.name] = prop.default_value if default_value else prop.value
            items.append(item_props)
        return items

    def _set_collection_values(self, value: List[dict]):
        """Assign Python data to collection property"""
        collection = getattr(self._data, self.name)
        for item_index, item_values in enumerate(value):
            # Some collections can be empty, in this case they should be expanded to be able to get new values
            if item_index == len(collection):
                item = collection.add()
            else:
                item = collection[item_index]
            for prop_name, prop_value in item_values.items():
                prop = BPYProperty(item, prop_name)
                if prop.is_valid:
                    prop.value = prop_value


class BPYPointers(Enum):
    """
    Pointer types which are used in Sverchok
    New properties should be added with updating collection property
    """
    # pointer name = type of data
    OBJECT = bpy.types.Object
    MESH = bpy.types.Mesh
    NODE_TREE = bpy.types.NodeTree
    NODE = bpy.types.Node  # there is pointers to nodes in Blender like node.parent property
    MATERIAL = bpy.types.Material
    COLLECTION = bpy.types.Collection
    TEXT = bpy.types.Text
    LIGHT = bpy.types.Light
    IMAGE = bpy.types.Image
    TEXTURE = bpy.types.Texture
    VECTOR_FONT = bpy.types.VectorFont
    GREASE_PENCIL = bpy.types.GreasePencil

    @property
    def collection(self):
        """Map of pointer type and its collection"""
        collections = {
            BPYPointers.OBJECT: bpy.data.objects,
            BPYPointers.MESH: bpy.data.meshes,
            BPYPointers.NODE_TREE: bpy.data.node_groups,
            BPYPointers.NODE: None,
            BPYPointers.MATERIAL:  bpy.data.materials,
            BPYPointers.COLLECTION: bpy.data.collections,
            BPYPointers.TEXT: bpy.data.texts,
            BPYPointers.LIGHT: bpy.data.lights,
            BPYPointers.IMAGE: bpy.data.images,
            BPYPointers.TEXTURE: bpy.data.textures,
            BPYPointers.VECTOR_FONT: bpy.data.curves,
            BPYPointers.GREASE_PENCIL: bpy.data.grease_pencils
        }
        return collections[self]

    @property
    def type(self):
        """Return Blender type of the pointer"""
        return self.value

    @classmethod
    def get_type(cls, bl_rna) -> Union[BPYPointers, None]:
        """Return Python pointer corresponding to given Blender pointer class (bpy.types.Mesh.bl_rna)"""
        for pointer in BPYPointers:
            if pointer.type.bl_rna == bl_rna or pointer.type.bl_rna == bl_rna.base:
                return pointer
        raise TypeError(f'Type: "{bl_rna}" was not found in: {[t.type.bl_rna for t in BPYPointers]}')


def get_func_and_args(prop):
    """
    usage:   
        - formerly
        prop_func, prop_args = some_class.__annotations__[some_prop_name]
        - new
        prop_to_decompose = some_class.__annotations__[some_prop_name]
        prop_func, prop_args = get_func_and_args(prop_to_decompose)
        
    """
    if hasattr(prop, "keywords"):
        return prop.function, prop.keywords
    else:
        return prop


def keep_enum_reference(enum_func):
    """remember you have to keep enum strings somewhere in py,
    else they get freed and Blender references invalid memory!
    This decorator should be used for these purposes"""
    saved_items = dict()

    @wraps(enum_func)
    def wrapper(node, context):
        nonlocal saved_items
        items = enum_func(node, context)
        saved_items[node.node_id] = items
        return saved_items[node.node_id]
    wrapper.keep_ref = True  # just for tests
    return wrapper
