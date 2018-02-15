# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils import logging

# pylint: disable=w0702

def add_named(prop_collection, name):
    prop_collection.add().name = name.strip()

def get_branch_list_online(self):
    """
    This function returns the branch names as found on issue 2053, as a list.
    """
    try:
        import requests

        comment_url = "https://api.github.com/repos/nortikin/sverchok/issues/2053#issuecomment-1"
        r = requests.get(comment_url)

        string_to_parse = r.json().get('body')
        string_to_parse = string_to_parse.replace('- ', '')
        named_branches = string_to_parse.split('\r\n')

    except Exception as err:

        logging.info("get_branch_list_online <-- error:\n " + err)
        named_branches = []
        self.report({'ERROR'}, "branch list not populated")

    return named_branches


class SvBranchOpPopulateBranchList(bpy.types.Operator):

    bl_idname = "node.sv_populate_branch_list"
    bl_label = "Populate Branch List"

    def execute(self, context):

        with sv_preferences() as prefs:
            prefs.branch_list.clear()
            prefs.selected_branch = ""

            _ = [add_named(prefs.branch_list, n) for n in get_branch_list_online(self)]

            if not prefs.branch_list:
                return {'CANCELLED'}

        return {'FINISHED'}

class SvBranchOpPickAlternativeBranch(bpy.types.Operator):

    bl_idname = "node.sv_pick_alternative_branch"
    bl_label = "Switch to selected branch"

    fn_name = bpy.props.StringProperty()

    def execute(self, context):
        
        if self.fn_name == 'PANIC':
            with sv_preferences() as prefs:
                prefs.branch_list.clear()
                prefs.selected_branch = ""

        bpy.node.sverchok_update_addon()
        return {'FINISHED'}


classes = [SvBranchOpPopulateBranchList, SvBranchOpPickAlternativeBranch]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
