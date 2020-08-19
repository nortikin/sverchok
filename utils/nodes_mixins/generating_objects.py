# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle
from typing import List

import bpy

from sverchok.utils.handle_blender_data import pick_create_object, correct_collection_length


class SvViewerMeshObjectList(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)

    # supported data blocks:
    mesh: bpy.props.PointerProperty(type=bpy.types.Mesh)
    # add other types if necessary

    def ensure_links_to_objects(self, data_block, name: str):
        """Add to obj and mesh fields data blocks with given name, if necessary"""
        if isinstance(data_block, bpy.types.Mesh):
            self.mesh = data_block
        else:
            raise TypeError(f"Unsupported type={type(data_block)} of given data block")
        if not self.obj:
            # objects can be deleted by users, so if property is exist it does not mean that it has an object
            self.obj = pick_create_object(name, data_block)
        try:
            bpy.context.scene.collection.objects.link(self.obj)
        except RuntimeError:
            # then the object already added, it looks like more faster way to ensure object is in the scene
            pass


class BlenderObjects:
    """Should be used for generating list of objects"""
    objects: bpy.props.CollectionProperty(type=SvViewerMeshObjectList)

    def regenerate_objects(self, object_names: List[str], data_blocks):
        """
        It will generate new or remove old objects
        :param data_blocks: any supported by property group data blocks ([bpy.types.Mesh])
        :param object_names: usually equal to name of data block
        :param data_block: for now it is support only be bpy.types.Mesh
        """
        correct_collection_length(self.objects, len(object_names))
        for prop_group, data_block, name in zip(self.objects, cycle(data_blocks), object_names):
            prop_group.ensure_links_to_objects(data_block, name)


register, unregister = bpy.utils.register_classes_factory([SvViewerMeshObjectList])
