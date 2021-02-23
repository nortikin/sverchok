# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from __future__ import annotations

from enum import Enum
from functools import singledispatch
from itertools import chain
from typing import Any, List, Union

import bpy


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
    return [ng for ng in bpy.data.node_groups if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}]


# ~~~~ encapsulation Blender objects ~~~~


class BPYNode:
    """Wrapping around ordinary node for extracting some its information"""
    def __init__(self, node):
        self.data = node

    @property
    def properties(self) -> List[BPYProperty]:
        """Iterator over all node properties"""
        node_properties = self.data.bl_rna.__annotations__ if hasattr(self.data.bl_rna, '__annotations__') else []
        return [BPYProperty(self.data, prop_name) for prop_name in node_properties]


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
            if pointer.type.bl_rna == bl_rna:
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
