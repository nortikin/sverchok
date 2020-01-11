# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from sverchok.data_structure import updateNode

"""
Usage:

    importing like so:

        from sverchok.utils.sv_collection_helper import (
            group_state_update_handler,
            to_collection, clear_collection
        )

    the node you add this to must implement " self.get_collection_name() "
    something like

        def get_collection_name(self):
            return self.custom_collection_name or self.basedata_name

    also add this property to your node for setting grouping On/Off

        grouping: BoolProperty(default=False, update=group_state_update_handler)

    and somewhere inside your process function

        if self.grouping:
            to_collection(self, objs)

"""


def group_state_update_handler(node, context):
    """
    since this is technically a scene/admin code controlling heirarchy, pressing
    the button should result in assymetric behaviour depending on the new state of
    "self.grouping".

    + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
    | state | desired behaviour                                             |
    + ----- + --------------------------------------------------------------+
    | True  | add all objects associated with the node to the collection    |
    + ----- + --------------------------------------------------------------+
    | False | remove collection, if present, and association with object    |
    + - - - + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
    
    """
    if node.grouping:
        updateNode(node, context)
    else:
        with node.sv_throttle_tree_update():
            clear_collection(node)

def to_collection(node, objs):
    collections = bpy.data.collections
    named = node.get_collection_name()

    # alias collection, or generate new collection and alias that
    collection = collections.get(named)
    if not collection:
        collection = collections.new(named)
        bpy.context.scene.collection.children.link(collection)

    for obj in objs:
        if obj.name not in collection.objects:
            collection.objects.link(obj)

def clear_collection(node):
    collections = bpy.data.collections
    named = node.get_collection_name()
    
    # alias collection, or generate new collection and alias that
    collection = collections.get(named)
    if not collection:
        # seems the collection is already gone, this is a no op
        return
    else:
        collections.remove(collection)
