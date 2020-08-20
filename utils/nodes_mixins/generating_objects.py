# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import cycle
from typing import List

import bpy

from sverchok.utils.handle_blender_data import correct_collection_length


class SvViewerMeshObjectList(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)

    def ensure_links_to_objects(self, data_block, name: str):
        """Add to obj field data blocks with given name, if necessary"""
        if not self.obj:
            # it looks like it means only that the property group item was created newly
            self.obj = bpy.data.objects.new(name=name, object_data=data_block)
        try:
            bpy.context.scene.collection.objects.link(self.obj)
        except RuntimeError:
            # then the object already added, it looks like more faster way to ensure object is in the scene
            pass

    def check_object_name(self, name: str) -> None:
        """If base name of an object was changed names of all instances also should be changed"""
        real_name = self.obj.name.rsplit('.', 1)[0]
        if real_name != name:
            self.obj.name = name


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

    def regenerate_objects(self, object_names: List[str], data_blocks):
        """
        It will generate new or remove old objects, number of generated objects will be equal to given data_blocks
        Object_names list can contain one name. In this case Blender will add suffix to next objects (.001, .002,...)
        :param data_blocks: any supported by property group data blocks ([bpy.types.Mesh])
        :param object_names: usually equal to name of data block
        :param data_blocks: for now it is support only be bpy.types.Mesh
        """
        correct_collection_length(self.object_data, len(data_blocks))
        prop_group: SvViewerMeshObjectList
        for prop_group, data_block, name in zip(self.object_data, data_blocks, cycle(object_names)):
            prop_group.ensure_links_to_objects(data_block, name)
            prop_group.check_object_name(name)

    def draw_object_properties(self, layout):
        """Should be used for adding update, hide, select, render objects properties"""
        col = layout.column(align=True)
        row = col.row(align=True)
        row.column().prop(self, 'is_active', toggle=True)
        row.prop(self, 'show_objects', toggle=True, text='',
                 icon=f"RESTRICT_VIEW_{'OFF' if self.show_objects else 'ON'}")
        row.prop(self, 'selectable_objects', toggle=True, text='',
                 icon=f"RESTRICT_SELECT_{'OFF' if self.selectable_objects else 'ON'}")
        row.prop(self, 'render_objects', toggle=True, text='',
                 icon=f"RESTRICT_RENDER_{'OFF' if self.render_objects else 'ON'}")


register, unregister = bpy.utils.register_classes_factory([SvViewerMeshObjectList])
