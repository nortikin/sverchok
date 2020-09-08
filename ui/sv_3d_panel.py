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
        col.template_list("SV_UL_NodeTreePropertyList", "", context.scene.sv_ui_node_props, 'props',
                          bpy.context.scene.sverchok_panel_properties, "selected_tree")


class SV_UL_NodeTreePropertyList(bpy.types.UIList):
    """Show in 3D tool panel"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item
        tree = prop.tree

        row = layout.row(align=True)

        if prop.type == 'TREE':
            prop.draw_tree(row)

        elif prop.type == 'NODE':
            row_space = row.row()
            row_space.alignment = 'LEFT'
            row_space.ui_units_x = 1
            row_space.label(text='')

            prop.draw_node(row, index)

            move_up = row.operator('node.sv_move_properties', text='', icon='TRIA_UP')
            move_up.direction = 'UP'
            move_up.prop_index = index
            move_down = row.operator('node.sv_move_properties', text='', icon='TRIA_DOWN')
            move_down.direction = 'DOWN'
            move_down.prop_index = index

    def filter_items(self, context, data, prop_name):
        ui_list = data

        items_filter = ui_list.filter(self.filter_name, self.use_filter_invert)
        combine_filter = [self.bitflag_filter_item if f else 0 for f in items_filter]
        return combine_filter, []


class Sv3dPropItem(bpy.types.PropertyGroup):
    """It represents property of a node item in 3D panel"""
    node_name: bpy.props.StringProperty()
    tree: bpy.props.PointerProperty(type=bpy.types.NodeTree)

    @property
    def type(self):
        """
        Items are divided into two categories: 'NODE' and 'TREE'
        'TREE' shows properties of a tree and 'NODE' properties of a node for 3D panel
         """
        return 'NODE' if self.node_name else 'TREE'

    def draw_node(self, layout, index):
        node = self.tree.nodes.get(self.node_name, None)
        if not node:
            # properties are not automatically removed from Sv3DProps when a node is deleted.
            row = layout.row()
            row.alert = True
            row.label(icon='ERROR', text=f'missing node: "{self.node_name}"')
            row.operator('node.sv_remove_3dviewprop_item', icon='CANCEL', text='').prop_index = index
        else:
            node.draw_buttons_3dpanel(layout.column())

    def draw_tree(self, row):
        row.prop(self.tree, 'sv_show_in_3d', icon='DOWNARROW_HLT' if self.tree.sv_show_in_3d else 'RIGHTARROW',
                 emboss=False, text='')
        row = row.row()
        row.label(text=self.tree.name)

        # buttons
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        row.ui_units_x = 7
        row.operator('node.sverchok_bake_all', text='B').node_tree_name = self.tree.name
        row.prop(self.tree, 'sv_show', icon=f"RESTRICT_VIEW_{'OFF' if self.tree.sv_show else 'ON'}", text=' ')
        row.prop(self.tree, 'sv_animate', icon='ANIM', text=' ')
        row.prop(self.tree, "sv_process", toggle=True, text="P")
        row.prop(self.tree, "sv_draft", toggle=True, text="D")
        row.prop(self.tree, 'use_fake_user', toggle=True, text='F')


class Sv3DNodeProperties(bpy.types.PropertyGroup):
    """It stores list of trees and node properties items in 3D panel"""
    props: bpy.props.CollectionProperty(type=Sv3dPropItem)

    def move_prop(self, direction: str, from_index: int):
        """
        Only node type items can be moved, if above or below will be tree type item nothing happens
        :param from_index: index of item which should be moved
        :param direction: 'UP' or 'DOWN'
        """
        if direction == 'UP':
            above_item = None if from_index == 0 else self.props[from_index - 1]
            if above_item and above_item.node_name:
                self.props.move(from_index, from_index - 1)
        elif direction == 'DOWN':
            below_item = None if from_index == len(self.props) - 1 else self.props[from_index + 1]
            if below_item and below_item.node_name:
                self.props.move(from_index, from_index + 1)
        else:
            raise TypeError(f'Unsupported direction="{direction}", possible values="UP", "DOWN"')

    def generate_data_structure(self):
        """
        create more complex data structure:
        {tree_name: {prop1: 0, prop2: 1},
        tree_name2: {prop1: 0,}, ...}
        """
        trees = dict()
        for prop in self.props:
            if not prop.node_name:
                trees[prop.tree.name] = dict()
            else:
                trees[prop.tree.name][prop.node_name] = None
        return trees

    def recreate_list(self, props: dict):
        """
        It will recreate list from scratch with new given data
        :param props: it will expect the same data structure as output of generate_data_structure method
        """
        self.props.clear()
        for tree_name in props:
            tree = bpy.data.node_groups[tree_name]

            self.add().tree = tree

            for node_name in props[tree_name]:
                prop = self.add()
                prop.node_name = node_name
                prop.tree = tree

    def filter(self, name: str = None, invert: bool = False):
        """
        Create filter mask of node property types, tree type items will be always shown
        Also it will filter out thous node properties which trees have sv_show_in_3d with False value
        :param name: string which should be in property name
        :param invert: returns inverted filter
        :return: bool list
        """
        hide_props = [True if prop.type == 'TREE' else prop.tree.sv_show_in_3d for prop in self.props]

        # next code is needed for hiding wrong tree types
        hide_props = [not f for f in hide_props] if invert else hide_props
        return hide_props

    def update_show_property(self, node):
        """This method will automatically add/remove property from 3d panel upon show 3d property changes"""
        if node.draw_3dpanel:
            # item should be added
            if (node.id_data.name, node.name) not in [(prop.tree.name, prop.node_name) for prop in self.props]:
                # just in case if it was not already added, how?
                tree_end = self.search_tree_end(node.id_data.name)
                if tree_end is None:
                    # tree item should be added first
                    self.add(tree=node.id_data)
                    self.add(tree=node.id_data, node_name=node.name)
                else:
                    # tree already added
                    self.insert(tree_end + 1, tree=node.id_data, node_name=node.name)
        else:
            # item should be removed
            position = self.search_node(node.name, node.id_data.name)
            if position:
                self.props.remove(position)

    def insert(self, index, tree=None, node_name=None):
        """Inserts element into custom position"""
        # move is quite efficient operation, looks independent from collection length
        current_index = len(self.props)
        prop = self.props.add()
        if tree:
            prop.tree = tree
        if node_name:
            prop.node_name = node_name
        self.props.move(current_index, index)
        return prop

    def clear(self):
        self.props.clear()

    def add(self, tree=None, node_name=None):
        prop = self.props.add()
        if tree:
            prop.tree = tree
        if node_name:
            prop.node_name = node_name
        return prop

    def search_tree(self, name: str):
        """Find position of a tree, return int or None if tree does not exist"""
        for i, prop in enumerate(self.props):
            if prop.type == 'TREE':
                if prop.tree.name == name:
                    return i
        return None

    def search_node(self, node_name, tree_name):
        """Several trees can have nodes with similar names"""
        for i, prop in enumerate(self.props):
            if prop.type == 'NODE':
                if prop.tree.name == tree_name and prop.node_name == node_name:
                    return i
        return None

    def search_tree_end(self, tree_name):
        """Return index of last property item of given tre or None if tree does not exist"""
        tree_index = self.search_tree(tree_name)
        if tree_index is not None:
            last_index = None
            for prop_index, prop in enumerate(self.props[tree_index:]):
                last_index = prop_index
                if prop.type == 'TREE' and prop.tree.name != tree_name:
                    # another tree has started
                    return tree_index + prop_index - 1
            if last_index is None:
                # the tree is last and does not have properties
                return tree_index
            else:
                # tree is last but has properties
                return tree_index + last_index
        else:
            # tree does not exist
            return None


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
        props = ui_list.generate_data_structure()

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

        ui_list.recreate_list(props)

        return {'FINISHED'}


class SvLayoutMoveProperties(bpy.types.Operator):
    """Move property in 3D panel"""
    bl_idname = "node.sv_move_properties"
    bl_label = "move property in 3D panel"

    direction: bpy.props.EnumProperty(items=[(i, i, '') for i in ['UP', 'DOWN']])
    prop_index: bpy.props.IntProperty(min=0)

    def execute(self, context):
        ui_list = context.scene.sv_ui_node_props
        ui_list.move_prop(self.direction, self.prop_index)
        return {'FINISHED'}


class Sv3dPropRemoveItem(bpy.types.Operator):
    ''' remove item by node_name from tree.Sv3Dprops  '''

    bl_idname = "node.sv_remove_3dviewprop_item"
    bl_label = "remove item from Sv3Dprops - useful for removed nodes"

    prop_index: bpy.props.IntProperty()

    def execute(self, context):
        context.scene.sv_ui_node_props.props.remove(self.prop_index)
        return {'FINISHED'}


classes = [
    SV_PT_3DPanel,
    SV_UL_NodeTreePropertyList,
    Sv3dPropItem,
    SvLayoutScanProperties,
    SvLayoutMoveProperties,
    Sv3dPropRemoveItem,
    Sv3DNodeProperties
]


def register():
    [bpy.utils.register_class(cls) for cls in classes]

    bpy.types.Scene.sv_ui_node_props = bpy.props.PointerProperty(type=Sv3DNodeProperties)
    bpy.types.NodeTree.sv_show_in_3d = bpy.props.BoolProperty(
        name='show in panel',
        default=True,
        description='Show properties in 3d panel or not')


def unregister():
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]

    del bpy.types.Scene.sv_ui_node_props
    del bpy.types.NodeTree.sv_show_in_3d
