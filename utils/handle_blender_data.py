# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from functools import singledispatch

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

    try:
        del_object(data_block)
    except ReferenceError:
        # looks like already was deleted
        pass


def get_sv_trees():
    return [ng for ng in bpy.data.node_groups if ng.bl_idname in {'SverchCustomTreeType', 'SverchGroupTreeType'}]
