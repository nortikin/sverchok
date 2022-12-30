# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import EnumProperty, BoolProperty

from sverchok.utils.logging import info
import sverchok.utils.profile as prof


class SvProfilingToggle(bpy.types.Operator):
    """Toggle profiling on/off"""
    bl_idname = "node.sverchok_profile_toggle"
    bl_label = "Toggle profiling"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        prof.is_currently_enabled = not prof.is_currently_enabled
        info("Profiling is set to %s", prof.is_currently_enabled)

        return {'FINISHED'}


class SvProfileDump(bpy.types.Operator):
    """Dump profiling statistics to log"""
    bl_idname = "node.sverchok_profile_dump"
    bl_label = "Dump profiling statistics to log"
    bl_options = {'INTERNAL'}

    sort_methods = [
        ("tottime", "Internal time", "Internal time (excluding time made in calls to sub-functions)", 0),
        ("cumtime", "Cumulative time", "Cumulative time (including sub-functions)", 1),
        ("calls", "Calls count", "Count of calls of function", 2),
        ("nfl", "Name, file, line", "Function name, file name, line number", 3)
    ]

    sort: EnumProperty(name="Sort by",
                       description="How to sort dumped statistics",
                       items=sort_methods,
                       default="tottime")

    strip_dirs: BoolProperty(name="Strip directories",
                             description="Strip directory path part of file name in the output",
                             default=True)

    def execute(self, context):
        prof.dump_stats(sort=self.sort, strip_dirs=self.strip_dirs)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class SvProfileSave(bpy.types.Operator):
    """Dump profiling statistics to binary file"""
    bl_idname = "node.sverchok_profile_save"
    bl_label = "Dump profiling statistics to binary file"
    bl_options = {'INTERNAL'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        prof.save_stats(self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvProfileReset(bpy.types.Operator):
    """Reset profiling statistics"""
    bl_idname = "node.sverchok_profile_reset"
    bl_label = "Reset profiling statistics"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        prof.reset_stats()
        info("Profiling statistics data cleared.")
        return {'FINISHED'}


classes = [SvProfilingToggle, SvProfileDump, SvProfileSave, SvProfileReset]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in reversed(classes):
        bpy.utils.unregister_class(class_name)
