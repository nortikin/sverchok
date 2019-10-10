# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
from os.path import dirname
from collections import defaultdict

import bpy
from sverchok.menu import node_add_operators, draw_add_node_operator
from sverchok.utils import get_node_class_reference
from sverchok.ui.sv_icons import icon


def parse_lite_menu(filename_to_parse):

    lite_menu_path = os.path.join(dirname(__file__), filename_to_parse)

    with open(lite_menu_path) as _file:
        categories = defaultdict(list)
        current_category = ""
        for line in _file:

            if line.strip().startswith("===="):
                current_category = line.strip()
                continue

            if line.strip().startswith("# "):
                current_category = line.strip().replace("# ", "")
                continue

            if not current_category:
                break

            if current_category.startswith("===="):
                categories[current_category].append("separator")
                continue

            text_on_line = line.strip()
            if text_on_line:
                categories[current_category].append(text_on_line)

        return categories

    print('failed to parse lite menu')
    return {}  # just in case


# this may not respond to attempts to repopulate the dict. we
# would need to move this external to this file and import... i think.
short_menu = parse_lite_menu("lite_menu.md")

def header_sliced(header):
    """ assumes lite_menu.md items are ABC XYZ {ICONNAME} """
    return header.replace('}', '').split(' {')


class SvPopulateLiteMenu(bpy.types.Operator):
    bl_label = "Populate Lite Menu"
    bl_idname = "node.sv_populate_lite_menu"

    def execute(self, context):
        menu_headers = context.space_data.node_tree.sv_lite_menu_headers
        menu_headers.clear()
        for k in short_menu.keys():
            item = menu_headers.add()
            item.heading = k
        return {'FINISHED'}


class SvLiteMenuItems(bpy.types.PropertyGroup):
    heading: bpy.props.StringProperty(name="heading to show", default="")


class NODEVIEW_MT_SvLiteSubmenu(bpy.types.Menu):
    bl_label = "Sv Nodes submenu"

    def draw(self, context):
        layout = self.layout
        for item in short_menu[context.sv_menu_key.heading]:
            if item == "---":
                layout.row().separator()
                continue
            
            node_add_operator = node_add_operators.get(item.lower())
            if node_add_operator:
                # node_ref = get_node_class_reference(item)
                # layout.operator(node_add_operator.bl_idname, text=node_ref.bl_label)
                draw_add_node_operator(layout, item, label=None, icon_name=None, params=None)
            else:
                layout.row().label(text=item)



class NODEVIEW_MT_SvLiteMenu(bpy.types.Menu):
    bl_label = "Sv Nodes"

    def draw(self, context):
        layout = self.layout
        for item in context.space_data.node_tree.sv_lite_menu_headers:
            row = layout.row()

            if item.heading.startswith("===="):
                row.separator()
                continue

            row.context_pointer_set("sv_menu_key", item)
            header, icon_str = header_sliced(item.heading)
            row.menu("NODEVIEW_MT_SvLiteSubmenu", text=header, **icon(icon_str))

def register():
    bpy.utils.register_class(SvPopulateLiteMenu)
    bpy.utils.register_class(SvLiteMenuItems)
    bpy.types.NodeTree.sv_lite_menu_headers = bpy.props.CollectionProperty(type=SvLiteMenuItems)
    bpy.utils.register_class(NODEVIEW_MT_SvLiteSubmenu) 
    bpy.utils.register_class(NODEVIEW_MT_SvLiteMenu)

def unregister():
    bpy.utils.unregister_class(NODEVIEW_MT_SvLiteSubmenu)
    bpy.utils.unregister_class(NODEVIEW_MT_SvLiteMenu)
    bpy.utils.unregister_class(SvLiteMenuItems)
    bpy.utils.unregister_class(SvPopulateLiteMenu)
    del bpy.types.NodeTree.sv_lite_menu_headers
