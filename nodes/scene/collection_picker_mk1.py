# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

# pylint: disable=w0613
# pylint: disable=c0111
# pylint: disable=c0103

class SvCollectionPicker(bpy.types.Node, SverchCustomTreeNode):
    
    """
    Triggers: SvCollectionPicker
    Tooltip: 
    
    A short description for reader of node code
    """

    bl_idname = 'SvCollectionPicker'
    bl_label = 'Collection Picker'
    bl_icon = 'GROUP'

    properties_to_skip_iojson = ['collection']

    def find_collections(self, object):
        return True

    def on_updateNode(self, context):
        self.named_collection = self.collection.name

    named_collection: bpy.props.StringProperty(name="collection name", update=updateNode)
    collection: bpy.props.PointerProperty(
        name="collection name", poll=find_collections, type=bpy.types.PropertyGroup, update=on_updateNode)

    def sv_init(self, context):
        self.outputs.new("SvObjectSocket", "Objects")

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop_search(self, 'named_collection', bpy.data, 'collections', text='', icon='GROUP')

    def process(self):

        found_objects = []
        if self.collection:
            found = bpy.data.collections.get(self.named_collection.strip())
            found_objects = found.objects[:] if found else []

        self.outputs['Objects'].sv_set(found_objects)



# SvCollectionPickerSettings
classes = [SvCollectionPicker]
register, unregister = bpy.utils.register_classes_factory(classes)
