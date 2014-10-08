# -*- coding: utf-8 -*-
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

''' borrows heavily from insights provided by Dynamic Space Bar! '''

import bpy
from bpy.props import (
    StringProperty,
)

from sverchok.menu import make_node_cats

node_cats = make_node_cats()


def layout_draw_categories(layout, node_details):
    # add_n_grab = 'node.sverchok_addngrab'
    add_n_grab = 'node.add_node'
    for node_info in node_details:
        num_items = len(node_info)
        if num_items == 3:
            bl_idname, shortname, icon = node_info
            node_op = layout.operator(add_n_grab, text=shortname, icon=icon)
        elif num_items == 2:
            bl_idname, shortname = node_info
            node_op = layout.operator(add_n_grab, text=shortname)
        else:
            continue
        node_op.type = bl_idname
        node_op.use_transform = True


class NODEVIEW_MT_Dynamic_Menu(bpy.types.Menu):
    bl_label = "Sverchok Nodes"

    @classmethod
    def poll(cls, context):
        tree_type = context.space_data.tree_type
        return (tree_type == 'SverchCustomTreeType')

    def draw(self, context):

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        s = layout.operator("node.add_search", text="Search", icon='VIEWZOOM')
        s.use_transform = True

        layout.separator()
        layout.menu("NODEVIEW_MT_AddGenerators", icon='OBJECT_DATAMODE')
        layout.menu("NODEVIEW_MT_AddTransforms", icon='MANIPUL')
        layout.menu("NODEVIEW_MT_AddAnalyzers", icon='BORDERMOVE')
        layout.menu("NODEVIEW_MT_AddModifiers", icon='MODIFIER')
        layout.separator()
        layout.menu("NODEVIEW_MT_AddNumber")
        layout.menu("NODEVIEW_MT_AddVector")
        layout.menu("NODEVIEW_MT_AddMatrix")
        layout.menu("NODEVIEW_MT_AddConditionals")
        layout.menu("NODEVIEW_MT_AddListOps")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddBasicViz")
        layout.menu("NODEVIEW_MT_AddBasicData")
        layout.menu("NODEVIEW_MT_AddBasicDebug")
        layout.separator()
        layout.menu("NODEVIEW_MT_AddBetas", icon='OUTLINER_DATA_POSE')
        layout.menu("NODEVIEW_MT_AddAlphas", icon='ERROR')


class NODEVIEW_MT_AddGenerators(bpy.types.Menu):
    bl_label = "Generators"

    def draw(self, context):
        layout = self.layout
        layout_draw_categories(self.layout, node_cats[self.bl_label])
        layout.menu("NODEVIEW_MT_AddGeneratorsExt", icon='PLUGIN')


class NODEVIEW_MT_AddGeneratorsExt(bpy.types.Menu):
    bl_label = "Extended Generators"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddTransforms(bpy.types.Menu):
    bl_label = "Transforms (Vec, Mat)"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddModifiers(bpy.types.Menu):
    bl_label = "Modifiers (Make, Change)"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddModifierChange")
        layout.menu("NODEVIEW_MT_AddModifierMake")


class NODEVIEW_MT_AddListOps(bpy.types.Menu):
    bl_label = "List operations"

    def draw(self, context):
        layout = self.layout
        layout.menu("NODEVIEW_MT_AddListmain")
        layout.menu("NODEVIEW_MT_AddListstruct")
        layout_draw_categories(self.layout, node_cats["List Masks"])


class NODEVIEW_MT_AddBetas(bpy.types.Menu):
    bl_label = "Beta Nodes"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddAlphas(bpy.types.Menu):
    bl_label = "Alpha Nodes"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddAnalyzers(bpy.types.Menu):
    bl_label = "Analyzers"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddBasicViz(bpy.types.Menu):
    bl_label = "Basic Viz"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddBasicData(bpy.types.Menu):
    bl_label = "Basic Data"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddBasicDebug(bpy.types.Menu):
    bl_label = "Basic Debug"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddListmain(bpy.types.Menu):
    bl_label = "List main"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddListstruct(bpy.types.Menu):
    bl_label = "List struct"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddNumber(bpy.types.Menu):
    bl_label = "Number"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddVector(bpy.types.Menu):
    bl_label = "Vector"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddMatrix(bpy.types.Menu):
    bl_label = "Matrix"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddModifierChange(bpy.types.Menu):
    bl_label = "Modifier Change"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddModifierMake(bpy.types.Menu):
    bl_label = "Modifier Make"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


class NODEVIEW_MT_AddConditionals(bpy.types.Menu):
    bl_label = "Conditionals"

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


classes = [
    NODEVIEW_MT_Dynamic_Menu,
    NODEVIEW_MT_AddGenerators,
    NODEVIEW_MT_AddGeneratorsExt,
    NODEVIEW_MT_AddTransforms,
    NODEVIEW_MT_AddModifiers,
    NODEVIEW_MT_AddAnalyzers,
    NODEVIEW_MT_AddBasicViz,
    NODEVIEW_MT_AddBasicData,
    NODEVIEW_MT_AddBasicDebug,
    NODEVIEW_MT_AddListmain,
    NODEVIEW_MT_AddListstruct,
    NODEVIEW_MT_AddNumber,
    NODEVIEW_MT_AddVector,
    NODEVIEW_MT_AddMatrix,
    NODEVIEW_MT_AddListOps,
    NODEVIEW_MT_AddModifierChange,
    NODEVIEW_MT_AddModifierMake,
    NODEVIEW_MT_AddConditionals,
    NODEVIEW_MT_AddBetas,
    NODEVIEW_MT_AddAlphas,
]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
        kmi.properties.name = "NODEVIEW_MT_Dynamic_Menu"


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Node Editor']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu':
                if kmi.properties.name == "NODEVIEW_MT_Dynamic_Menu":
                    km.keymap_items.remove(kmi)
                    break
