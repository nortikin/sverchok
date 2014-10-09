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

'''
zeffii 2014.

borrows heavily from insights provided by Dynamic Space Bar!
but massively condensed for sanity.
'''

import bpy
from bpy.props import (
    StringProperty,
)

from sv_nodes_menu import make_node_cats

node_cats = make_node_cats()


def layout_draw_categories(layout, node_details):
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


# does not get registered
class NodeViewMenuTemplate(bpy.types.Menu):
    bl_label = ""

    def draw(self, context):
        layout_draw_categories(self.layout, node_cats[self.bl_label])


# quick class factory.
def make_class(name, node_list):
    name = 'NODEVIEW_MT_Add' + name
    return type(name, (NodeViewMenuTemplate,), {'bl_label': node_list})


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

# make class                   | NODEVIEW_MT_Add + class name , menu name
NODEVIEW_MT_AddGeneratorsExt = make_class('GeneratorsExt', "Extended Generators")
NODEVIEW_MT_AddTransforms = make_class('Transforms', "Transforms (Vec, Mat)")
NODEVIEW_MT_AddAnalyzers = make_class('Analyzers', "Analyzers")

NODEVIEW_MT_AddNumber = make_class('Number', "Number")
NODEVIEW_MT_AddVector = make_class('Vector', "Vector")
NODEVIEW_MT_AddMatrix = make_class('Matrix', "Matrix")
NODEVIEW_MT_AddConditionals = make_class('Conditionals', "Conditionals")

NODEVIEW_MT_AddListmain = make_class('Listmain', "List main")
NODEVIEW_MT_AddListstruct = make_class('Liststruct', "List struct")
NODEVIEW_MT_AddModifierChange = make_class('ModifierChange', "Modifier Change")
NODEVIEW_MT_AddModifierMake = make_class('ModifierMake', "Modifier Make")

NODEVIEW_MT_AddBasicViz = make_class('BasicViz', "Basic Viz")
NODEVIEW_MT_AddBasicData = make_class('BasicData', "Basic Data")
NODEVIEW_MT_AddBasicDebug = make_class('BasicDebug', "Basic Debug")

NODEVIEW_MT_AddBetas = make_class('Betas', "Beta Nodes")
NODEVIEW_MT_AddAlphas = make_class('Alphas', "Alpha Nodes")

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
