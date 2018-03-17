# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import os
import bpy

from sverchok.utils.sv_examples_utils import examples_paths


def draw_item(self, context, item):

    ntree = context.space_data.node_tree
    if not ntree:
        ntree = lambda: None
        ntree.name = '____make_new____'

    self.path_menu(searchpaths=[examples_paths.get(item)], operator='node.tree_importer_silent', props_default={"id_tree": ntree.name})

# quick class factory.
def make_class(bl_label):
    bl_idname = "SV_MT_PyMenu_" + bl_label
    draw_func = lambda s, c: draw_item(s, c, bl_label)
    return type(bl_idname, (bpy.types.Menu,), {'bl_label': bl_label, 'draw': draw_func, 'bl_idname': bl_idname})

menu_classes = []
for catname in examples_paths:
    locals()['SV_MT_PyMenu_'+ catname] = make_class(catname) 
    menu_classes.append(locals()['SV_MT_PyMenu_'+ catname])



# Node Examples Menu
class SV_MT_layouts_examples(bpy.types.Menu):
    bl_idname = 'SV_MT_layouts_examples'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Examples"
    bl_description = "List of Sverchok Examples"


    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType' and context.scene.node_tree
        except Exception as err:
            return False

    def draw(self, context):
        layout = self.layout

        # scene = context.scene
        for cls in menu_classes:
            layout.menu(cls.__name__)


def node_examples_pulldown(self, context):
    if context.space_data.tree_type == 'SverchCustomTreeType':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.menu("SV_MT_layouts_examples", icon="RNA")


classes = menu_classes + [SV_MT_layouts_examples]

def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]
    bpy.types.NODE_HT_header.append(node_examples_pulldown)


def unregister():
    bpy.types.NODE_HT_header.remove(node_examples_pulldown)
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]


# if __name__ == "__main__":
#     register()
