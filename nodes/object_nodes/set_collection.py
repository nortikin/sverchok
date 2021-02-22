# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from sverchok.data_structure import repeat_last, updateNode

from sverchok.node_tree import SverchCustomTreeNode


class SvSetCollection(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: collection

    Assign object to a collection
    """

    bl_idname = 'SvSetCollection'
    bl_label = 'Set collection'
    bl_icon = 'OUTLINER_COLLECTION'

    collection: bpy.props.PointerProperty(type=bpy.types.Collection, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('SvObjectSocket', 'Collection').prop_name = 'collection'
        self.outputs.new('SvObjectSocket', 'Object')

    def process(self):
        objects = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        collections = self.inputs['Collection'].sv_get(deepcopy=False, default=[])
        collections = [] if collections == [None] else collections

        if not objects:
            self.outputs['Object'].sv_set([])
            return

        elif not collections:
            self.outputs['Object'].sv_set(objects)
            return

        for obj, collection in zip(objects, repeat_last(collections)):
            for previous_col in obj.users_collection:  # it takes O(n) collections
                previous_col.objects.unlink(obj)
            collection.objects.link(obj)
        self.outputs['Object'].sv_set(objects)


register, unregister = bpy.utils.register_classes_factory([SvSetCollection])
