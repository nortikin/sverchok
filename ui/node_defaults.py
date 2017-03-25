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

import bpy
import os

from bpy.props import CollectionProperty, BoolProperty


# condidate for library (also defined in development.py)
def displaying_sverchok_nodes(context):
    return context.space_data.tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}



class SvSaveNodeDefaults(bpy.types.Operator):

    bl_idname = "node.sv_save_node_defaults"
    bl_label = "Save as defaults"

    store_bl_idname = bpy.props.StringProperty(default='')

    def execute(self, context):
        # write store_bl_idname / props
        return {'FINISHED'}


class SvNodeDefaultsBooleans(bpy.types.PropertyGroup):
    store = bpy.props.BoolProperty(name="store", default=False)
    name = bpy.props.StringProperty(name="name", default="")
    var_name = bpy.props.StringProperty(name="name", default="")


class SvGetNodeDefaultsDeviations(bpy.types.Operator):

    bl_idname = "node.sv_get_node_defaults_deviations"
    bl_label = "Get deviations from default values"

    store_bl_idname = bpy.props.StringProperty(default='')

    def execute(self, context):
        # write store_bl_idname / props
        self.dynamic_strings.add().line = ""
        node = context.active_node
        collection = node.bl_id_data.SvNodeDefaultBools
        collection.clear()   # could cache? else each press of this button will untick bools..

        for prop_name, prop_val in node.items():
            if prop_name == 'n_id':
                continue

            show_name = node.bl_rna.properties[prop_name].name or prop_name
            item = collection.add()
            item.name = show_name
            item.var_name = prop_name
            item.store = False

        return {'FINISHED'}



def node_default_deviations_draw(self, context):
    if not displaying_sverchok_nodes(context):
        return
    layout = self.layout

    node = context.active_node
    if not node:
        return
    bl_idname = node.bl_idname

    show = node.id_data.sv_configure_defaults
    box = layout.box()
    row = box.row()
    row.label(icon=["RIGHTARROW", "DOWNARROW_HLT"][show])
    row.prop(node.id_data, 'sv_configure_defaults', text='configure defaults')

    if show == False:
        return

    row = box.row(align=True)
    row.operator("node.sv_get_node_defaults_deviations")

    # this will instead display the content of  SvNodeDefaultsBooleans(PropertyGroup)
    # soon.
    for prop_name, prop_val in node.items():
        if prop_name == 'n_id':
            continue
        row = box.row(align=True)
        show_name = node.bl_rna.properties[prop_name].name or prop_name
        row.enabled = False
        row.label(show_name + ':')
        row.prop(node, prop_name)

    row = box.row()
    row.operator("node.sv_save_node_defaults")


def register():
    bpy.utils.register_class(SvSaveNodeDefaults)
    bpy.utils.register_class(SvGetNodeDefaultsDeviations)
    bpy.utils.register_class(SvNodeDefaultsBooleans)
    bpy.types.SverchCustomTreeType.SvNodeDefaultBools = CollectionProperty(type=SvNodeDefaultsBooleans)
    bpy.types.SverchCustomTreeType.sv_configure_defaults = BoolProperty()
    bpy.types.NODE_PT_active_node_generic.append(node_default_deviations_draw)



def unregister():
    bpy.types.NODE_PT_active_node_generic.remove(node_default_deviations_draw)
    bpy.utils.unregister_class(SvSaveNodeDefaults)
    bpy.utils.unregister_class(SvGetNodeDefaultsDeviations)
    bpy.utils.unregister_class(SvNodeDefaultsBooleans)
    del bpy.types.SverchCustomTreeType.sv_configure_defaults
    del bpy.types.SverchCustomTreeType.SvNodeDefaultBools