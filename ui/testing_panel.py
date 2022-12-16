# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from itertools import chain
from pathlib import Path

import bpy
import sverchok
from sverchok import old_nodes
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.modules_inspection import iter_submodule_names
from sverchok.utils.logging import info


class SvRunTests(bpy.types.Operator):
    """
    Run all tests.
    """

    bl_idname = "node.sv_testing_run_tests"
    bl_label = "Run tests"
    bl_options = {'INTERNAL'}

    test_module: bpy.props.EnumProperty(
        name="Module to test",
        description="Pick up which module to test",
        items=[(i, i, '') for i in
               chain(['All'], iter_submodule_names(Path(sverchok.__file__).parent / 'tests', depth=1))])

    def execute(self, context):
        import sverchok.utils.testing as test  # for startup performance
        if self.test_module == 'All':
            # making self.report after all tests lead to strange error, so no report for testing all
            test.run_all_tests()
        else:
            test_result = test.run_test_from_file(self.test_module + '.py')
            self.report(type={'ERROR'} if test_result != 'OK' else {'INFO'}, message=test_result)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SvDumpNodeDef(bpy.types.Operator):
    """
    Print definition of selected node to stdout.
    This works correctly only for simple cases!
    """

    bl_idname = "node.sv_testing_dump_node_def"
    bl_label = "Dump node definition"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.edit_tree)

    def execute(self, context):
        ntree = context.space_data.node_tree
        selection = list(filter(lambda n: n.select, ntree.nodes)) if ntree else []
        if len(selection) != 1:
            self.report({'ERROR'}, "Exactly one node must be selected!")
            return {'CANCELLED'}

        node = selection[0]
        from sverchok.utils.testing import generate_node_definition  # for startup performance
        print(generate_node_definition(node))
        self.report({'INFO'}, "See console")

        return {'FINISHED'}


class SvListOldNodes(bpy.types.Operator):
    """
    Print names and bl_idnames of all
    deprecated nodes (old_nodes) in the current
    node tree.
    """

    bl_idname = "node.sv_testing_list_old_nodes"
    bl_label = "List old nodes"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.edit_tree)

    def execute(self, context):
        ntree = context.space_data.node_tree

        for node in ntree.nodes:
            if old_nodes.is_old(node):
                info("Deprecated node: `%s' (%s)", node.name, node.bl_idname)

        self.report({'INFO'}, "See logs")
        return {'FINISHED'}


class SV_PT_TestingPanel(bpy.types.Panel):
    bl_idname = "SV_PT_TestingPanel"
    bl_label = "SV Testing"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    bl_order = 8
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            if context.space_data.tree_type != 'SverchCustomTreeType':
                return False
            with sv_preferences() as prefs:
                return prefs.developer_mode
        except:
            return False

    def draw(self, context):
        layout = self.layout
        layout.operator("node.sv_testing_run_tests")
        layout.operator("node.sv_testing_list_old_nodes")
        layout.operator("node.sv_testing_dump_node_def")


classes = [SvRunTests, SvDumpNodeDef, SvListOldNodes, SV_PT_TestingPanel]


def register():
    for clazz in classes:
        bpy.utils.register_class(clazz)


def unregister():
    for clazz in reversed(classes):
        bpy.utils.unregister_class(clazz)
