# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, BoolProperty, PointerProperty, EnumProperty


class SvIOPanelProperties(bpy.types.PropertyGroup):

    new_nodetree_name: StringProperty(
        name='new_nodetree_name',
        default="Imported tree",
        description="The name to give the new NodeTree, defaults to: Imported")

    compress_output: BoolProperty(
        default=0,
        name='compress_output',
        options={'HIDDEN'},
        description='option to also compress the json, will generate both')

    gist_id: StringProperty(
        name='new_gist_id',
        default="Enter Gist ID here",
        description="This gist ID will be used to obtain the RAW .json from github")

    export_selected_only: BoolProperty(
        name="Selected Only",
        options={'HIDDEN'},
        description="Export selected nodes only",
        default=False)


def register():
    register_class(SvIOPanelProperties)
    bpy.types.Scene.io_panel_properties = PointerProperty(name="io_panel_properties", type=SvIOPanelProperties)


def unregister():
    del bpy.types.Scene.io_panel_properties
    unregister_class(SvIOPanelProperties)
