# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy

from sverchok.core.update_system import process_from_nodes


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

        col.operator('node.sverchok_update_all', text='Update all trees')
        col.operator('node.sv_scan_properties', text='Scan for props')

        col_edit = col.column()
        col_edit.use_property_split = True
        col_edit.prop(context.scene.sv_ui_node_props, 'edit')
        col.template_list("SV_UL_NodeTreePropertyList", "", context.scene.sv_ui_node_props, 'props',
                          context.scene.sv_ui_node_props, "selected")


class SV_UL_NodeTreePropertyList(bpy.types.UIList):
    """Show in 3D tool panel"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item

        row = layout.row(align=True)

        if prop.type == 'TREE':
            prop.draw_tree(item, row, data)

            if data.edit:
                row = row.row(align=True)
                row.alignment = 'RIGHT'
                move_up = row.operator('node.sv_move_3d_panel_item', text='', icon='TRIA_UP')
                move_up.direction = 'UP'
                move_up.prop_index = index

                move_down = row.operator('node.sv_move_3d_panel_item', text='', icon='TRIA_DOWN')
                move_down.direction = 'DOWN'
                move_down.prop_index = index

                row.operator('node.popup_edit_label', text='', icon='GREASEPENCIL').prop_index = index
                row.prop(item, 'show_tree', text='', icon=f"RESTRICT_VIEW_{'OFF' if item.show_tree else 'ON'}")

        elif prop.type == 'NODE':
            row_space = row.row()
            row_space.alignment = 'LEFT'
            row_space.ui_units_x = 1
            row_space.label(text='')

            prop.draw_node(item, row)

            if data.edit:
                move_up = row.operator('node.sv_move_3d_panel_item', text='', icon='TRIA_UP')
                move_up.direction = 'UP'
                move_up.prop_index = index

                move_down = row.operator('node.sv_move_3d_panel_item', text='', icon='TRIA_DOWN')
                move_down.direction = 'DOWN'
                move_down.prop_index = index

                row.operator('node.popup_edit_label', text='', icon='GREASEPENCIL').prop_index = index

                row.operator('node.sv_remove_3dviewprop_item', text='', icon='CANCEL').prop_index = index

    def filter_items(self, context, data, prop_name):
        ui_list = data

        show_nested_props = None
        show_tree = None
        list_filter = []
        for prop in ui_list.props:
            if prop.type == 'TREE':
                # tree item should be always shown in list edit mode or if its attribute show_tree is True
                # tree showing should not be invertible
                show_nested_props = prop.show_props
                show_tree = prop.show_tree
                list_filter.append(ui_list.edit or show_tree)
            else:  # type == 'NODE'
                # property item should be shown if tree owner is for show and if tree properties are expanded
                # and if property include substring of filter name
                # filter by filter name should be invertible
                if show_tree and show_nested_props:
                    show_prop = self.filter_name.lower() in (prop.node_label or prop.node_name).lower()
                    show_prop = not show_prop if self.use_filter_invert else show_prop
                else:
                    show_prop = False
                list_filter.append(show_prop)

        # next code is needed for hiding wrong tree types
        mix_with_inverse = [not f for f in list_filter] if self.use_filter_invert else list_filter
        mix_with_inverse = [self.bitflag_filter_item if f else 0 for f in mix_with_inverse]
        return mix_with_inverse, []


class Sv3dPropItem(bpy.types.PropertyGroup):
    """It represents property of a node item in 3D panel"""
    node_name: bpy.props.StringProperty()
    node_label: bpy.props.StringProperty()

    """
    The initial idea was to create tree attribute with pointer to NodeTree type
    mainly for performance in draw functions
    it was working fine but Blender was crashed after `script reloading` (F8) if file was saved before
    https://devtalk.blender.org/t/crash-after-reload-script-f8/15284
    so now it is tree_name instead
    """
    tree_name: bpy.props.StringProperty()  # all item types should have actual name of a tree
    show_tree: bpy.props.BoolProperty(default=True)  # switch on/off showing tree in 3d panel
    show_props: bpy.props.BoolProperty(default=True)  # store actual data only in tree type items

    @property
    def type(self):
        """
        Items are divided into two categories: 'NODE' and 'TREE'
        'TREE' shows properties of a tree and 'NODE' properties of a node for 3D panel
         """
        return 'NODE' if self.node_name else 'TREE'

    @staticmethod
    def draw_node(list_item, layout):
        tree = bpy.data.node_groups.get(list_item.tree_name)
        node = tree.nodes.get(list_item.node_name) if tree is not None else None
        if not node:
            # properties are not automatically removed from Sv3DProps when a node is deleted.
            row = layout.row()
            row.alert = True
            row.label(icon='ERROR', text=f'missing node: "{list_item.node_name}"')
        else:
            node.draw_buttons_3dpanel(layout.column())

    @staticmethod
    def draw_tree(list_item, row, ui_list):
        row.prop(list_item, 'show_props', icon='DOWNARROW_HLT' if list_item.show_props else 'RIGHTARROW',
                 emboss=False, text='')
        row = row.row()
        tree = bpy.data.node_groups.get(list_item.tree_name)
        if tree is None:
            row.alert = True
            row.label(text=f'"{list_item.tree_name}" was renamed / deleted')
        else:
            row.alert = False
            row.active = list_item.show_tree
            row.label(text=list_item.tree_name)

            # buttons
            if not ui_list.edit:
                row = row.row(align=True)
                row.alignment = 'RIGHT'
                row.ui_units_x = 4.5
                row.operator('node.sverchok_bake_all', text='B').node_tree_name = list_item.tree_name
                row.prop(tree, 'sv_show',
                         icon=f"RESTRICT_VIEW_{'OFF' if tree.sv_show else 'ON'}", text=' ')
                row.prop(tree, 'sv_animate', icon='ANIM', text=' ')
                row.prop(tree, "sv_process", toggle=True, text="P")
                row.prop(tree, "sv_draft", toggle=True, text="D")


class Sv3DNodeProperties(bpy.types.PropertyGroup):
    """It stores list of trees and node properties items in 3D panel"""
    props: bpy.props.CollectionProperty(type=Sv3dPropItem)
    edit: bpy.props.BoolProperty(name="Edit properties", description="Edit position of node properties in 3D panel",
                                 default=False, options=set())
    selected: bpy.props.IntProperty()  # selected item

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

    def move_tree(self, direction: str, from_index: str):
        """
        Only tree type items can be moved
        :param from_index: index of item which should be moved
        :param direction: 'UP' or 'DOWN'
        """
        tree_name = self.props[from_index].tree_name
        list_structure = self.generate_data_structure()  # {tree_name: {prop1: _, prop2:, _}, tree_name2: ...}
        trees = list(list_structure.keys())  # [tree_name, tree_name2, ...]
        current_index = trees.index(tree_name)
        if direction == 'UP':
            if current_index > 0:
                upper_index = current_index - 1
                trees[upper_index], trees[current_index] = trees[current_index], trees[upper_index]
        elif direction == 'DOWN':
            if current_index + 1 < len(trees):
                below_index = current_index + 1
                trees[current_index], trees[below_index] = trees[below_index], trees[current_index]
        else:
            raise TypeError(f'Unsupported direction="{direction}", possible values="UP", "DOWN"')
        self.recreate_list({tree_name: list_structure[tree_name] for tree_name in trees})

    def update_properties(self):
        """It will add or remove properties from list according state of existing layouts"""
        # 1. Recreate hierarchical data structure from list
        # 2. Update the data structure
        # 3. Recreate list from scratch
        props = self.generate_data_structure()

        # if tree was renamed or removed list can contain outdated information, such trees can be only ignored
        for tree_name in props.copy():
            if tree_name not in bpy.data.node_groups:
                del props[tree_name]

        for tree in bpy.data.node_groups:
            if tree.bl_idname != 'SverchCustomTreeType':
                continue

            nodes_to_show = set()
            for node in tree.nodes:
                if hasattr(node, 'draw_3dpanel'):
                    if node.draw_3dpanel:
                        nodes_to_show.add(node.name)

            showed_nodes = props.get(tree.name, {}).get('props', {})
            for name_to_show in nodes_to_show:
                if name_to_show not in showed_nodes:
                    showed_nodes[name_to_show] = None

            for showed_name in showed_nodes.copy():
                if showed_name not in nodes_to_show:
                    del showed_nodes[showed_name]

            if tree.name not in props:
                props[tree.name] = {'props': dict(), 'show_tree': True, 'show_props': True}
            props[tree.name]['props'] = showed_nodes

        self.recreate_list(props)

    def generate_data_structure(self):
        """
        create more complex data structure:
        {tree_name: {props: {prop1: _, prop2: _},
                     show_tree: bool,
                     show_props: bool},
        tree_name2: ...}
        """
        trees = dict()
        prop: Sv3dPropItem
        for prop in self.props:
            if prop.type == 'TREE':
                trees[prop.tree_name] = {'props': dict(), 'show_tree': prop.show_tree, 'show_props': prop.show_props}
            elif prop.type == 'NODE':
                trees[prop.tree_name]['props'][prop.node_name] = None
        return trees

    def recreate_list(self, props: dict):
        """
        It will recreate list from scratch with new given data
        :param props: it will expect the same data structure as output of generate_data_structure method
        """
        self.props.clear()
        for tree_name in props:
            tree = bpy.data.node_groups[tree_name]

            tree_prop: Sv3dPropItem = self.add(tree_name=tree.name)
            tree_prop.show_tree = props[tree_name]['show_tree']
            tree_prop.show_props = props[tree_name]['show_props']

            for node_name in props[tree_name]['props']:
                node = tree.nodes.get(node_name)
                self.add(tree_name=tree.name, node_name=node.name, node_label=node.label)

    def add(self, tree_name=None, node_name=None, node_label=None):
        prop = self.props.add()
        if tree_name:
            prop.tree_name = tree_name
        if node_name:
            prop.node_name = node_name
        if node_label:
            prop.node_label = node_label
        return prop

    def search_node(self, node_name, tree_name):
        """
        It returns index of given node in list or None
        Several trees can have nodes with similar names
        """
        for i, prop in enumerate(self.props):
            if prop.type == 'NODE':
                if prop.tree_name == tree_name and prop.node_name == node_name:
                    return i
        return None

    def search_tree(self, tree_name):
        """
        It returns index of given tree in list or None
        """
        for i, prop in enumerate(self.props):
            if prop.type == 'TREE':
                if prop.tree_name == tree_name:
                    return i
        return None


class SvLayoutScanProperties(bpy.types.Operator):
    """
    Scan layouts of Sverchok for properties
    Nodes with available "Show in 3D" properties on will be added to property list
    """
    bl_idname = "node.sv_scan_properties"
    bl_label = "scan for properties in Sverchok layouts"

    def execute(self, context):
        context.scene.sv_ui_node_props.update_properties()
        return {'FINISHED'}


class SvMove3DPanelItem(bpy.types.Operator):
    """Move property in 3D panel"""
    bl_idname = "node.sv_move_3d_panel_item"
    bl_label = "move property in 3D panel"

    direction: bpy.props.EnumProperty(items=[(i, i, '') for i in ['UP', 'DOWN']])
    prop_index: bpy.props.IntProperty(min=0)

    def execute(self, context):
        ui_list = context.scene.sv_ui_node_props
        if ui_list.props[self.prop_index].type == 'NODE':
            ui_list.move_prop(self.direction, self.prop_index)
        else:
            ui_list.move_tree(self.direction, self.prop_index)
        return {'FINISHED'}


class Sv3dPropRemoveItem(bpy.types.Operator):
    ''' remove item by node_name from tree.Sv3Dprops  '''

    bl_idname = "node.sv_remove_3dviewprop_item"
    bl_label = "remove item from Sv3Dprops - useful for removed nodes"

    prop_index: bpy.props.IntProperty()

    def execute(self, context):
        prop = context.scene.sv_ui_node_props.props[self.prop_index]
        node = bpy.data.node_groups.get(prop.tree_name).nodes.get(prop.node_name)
        if node:
            # assume that node will delete its itself
            node.draw_3dpanel = False
        else:
            # in case if node was already deleted
            context.scene.sv_ui_node_props.props.remove(self.prop_index)
        return {'FINISHED'}


class SvPopupEditLabel(bpy.types.Operator):
    """Menu for editing node labels and tree names"""
    bl_idname = "node.popup_edit_label"
    bl_label = "Edit label"
    bl_options = {'INTERNAL'}

    prop_index: bpy.props.IntProperty()

    # for internal usage
    new_node_name: bpy.props.StringProperty()  # actually will be assigned to node label
    new_tree_name: bpy.props.StringProperty()

    def execute(self, context):
        prop = context.scene.sv_ui_node_props.props[self.prop_index]
        tree = bpy.data.node_groups.get(prop.tree_name)
        node = tree.nodes.get(prop.node_name) if tree is not None else None
        if prop.type == 'NODE':
            prop.node_label = self.new_node_name
            if node is not None:
                node.label = self.new_node_name
        elif prop.type == 'TREE':
            old_tree_name = prop.tree_name
            for prop in context.scene.sv_ui_node_props.props[self.prop_index:]:
                # tree names in nested properties also should be renamed
                if prop.tree_name != old_tree_name:
                    break
                prop.tree_name = self.new_tree_name
            if tree is not None:
                tree.name = self.new_tree_name
        return {'FINISHED'}

    def invoke(self, context, event):
        prop = context.scene.sv_ui_node_props.props[self.prop_index]
        if prop.type == 'NODE':
            self.new_node_name = prop.node_label or prop.node_name
            self.new_tree_name = ''
        elif prop.type == 'TREE':
            self.new_node_name = ''
            self.new_tree_name = prop.tree_name

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        if self.new_node_name:
            self.layout.label(text=f'Edit label of node="{self.new_node_name}"')
            self.layout.prop(self, 'new_node_name')
        else:
            self.layout.label(text=f'Edit tree name="{self.new_tree_name}"')
            self.layout.prop(self, 'new_tree_name')


class Sv3DViewObjInUpdater(bpy.types.Operator, object):
    """For automatic trees reevaluation upon changes in 3D space"""
    bl_idname = "wm.sv_obj_modal_update"
    bl_label = "start n stop obj updating"

    _timer = None
    mode: bpy.props.StringProperty(default='toggle')
    node_name: bpy.props.StringProperty(default='')
    node_group: bpy.props.StringProperty(default='')
    speed: bpy.props.FloatProperty(default=1 / 13)

    def modal(self, context, event):

        if not context.scene.SvShowIn3D_active:
            self.cancel(context)
            return {'FINISHED'}

        if not (event.type == 'TIMER'):
            return {'PASS_THROUGH'}

        objects_nodes_set = {'ObjectsNode', 'ObjectsNodeMK2', 'SvObjectsNodeMK3', 'SvExNurbsInNode', 'SvBezierInNode'}
        obj_nodes = []
        for ng in bpy.data.node_groups:
            if ng.bl_idname == 'SverchCustomTreeType':
                if ng.sv_process:
                    nodes = []
                    for n in ng.nodes:
                        if n.bl_idname in objects_nodes_set:
                            nodes.append(n)
                    if nodes:
                        obj_nodes.append(nodes)

        ''' reaches here only if event is TIMER and self.active '''
        for n in obj_nodes:
            # print('calling process on:', n.name, n.id_data)
            process_from_nodes(n)

        return {'PASS_THROUGH'}

    def start(self, context):
        context.scene.SvShowIn3D_active = True

        # rate can only be set in event_timer_add (I think...)
        # self.speed = 1 / context.node.updateRate

        wm = context.window_manager
        self._timer = wm.event_timer_add(self.speed, window=context.window)
        wm.modal_handler_add(self)
        self.report({'INFO'}, "Live Update mode enabled")

    def stop(self, context):
        context.scene.SvShowIn3D_active = False

    def toggle(self, context):
        if context.scene.SvShowIn3D_active:
            self.stop(context)
        else:
            self.start(context)

    def event_dispatcher(self, context, type_op):
        if type_op == 'start':
            self.start(context)
        elif type_op == 'end':
            self.stop(context)
        else:
            self.toggle(context)

    def execute(self, context):
        # n  = context.node
        # self.node_name = context.node.name
        # self.node_group = context.node.id_data.name

        self.event_dispatcher(context, self.mode)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.report({'INFO'}, "Live Update mode disabled")


classes = [
    SV_PT_3DPanel,
    SV_UL_NodeTreePropertyList,
    Sv3dPropItem,
    SvLayoutScanProperties,
    SvMove3DPanelItem,
    Sv3dPropRemoveItem,
    Sv3DNodeProperties,
    SvPopupEditLabel,
    Sv3DViewObjInUpdater,
]


def register():
    [bpy.utils.register_class(cls) for cls in classes]

    bpy.types.Scene.sv_ui_node_props = bpy.props.PointerProperty(type=Sv3DNodeProperties)


def unregister():
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]

    del bpy.types.Scene.sv_ui_node_props
