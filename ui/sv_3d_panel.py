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
        col.template_list("SV_UL_NodeTreePropertyList", "", context.scene, 'sv_ui_node_props',
                          bpy.context.scene.sverchok_panel_properties, "selected_tree")


class SV_UL_NodeTreePropertyList(bpy.types.UIList):
    """Show in 3D tool panel"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item
        tree = prop.tree

        row = layout.row(align=True)

        if not prop.node_name:
            # it is tree item
            row.prop(tree, 'SvShowIn3D', icon='DOWNARROW_HLT' if tree.SvShowIn3D else 'RIGHTARROW',
                     emboss=False, text='')
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
        else:
            # it is node item
            row_space = row.row()
            row_space.alignment = 'LEFT'
            row_space.ui_units_x = 1
            row_space.label(text='')

            prop.draw(row, tree, index)

            move_up = row.operator('node.sv_move_properties', text='', icon='TRIA_UP')
            move_up.direction = 'UP'
            move_up.prop_index = index
            move_down = row.operator('node.sv_move_properties', text='', icon='TRIA_DOWN')
            move_down.direction = 'DOWN'
            move_down.prop_index = index

    def filter_items(self, context, data, prop_name):
        ui_list = getattr(data, prop_name)
        filter_name = self.filter_name
        filter_invert = self.use_filter_invert

        hide_props = [True if not prop.node_name else prop.tree.SvShowIn3D for prop in ui_list]

        # next code is needed for hiding wrong tree types
        combine_filter = [not f for f in hide_props] if filter_invert else hide_props
        combine_filter = [self.bitflag_filter_item if f else 0 for f in hide_props]
        return combine_filter, []


class Sv3dPropItem(bpy.types.PropertyGroup):
    """It represents property of a node item in 3D panel"""
    node_name: bpy.props.StringProperty()
    tree: bpy.props.PointerProperty(type=bpy.types.NodeTree)

    def draw(self, layout, tree, index):
        node = tree.nodes.get(self.node_name, None)
        if not node:
            # properties are not automatically removed from Sv3DProps when a node is deleted.
            row = layout.row()
            row.alert = True
            row.label(icon='ERROR', text=f'missing node: "{self.node_name}"')
            row.operator('node.sv_remove_3dviewprop_item', icon='CANCEL', text='').prop_index = index
        else:
            node.draw_buttons_3dpanel(layout.column())


class SvLayoutScanProperties(bpy.types.Operator):
    """Scan layouts of Sverchok for properties"""

    bl_idname = "node.sv_scan_properties"
    bl_label = "scan for properties in Sverchok layouts"

    def execute(self, context):
        """
        1. Recreate hierarchical data structure from list
        2. Update the data structure
        3. Recreate list from scratch
        """
        ui_list = context.scene.sv_ui_node_props
        props = self.convert_ui_list(ui_list)

        for tree in bpy.data.node_groups:
            if tree.bl_idname != 'SverchCustomTreeType':
                continue

            nodes_to_show = set()
            for node in tree.nodes:
                if hasattr(node, 'draw_3dpanel'):
                    if node.draw_3dpanel:
                        nodes_to_show.add(node.name)

            showed_nodes = props.get(tree.name, {})
            for name_to_show in nodes_to_show:
                if name_to_show not in showed_nodes:
                    showed_nodes[name_to_show] = None

            for showed_name in showed_nodes.copy():
                if showed_name not in nodes_to_show:
                    del showed_nodes[showed_name]

            props[tree.name] = showed_nodes

        ui_list.clear()
        for tree_name in props:
            tree = bpy.data.node_groups[tree_name]

            ui_list.add().tree = tree

            for node_name in props[tree_name]:
                prop = ui_list.add()
                prop.node_name = node_name
                prop.tree = tree

        return {'FINISHED'}

    @staticmethod
    def convert_ui_list(ui_list):
        """
        create more complex data structure:
        {tree_name: {prop1: 0, prop2: 1},
        tree_name2: {prop1: 0,}, ...}
        """
        trees = dict()
        for prop in ui_list:
            if not prop.node_name:
                trees[prop.tree.name] = dict()
            else:
                trees[prop.tree.name][prop.node_name] = None
        return trees


class SvLayoutMoveProperties(bpy.types.Operator):
    """Move property in 3D panel"""
    bl_idname = "node.sv_move_properties"
    bl_label = "move property in 3D panel"

    direction: bpy.props.EnumProperty(items=[(i, i, '') for i in ['UP', 'DOWN']])
    prop_index: bpy.props.IntProperty(min=0)

    def execute(self, context):
        ui_list = context.scene.sv_ui_node_props
        if self.direction == 'UP':
            above_item = None if self.prop_index == 0 else ui_list[self.prop_index - 1]
            if above_item and above_item.node_name:
                ui_list.move(self.prop_index, self.prop_index - 1)
        else:
            below_item = None if self.prop_index == len(ui_list) - 1 else ui_list[self.prop_index + 1]
            if below_item and below_item.node_name:
                ui_list.move(self.prop_index, self.prop_index + 1)

        return {'FINISHED'}


class Sv3dPropRemoveItem(bpy.types.Operator):
    ''' remove item by node_name from tree.Sv3Dprops  '''

    bl_idname = "node.sv_remove_3dviewprop_item"
    bl_label = "remove item from Sv3Dprops - useful for removed nodes"

    prop_index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.sv_ui_node_props.remove(self.prop_index)
        return {'FINISHED'}


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

    bpy.types.Scene.sv_ui_node_props = bpy.props.CollectionProperty(type=Sv3dPropItem)


def unregister():
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]

    del bpy.types.Scene.sv_ui_node_props
