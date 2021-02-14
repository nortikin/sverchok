# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BPYPointers
from sverchok.data_structure import fixed_iter, repeat_last, throttle_tree_update, updateNode


class SvBlenderDataPointers(bpy.types.PropertyGroup):

    def update(self, context):
        pass

    __annotations__ = dict()
    for enum in BPYPointers:
        __annotations__[enum.name.lower()] = bpy.props.PointerProperty(
            type=enum.value, update=lambda s, c: updateNode(c.node, c))


class SvAddDataBlock(bpy.types.Operator):
    bl_label = "Add data block"
    bl_idname = "sverchok.add_data_block"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        node = context.node
        node.blender_data.add()
        return {'FINISHED'}


class SvRemoveDataBlock(bpy.types.Operator):
    bl_label = "Remove data block"
    bl_idname = "sverchok.remove_data_block"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    item_index: bpy.props.IntProperty()

    def execute(self, context):
        node = context.node
        node.blender_data.remove(self.item_index)
        updateNode(node, context)
        return {'FINISHED'}


class SvMoveDataBlock(bpy.types.Operator):
    bl_label = "Move data block"
    bl_idname = "sverchok.move_data_block"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    item_index: bpy.props.IntProperty()
    up_direction: bpy.props.BoolProperty()

    def execute(self, context):
        node = context.node
        next_index = self.item_index + (-1 if self.up_direction else 1)
        next_index = min(next_index, len(node.blender_data) - 1)
        next_index = max(0, next_index)
        node.blender_data.move(self.item_index, next_index)
        updateNode(node, context)
        return {'FINISHED'}


class UI_UL_SvBlenderDataList(bpy.types.UIList):
    def draw_item(self, context, layout, node, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        data_type = getattr(BPYPointers, node.data_type.upper())

        row.prop_search(item, node.data_type, bpy.data, data_type.collection_name, text='')

        if node.edit_mode:

            up = row.operator(SvMoveDataBlock.bl_idname, text='', icon='TRIA_UP')
            up.item_index = index
            up.up_direction = True

            down = row.operator(SvMoveDataBlock.bl_idname, text='', icon='TRIA_DOWN')
            down.item_index = index
            down.up_direction = False

            remove = row.operator(SvRemoveDataBlock.bl_idname, text='', icon='REMOVE')
            remove.item_index = index

    def draw_filter(self, context, layout):
        pass


class SvBlenderDataListNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: list
    Tooltip:
    """
    bl_idname = 'SvBlenderDataListNode'
    bl_label = 'Blender data'
    bl_icon = 'ALIGN_TOP'

    data_type: bpy.props.EnumProperty(items=[(e.name.lower(), e.name, '') for e in BPYPointers], name='Type',
                                      update=updateNode)
    edit_mode: bpy.props.BoolProperty(name='Edit list')
    blender_data: bpy.props.CollectionProperty(type=SvBlenderDataPointers)
    selected: bpy.props.IntProperty()

    def sv_init(self, context):
        self.outputs.new('SvObjectSocket', 'Object')  # todo change label?
        self.blender_data.add()

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'data_type')
        row = col.row(align=True)
        row.prop(self, 'edit_mode')
        row.operator(SvAddDataBlock.bl_idname, text='+')
        layout.template_list(UI_UL_SvBlenderDataList.__name__, "blender_data", self, "blender_data", self, "selected")

    def process(self):
        self.outputs['Object'].sv_set(
            [getattr(p, self.data_type) for p in self.blender_data if getattr(p, self.data_type)])


classes = [
    SvBlenderDataPointers,
    SvAddDataBlock, SvRemoveDataBlock, SvMoveDataBlock,  # operators
    UI_UL_SvBlenderDataList,
    SvBlenderDataListNode]


register, unregister = bpy.utils.register_classes_factory(classes)
