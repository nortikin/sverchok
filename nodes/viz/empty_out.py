# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id
import sverchok.core.base_nodes as base_nodes


class SvEmptyOutNode(bpy.types.Node, SverchCustomTreeNode, base_nodes.OutputNode):

    """
    Triggers: empty
    Tooltip: generate a single empty from a matrix
    
    """

    bl_idname = 'SvEmptyOutNode'
    bl_label = 'Empty out'
    bl_icon = 'OUTLINER_DATA_EMPTY'

    def rename_empty(self, context):
        empty = self.find_empty()
        if empty:
            empty.name = self.empty_name
            self.label = empty.name

    @property
    def is_active_output(self) -> bool:
        return True

    empty_name: StringProperty(
        default='Sv empty', name="Base name",
        description="Base name of empty",
        update=rename_empty)

    auto_remove: BoolProperty(
        default=True, description="Remove on node delete",
        name="Auto delete")

    empty_ref_name: StringProperty(default='')

    def create_empty(self):
        
        n_id = node_id(self)

        collection = bpy.context.collection
        objects = bpy.data.objects
        empty = objects.new(self.empty_name, None)
        collection.objects.link(empty)
        empty["SVERCHOK_REF"] = n_id
        self.empty_ref_name = empty.name
        return empty

    def sv_init(self, context):
        self.create_empty()
        self.inputs.new('SvMatrixSocket', "Matrix")
        self.outputs.new('SvObjectSocket', "Objects")

    def find_empty(self):
        n_id = node_id(self)

        def check_empty(obj):
            """ Check that it is the correct empty """
            if obj.type == 'EMPTY':
                return "SVERCHOK_REF" in obj and obj["SVERCHOK_REF"] == n_id
            return False

        objects = bpy.data.objects
        if self.empty_ref_name in objects:
            obj = objects[self.empty_ref_name]
            if check_empty(obj):
                return obj
        for obj in objects:
            if check_empty(obj):
                self.empty_ref_name = obj.name
                return obj
        return None

    def draw_buttons(self, context, layout):
        layout.label(text="Base name")
        row = layout.row()
        row.scale_y = 1.1
        row.prop(self, "empty_name", text="")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "auto_remove")

    def process(self):
        empty = self.find_empty()
        if not empty:
            empty = self.create_empty()
            print("created new empty")

        mat = self.inputs['Matrix'].sv_get([Matrix()])[0]
        self.label = empty.name
        empty.matrix_world = mat
        
        self.outputs['Objects'].sv_set([empty])

    def sv_copy(self, node):
        self.n_id = ''
        empty = self.create_empty()
        self.label = empty.name

    def sv_free(self):
        if self.auto_remove:
            empty = self.find_empty()
            if empty:
                collection = bpy.context.collection
                objects = bpy.data.objects
                try:
                    collection.objects.unlink(empty)
                    objects.remove(empty)
                except:
                    print(f"{self.name} failed to remove empty")


def register():
    bpy.utils.register_class(SvEmptyOutNode)


def unregister():
    bpy.utils.unregister_class(SvEmptyOutNode)
