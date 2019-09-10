# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

short_menu = {
    "input": "SvNumber SvFloatRange SvIntRange SvRandomNumber SvRandomVector SvFieldVector".split(),
    "generator": "SvLine SvPlane SvCircle SvCube SvSphere SvRoundedCube".split(), 
    "effect": "SvInset SvApplyNoise SvApplyRandom SvSmooth".split(),
    "topology": "SvSeparate SvUVConnection SvMergeMesh SvBoolean".split(),
    "analyze": "SvStethoscope SvIndexViewer".split(),
    "output": "SvVDExperimental SvBmeshViewer SvCurveViewer".split()
}


class SvPopulateLiteMenu(bpy.types.Operator):
    bl_label = "Populate Lite Menu"
    bl_idname = "node.sv_populate_lite_menu"

    def execute(self, context):
        menu_headers = context.space_data.node_tree.sv_lite_menu_headers
        menu_headers.clear()
        for k in short_menu.keys():
            item = menu_headers.add()
            item.heading = k


class SvLiteMenuItems(bpy.types.PropertyGroup):
    heading: bpy.props.StringProperty(name="heading to show", default="")


class NODEVIEW_MT_SvLiteSubmenu(bpy.types.Menu):
    bl_label = "Camera Properties"

    def draw(self, context):
        layout = self.layout
        for item in short_menu[context.sv_menu_key.heading]:
            layout.row().label(text=item)

class NODEVIEW_MT_SvLiteMenu(bpy.types.Menu):
    bl_label = "Sv Nodes"

    def draw(self, context):
        layout = self.layout
        for item in context.space_data.node_tree.sv_lite_menu_headers:
            row = layout.row()
            row.context_pointer_set("sv_menu_key", item)
            row.menu(NODEVIEW_MT_SvLiteSubmenu.bl_idname, text=item.heading)

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
