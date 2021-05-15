# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain, cycle

import bpy
from sverchok.data_structure import updateNode, fixed_iter

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import correct_collection_length


class SvUnlinkFromOtherCollections(bpy.types.Operator):
    bl_idname = "node.sv_unlink_from_other_collections"
    bl_label = "Unlink from other collections"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        col_node = context.node

        for last in col_node.last_objects:
            # unlink from all collections
            for col in chain(bpy.data.collections, [bpy.context.scene.collection]):
                try:
                    col.objects.unlink(last.obj)
                except RuntimeError:
                    pass

            # link to collection of the node
            if last.col:
                last.col.objects.link(last.obj)

        return {'FINISHED'}


class SvObjectsWithCollections(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)  # this can be None if object was deleted
    col: bpy.props.PointerProperty(type=bpy.types.Collection)

    def link(self, obj, col):
        self.obj = obj
        self.col = col

        self._unlike_from_scene()

        try:
            if col is not None:
                col.objects.link(obj)
        except RuntimeError:
            pass

    def unlink(self):
        try:
            if self.col is not None and self.obj is not None:
                self.col.objects.unlink(self.obj)
        except RuntimeError:
            pass

    def _unlike_from_scene(self):
        # the object should each time be unliked from scene collection because Mesh Viewer node link it each time
        # and this looks like most efficient solution I can think of
        try:
            bpy.context.scene.collection.objects.unlink(self.obj)
        except RuntimeError:
            pass


class SvSetCollection(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: collection

    Assign object to a collection
    """

    bl_idname = 'SvSetCollection'
    bl_label = 'Set collection'
    bl_icon = 'OUTLINER_COLLECTION'

    collection: bpy.props.PointerProperty(type=bpy.types.Collection, update=updateNode)
    last_objects: bpy.props.CollectionProperty(type=SvObjectsWithCollections)

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Object')
        self.inputs.new('SvObjectSocket', 'Collection').prop_name = 'collection'
        self.outputs.new('SvObjectSocket', 'Object')

    def sv_copy(self, original):
        # new node new history
        self.last_objects.clear()

    def draw_buttons(self, context, layout):
        layout.operator('node.sv_unlink_from_other_collections', text="Unlink others", icon='UNLINKED')

    def process(self):
        objects = self.inputs['Object'].sv_get(deepcopy=False, default=[])
        collections = self.inputs['Collection'].sv_get(deepcopy=False, default=[])

        # first step is undo previous changes by the node if necessary
        len_last = len(self.last_objects)
        for last, obj, col in zip(self.last_objects, chain(objects, cycle([None])), fixed_iter(collections, len_last)):
            last.unlink()
        correct_collection_length(self.last_objects, len(objects))

        # save and assign new collections
        for last, obj, col in zip(self.last_objects, objects, fixed_iter(collections, len(objects))):
            last.link(obj, col)

        self.outputs['Object'].sv_set(objects)


register, unregister = bpy.utils.register_classes_factory(
    [SvUnlinkFromOtherCollections, SvObjectsWithCollections, SvSetCollection])
