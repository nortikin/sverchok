# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from os.path import basename

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty

from sverchok.utils.sv_IO_panel_tools import import_tree


class SvNodeTreeImporterSilent(bpy.types.Operator):

    '''Importing operation just do it!'''

    bl_idname = "node.tree_importer_silent"
    bl_label = "sv NodeTree Import Silent"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    id_tree: StringProperty()

    def execute(self, context):

        # print(self.id_tree, self.filepath)

        # if triggered from a non-initialized tree, we first make a tree
        if self.id_tree == '____make_new____':
            ng_params = {
                'name': basename(self.filepath),
                'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)

            # pass this tree to the active nodeview
            context.space_data.node_tree = ng

        else:

            ng = bpy.data.node_groups[self.id_tree]

        # Deselect everything, so as a result only imported nodes
        # will be selected
        bpy.ops.node.select_all(action='DESELECT')
        import_tree(ng, self.filepath)
        context.space_data.node_tree = ng
        return {'FINISHED'}


classes = [SvNodeTreeImporterSilent]


def register():
    _ = [register_class(cls) for cls in classes]


def unregister():
    _ = [unregister_class(cls) for cls in classes[::-1]]
