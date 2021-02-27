# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.handle_blender_data import BPYPointers
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode


class SvBlenderDataPointers(bpy.types.PropertyGroup):

    __annotations__ = dict()
    for enum in BPYPointers:
        __annotations__[enum.name.lower()] = bpy.props.PointerProperty(
            type=enum.value, update=lambda s, c: updateNode(c.node, c))


class SvEditDataBlockList(bpy.types.Operator):
    bl_label = "Edit data block list"
    bl_idname = "sverchok.edit_data_block_list"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    operations = ['add', 'remove', 'move_up', 'move_down', 'clear', 'get_selected', 'add_selected']
    operation: bpy.props.EnumProperty(items=[(i, i, '') for i in operations])

    item_index: bpy.props.IntProperty()  # required for some operations

    def execute(self, context):
        node = context.node

        if self.operation == 'add':
            node.blender_data.add()
        elif self.operation == 'remove':
            node.blender_data.remove(self.item_index)
        elif self.operation == 'move_up':
            next_index = max(0, self.item_index - 1)
            node.blender_data.move(self.item_index, next_index)
        elif self.operation == 'move_down':
            next_index = min(self.item_index + 1, len(node.blender_data) - 1)
            node.blender_data.move(self.item_index, next_index)
        elif self.operation == 'clear':
            node.blender_data.clear()
        elif self.operation == 'get_selected':
            node.blender_data.clear()
            self.add_selected(context, node.blender_data)
        elif self.operation == 'add_selected':
            self.add_selected(context, node.blender_data)

        updateNode(node, context)
        return {'FINISHED'}

    @staticmethod
    def add_selected(context, collection):
        # if any bugs then you have probably using depsgraph here
        for obj in context.selected_objects:
            item = collection.add()
            item.object = obj


class SvDataBlockListOptions(bpy.types.Menu):
    bl_idname = "OBJECT_MT_data_block_list_options"
    bl_label = "Options"

    def draw(self, context):
        layout = self.layout
        node = context.node

        op = layout.operator(SvEditDataBlockList.bl_idname, text='Clear the list')
        op.operation = 'clear'

        layout.separator()
        layout.prop(node, 'is_animatable')
        layout.prop(node, 'refresh', toggle=False, icon='FILE_REFRESH')


class UI_UL_SvBlenderDataList(bpy.types.UIList):
    def draw_item(self, context, layout, node, item, icon, active_data, active_propname, index, flt_flag):
        row = layout.row(align=True)
        data_type = getattr(BPYPointers, node.data_type.upper())

        row.prop_search(item, node.data_type, bpy.data, data_type.collection_name, text='')

        if node.edit_mode:

            up = row.operator(SvEditDataBlockList.bl_idname, text='', icon='TRIA_UP')
            up.operation = 'move_up'
            up.item_index = index

            down = row.operator(SvEditDataBlockList.bl_idname, text='', icon='TRIA_DOWN')
            down.operation = 'move_down'
            down.item_index = index

            remove = row.operator(SvEditDataBlockList.bl_idname, text='', icon='REMOVE')
            remove.operation = 'remove'
            remove.item_index = index

    def draw_filter(self, context, layout):
        pass


class SvBlenderDataListNode(SvAnimatableNode, SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: list
    Tooltip:
    """
    bl_idname = 'SvBlenderDataListNode'
    bl_label = 'Blender data list'
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
        if self.data_type == 'object':
            row = col.row(align=True)
            row.label(text='Selected:')
            row.operator(SvEditDataBlockList.bl_idname, text='Get').operation = 'get_selected'
            row.operator(SvEditDataBlockList.bl_idname, text='Add').operation = 'add_selected'
        row = col.row(align=True)
        row.prop(self, 'edit_mode')
        op = row.operator(SvEditDataBlockList.bl_idname, text='+')
        op.operation = 'add'
        row.menu(SvDataBlockListOptions.bl_idname, icon='DOWNARROW_HLT', text="")
        layout.template_list(UI_UL_SvBlenderDataList.__name__, "blender_data", self, "blender_data", self, "selected")

    def process(self):
        self.outputs['Object'].sv_set(
            [getattr(p, self.data_type) for p in self.blender_data if getattr(p, self.data_type)])


classes = [
    SvBlenderDataPointers,
    SvEditDataBlockList,
    SvDataBlockListOptions,
    UI_UL_SvBlenderDataList,
    SvBlenderDataListNode]


register, unregister = bpy.utils.register_classes_factory(classes)
