# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain
from os.path import basename
from pathlib import Path

import bpy

import sverchok
from sverchok.utils.sv_json_import import JSONImporter


def node_examples_pulldown(self, context):
    if context.space_data.tree_type == 'SverchCustomTreeType':
        layout = self.layout
        row = layout.row(align=True)
        row.scale_x = 1.3
        row.menu("SV_MT_layouts_examples", icon="RNA")


class SV_MT_LayoutsExamples(bpy.types.Menu):
    """Node tree examples"""
    bl_idname = 'SV_MT_layouts_examples'
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Examples"
    bl_description = "List of Sverchok Examples"

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except Exception as err:
            return False

    def draw(self, context):
        for path, category_name in example_categories_names():
            self.layout.menu("SV_MT_PyMenu_" + category_name.replace(' ', '_'))


def make_submenu_classes(path, category_name):
    """Generator of submenus classes"""
    def draw_submenu(self, context):
        """Draw Svershok template submenu"""
        category_path = path / category_name
        self.path_menu(searchpaths=[str(category_path)], operator='node.tree_importer_silent')

    class_name = "SV_MT_PyMenu_" + category_name.replace(' ', '_')

    return type(class_name, (bpy.types.Menu,), {'bl_label': category_name, 'draw': draw_submenu,
                                               'bl_idname': class_name})

extra_examples= dict()
def add_extra_examples(provider, path):
    global extra_examples
    extra_examples[provider] = path

def example_categories_names():
    examples_path = Path(sverchok.__file__).parent / 'json_examples'
    names = []
    for category_path in examples_path.iterdir():
        if category_path.is_dir():
            names.append((examples_path, category_path.name))
    for c in extra_examples:
        for category_path in extra_examples[c].iterdir():
            if category_path.is_dir():
                names.append((extra_examples[c], category_path.name))
    for name in names:
        yield name


class SvNodeTreeImporterSilent(bpy.types.Operator):
    """Importing template tree"""
    bl_idname = "node.tree_importer_silent"
    bl_label = "sv NodeTree Import Silent"

    filepath: bpy.props.StringProperty(  # path to template file got from path_menu
        name="File Path",
        description="File path used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        # if triggered from a non-initialized tree, we first make a tree
        tree = context.space_data.node_tree
        if tree is None:
            tree = bpy.data.node_groups.new(basename(self.filepath), 'SverchCustomTreeType')
            context.space_data.node_tree = tree  # pass this tree to the active node view

        # Deselect everything, so as a result only imported nodes will be selected
        bpy.ops.node.select_all(action='DESELECT')
        JSONImporter.init_from_path(self.filepath).import_into_tree(tree)
        return {'FINISHED'}


classes = [SV_MT_LayoutsExamples, SvNodeTreeImporterSilent]


def register():
    submenu_classes = (make_submenu_classes(path, category_name) for path, category_name in example_categories_names())
    _ = [bpy.utils.register_class(cls) for cls in chain(classes, submenu_classes)]
    bpy.types.NODE_HT_header.append(node_examples_pulldown)


def unregister():
    bpy.types.NODE_HT_header.remove(node_examples_pulldown)
    _ = [bpy.utils.unregister_class(cls) for cls in reversed(classes)]
