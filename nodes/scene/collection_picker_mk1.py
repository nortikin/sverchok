# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode
from bpy.props import BoolProperty;

# pylint: disable=w0613
# pylint: disable=c0111
# pylint: disable=c0103

class SvCollectionPicker(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):

    """
    Triggers: SvCollectionPicker
    Tooltip:

    A short description for reader of node code
    """

    bl_idname = 'SvCollectionPicker'
    bl_label = 'Collection Picker'
    bl_icon = 'GROUP'

    def find_collections(self, object):
        return True

    collection: bpy.props.PointerProperty(
        name="collection name", poll=find_collections, type=bpy.types.Collection, update=updateNode)

    sort_object: BoolProperty(
        name="Sort Objects", description="Sort objects by name",
        default=True, update=updateNode)

    show_all_objects: bpy.props.BoolProperty(
        name="Show All Objects", description="Show all objects in the hierarchy of collections",
        default=False, update=updateNode)

    show_only_visible: bpy.props.BoolProperty(
        name="Show Only Visible", description="Show only the visible objects",
        default=False, update=updateNode)

    def sv_init(self, context):
        self.outputs.new("SvObjectSocket", "Objects")

    def draw_buttons(self, context, layout):
        self.draw_animatable_buttons(layout, icon_only=True)
        col = layout.column()
        col.prop_search(self, 'collection', bpy.data, 'collections', text='', icon='GROUP')
        layout.prop(self, "show_all_objects")
        layout.prop(self, "show_only_visible")
        layout.prop(self, "sort_object");

    def process(self):

        found_objects = []
        if self.collection:
            if self.show_all_objects:
                found_objects = bpy.data.collections[self.collection.name].all_objects[:] or []
            else:
                found_objects = self.collection.objects[:] or []

        if self.show_only_visible:
            found_objects = [obj for obj in found_objects if obj.visible_get()]

        if self.sort_object:
            items = [(obj.name, obj) for obj in found_objects]
            items = sorted(items, key=lambda x: x[0], reverse=False)
            found_objects = [item[1] for item in items]

        self.outputs['Objects'].sv_set(found_objects)

classes = [SvCollectionPicker]
register, unregister = bpy.utils.register_classes_factory(classes)

if __name__ == '__main__':
    register()
