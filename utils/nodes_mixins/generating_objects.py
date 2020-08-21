# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle
from typing import List

import bpy

from sverchok.utils.handle_blender_data import correct_collection_length, delete_data_block


class SvViewerMeshObjectList(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)

    # Object have not information about in which collection it is located
    # Keep here information about collection for performance reasons
    # Now object can be only in on collection
    collection: bpy.props.PointerProperty(type=bpy.types.Collection)

    def ensure_object(self, data_block, name: str, object_template: bpy.types.Object = None):
        """Add object if it does not exist, if object_template is given new object will be copied from it"""
        if not self.obj:
            # it looks like it means only that the property group item was created newly
            if object_template:
                self.obj = object_template.copy()
                self.obj.data = data_block
            else:
                self.obj = bpy.data.objects.new(name=name, object_data=data_block)
        else:
            # in case if data block was changed
            self.obj.data = data_block

    def ensure_link_to_collection(self, collection: bpy.types.Collection = None):
        """Links object to scene or given collection, unlink from previous collection"""
        try:
            if collection:
                collection.objects.link(self.obj)
            else:
                # default collection
                bpy.context.scene.collection.objects.link(self.obj)
        except RuntimeError:
            # then the object already added, it looks like more faster way to ensure object is in the scene
            pass

        if self.collection != collection:
            # new collection was given, object should be removed from previous one
            if self.collection is None:
                # it means that it is scene default collection
                # from other hand if item only was created it also will be None but object is not in any collection yet
                try:
                    bpy.context.scene.collection.objects.unlink(self.obj)
                except RuntimeError:
                    pass
            else:
                self.collection.objects.unlink(self.obj)

            self.collection = collection

    def check_object_name(self, name: str) -> None:
        """If base name of an object was changed names of all instances also should be changed"""
        real_name = self.obj.name.rsplit('.', 1)[0]
        if real_name != name:
            self.obj.name = name

    def recreate_object(self, object_template: bpy.types.Object = None):
        """
        Object will be replaced by new object recreated from scratch or copied from given object_template if given
        Previous object will be removed, data block remains unchanged
        """
        # in case recreated object should have a chance to get the same name of previous object
        # previous object should be deleted first
        data_block = self.obj.data
        obj_name = self.obj.name
        bpy.data.objects.remove(self.obj)
        if object_template:
            new_obj = object_template.copy()
            new_obj.data = data_block
        else:
            new_obj = bpy.data.objects.new(name=obj_name, object_data=data_block)
        self.obj = new_obj

    def remove(self):
        """Should be called before removing item"""
        if self.obj:
            delete_data_block(self.obj)


class BlenderObjects:
    """Should be used for generating list of objects"""
    object_data: bpy.props.CollectionProperty(type=SvViewerMeshObjectList)

    show_objects: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: [setattr(prop.obj, 'hide_viewport', False if s.show_objects else True)
                             for prop in s.object_data])

    selectable_objects: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: [setattr(prop.obj, 'hide_select', False if s.selectable_objects else True)
                             for prop in s.object_data])

    render_objects: bpy.props.BoolProperty(
        default=True,
        update=lambda s, c: [setattr(prop.obj, 'hide_render', False if s.render_objects else True)
                             for prop in s.object_data])

    def regenerate_objects(self,
                           object_names: List[str],
                           data_blocks,
                           collections: List[bpy.types.Collection] = None,
                           object_template: List[bpy.types.Object] = None):
        """
        It will generate new or remove old objects, number of generated objects will be equal to given data_blocks
        Object_names list can contain one name. In this case Blender will add suffix to next objects (.001, .002,...)
        :param object_template: optionally, object which properties should be grabbed for instanced object
        :param collections: objects will be putted into collections if given, only one in list can be given
        :param data_blocks: nearly any data blocks - mesh, curves, lights ...
        :param object_names: usually equal to name of data block
        :param data_blocks: for now it is support only be bpy.types.Mesh
        """
        correct_collection_length(self.object_data, len(data_blocks))
        prop_group: SvViewerMeshObjectList
        input_data = zip(self.object_data, data_blocks, cycle(object_names), cycle(collections), cycle(object_template))
        for prop_group, data_block, name, collection, template in input_data:
            prop_group.ensure_object(data_block, name, template)
            prop_group.ensure_link_to_collection(collection)
            prop_group.check_object_name(name)

    def draw_object_properties(self, layout):
        """Should be used for adding hide, select, render objects properties"""
        layout.prop(self, 'show_objects', toggle=True, text='',
                    icon=f"RESTRICT_VIEW_{'OFF' if self.show_objects else 'ON'}")
        layout.prop(self, 'selectable_objects', toggle=True, text='',
                    icon=f"RESTRICT_SELECT_{'OFF' if self.selectable_objects else 'ON'}")
        layout.prop(self, 'render_objects', toggle=True, text='',
                    icon=f"RESTRICT_RENDER_{'OFF' if self.render_objects else 'ON'}")


register, unregister = bpy.utils.register_classes_factory([SvViewerMeshObjectList])
