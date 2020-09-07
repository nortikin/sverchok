# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.utils.logging import debug


class SV_PT_3DPanel(bpy.types.Panel):
    """Panel to manipulate parameters in Sverchok layouts"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    bl_label = "Sverchok"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        col = self.layout.column()
        if context.scene.SvShowIn3D_active:
            col.operator('wm.sv_obj_modal_update', text='Stop live update', icon='CANCEL').mode = 'end'
        else:
            col.operator('wm.sv_obj_modal_update', text='Start live update', icon='EDITMODE_HLT').mode = 'start'

        col.operator('node.sv_scan_properties', text='Scan for props')
        col.template_list("SV_UL_NodeTreePropertyList", "", bpy.data, 'node_groups',
                          bpy.context.scene.sverchok_panel_properties, "selected_tree")


class SV_UL_NodeTreePropertyList(bpy.types.UIList):
    """Show in 3D tool panel"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        tree = item

        col = layout.column(align=True)
        row = col.row(align=True)
        row.alignment = 'LEFT'

        if tree.SvShowIn3D:
            row.prop(tree, 'SvShowIn3D', icon='DOWNARROW_HLT', emboss=False, text='')
            for i, prop in enumerate(tree.sv_ui_node_props):
                row_prop = col.column().row(align=True)
                prop.draw(row_prop, tree)
                move_up = row_prop.operator('node.sv_move_properties', text='', icon='TRIA_UP')
                move_up.direction = 'UP'
                move_up.prop_index = i
                move_up.tree_owner = tree.name
                move_down = row_prop.operator('node.sv_move_properties', text='', icon='TRIA_DOWN')
                move_down.direction = 'DOWN'
                move_down.prop_index = i
                move_down.tree_owner = tree.name
        else:
            row.prop(tree, 'SvShowIn3D', icon='RIGHTARROW', emboss=False, text='')

        row = row.row()
        row.label(text=tree.name)

        # buttons
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.ui_units_x = 7
        row.operator('node.sverchok_bake_all', text='B').node_tree_name = tree.name
        row.prop(tree, 'sv_show', icon=f"RESTRICT_VIEW_{'OFF' if tree.sv_show else 'ON'}", text=' ')
        row.prop(tree, 'sv_animate', icon='ANIM', text=' ')
        row.prop(tree, "sv_process", toggle=True, text="P")
        row.prop(tree, "sv_draft", toggle=True, text="D")
        row.prop(tree, 'use_fake_user', toggle=True, text='F')

    def filter_items(self, context, data, prop_name):
        trees = getattr(data, prop_name)
        filter_name = self.filter_name
        filter_invert = self.use_filter_invert

        filter_tree_types = [tree.bl_idname == 'SverchCustomTreeType' for tree in trees]

        filter_tree_names = [filter_name in tree.name for tree in trees]
        filter_tree_names = [not f for f in filter_tree_names] if filter_invert else filter_tree_names

        combine_filter = [f1 and f2 for f1, f2 in zip(filter_tree_types, filter_tree_names)]
        # next code is needed for hiding wrong tree types
        combine_filter = [not f for f in combine_filter] if filter_invert else combine_filter
        combine_filter = [self.bitflag_filter_item if f else 0 for f in combine_filter]
        return combine_filter, []


class Sv3dPropItem(bpy.types.PropertyGroup):
    """It represents property of a node item in 3D panel"""
    node_name: bpy.props.StringProperty()

    def draw(self, layout, tree):
        node = tree.nodes.get(self.node_name, None)
        if not node:
            # properties are not automatically removed from Sv3DProps when a node is deleted.
            row = layout.row()
            row.alert = True
            row.label(icon='ERROR', text=f'missing node: "{self.node_name}"')
            op = row.operator('node.sv_remove_3dviewpropitem', icon='CANCEL', text='')
            op.tree_name = tree.name
            op.node_name = self.node_name

        node.draw_buttons_3dpanel(layout.column())


class SvLayoutScanProperties(bpy.types.Operator):
    """Scan layouts of Sverchok for properties"""

    bl_idname = "node.sv_scan_properties"
    bl_label = "scan for properties in Sverchok layouts"

    def execute(self, context):
        for tree in bpy.data.node_groups:

            if tree.bl_idname != 'SverchCustomTreeType':
                continue

            nodes_to_show = set()
            for node in tree.nodes:
                if hasattr(node, 'draw_3dpanel'):
                    if node.draw_3dpanel:
                        nodes_to_show.add(node.name)

            showed_nodes = {prop.node_name for prop in tree.sv_ui_node_props}
            for name_to_show in nodes_to_show:
                if name_to_show not in showed_nodes:
                    debug(f'3D PANEL: add property of the node="{name_to_show}"')
                    item = tree.sv_ui_node_props.add()
                    item.node_name = name_to_show

            for i in range(len(showed_nodes) - 1, -1, -1):
                if tree.sv_ui_node_props[i].node_name not in nodes_to_show:
                    debug(f'3D PANEL: remove property of the node="{tree.sv_ui_node_props[i].node_name}"')
                    tree.sv_ui_node_props.remove(i)

        return {'FINISHED'}


class SvLayoutMoveProperties(bpy.types.Operator):
    """Move property in 3D panel"""
    bl_idname = "node.sv_move_properties"
    bl_label = "move property in 3D panel"

    direction: bpy.props.EnumProperty(items=[(i, i, '') for i in ['UP', 'DOWN']])
    prop_index: bpy.props.IntProperty(min=0)
    tree_owner: bpy.props.StringProperty()

    def execute(self, context):
        tree = bpy.data.node_groups.get(self.tree_owner)
        tree.sv_ui_node_props.move(self.prop_index, self.prop_index - (1 if self.direction == 'UP' else -1))

        return {'FINISHED'}


class Sv3dPropRemoveItem(bpy.types.Operator):
    ''' remove item by node_name from tree.Sv3Dprops  '''

    bl_idname = "node.sv_remove_3dviewpropitem"
    bl_label = "remove item from Sv3Dprops - useful for removed nodes"

    tree_name: bpy.props.StringProperty(description="store tree name")
    node_name: bpy.props.StringProperty(description="store node name")

    def execute(self, context):

        tree = bpy.data.node_groups[self.tree_name]
        props = tree.sv_ui_node_props

        for index in range(len(props)):
            if props[index].node_name == self.node_name:
                props.remove(index)
                return {'FINISHED'}

        return {'CANCELLED'}


classes = [
    SV_PT_3DPanel,
    SV_UL_NodeTreePropertyList,
    Sv3dPropItem,
    SvLayoutScanProperties,
    SvLayoutMoveProperties,
    Sv3dPropRemoveItem
]


def register():
    [bpy.utils.register_class(cls) for cls in classes]

    bpy.types.NodeTree.sv_ui_node_props = bpy.props.CollectionProperty(type=Sv3dPropItem)


def unregister():
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]

    del bpy.types.NodeTree.sv_ui_node_props
