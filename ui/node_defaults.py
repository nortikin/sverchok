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

import os
import json

import bpy
from bpy.props import CollectionProperty, BoolProperty, StringProperty


# condidate for library (also defined in development.py)
def displaying_sverchok_nodes(context):
    return context.space_data.tree_type in {'SverchCustomTreeType', 'SverchGroupTreeType'}

def get_cache_dict(collection):
    return {item.var_name: item.store for item in collection.values()}

def ensure_node_defaults_folder():

    dirpath = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    node_defaults_path = os.path.join(dirpath, 'node_defaults')
    fullpath = os.path.join(node_defaults_path, 'deviations.json')
    
    # create node_defaults_path if it doesn't exist
    if not os.path.exists(node_defaults_path):
        os.mkdir(node_defaults_path)
    
    if not os.path.exists(fullpath):
        with open(fullpath, 'w') as _:
            pass

    return fullpath


class SvRestoreADefault(bpy.types.Operator):

    bl_idname = "node.sv_restore_a_default"
    bl_label = "Restore a default"

    prop_name = StringProperty()

    def execute(self, context):
        node = context.active_node
        node.property_unset(self.prop_name)

        # simple way to trigger draw_buttons, a kludge for now
        node.width = node.width

        bpy.ops.node.sv_get_node_defaults_deviations()
        return {'FINISHED'}


class SvSaveNodeDefaults(bpy.types.Operator):

    bl_idname = "node.sv_save_node_defaults"
    bl_label = "Save as defaults"

    # store_bl_idname = bpy.props.StringProperty(default='')

    def execute(self, context):
        fullpath = ensure_node_defaults_folder()
        with open(fullpath, 'w') as json_data:
            try:
                d = json.load(json_data)
            except:
                print('start new defaults file')
            node = context.active_node
            collection = node.id_data.SvNodeDefaultBools
            # .... yikes.

        return {'FINISHED'}


class SvNodeDefaultsBooleans(bpy.types.PropertyGroup):
    store = bpy.props.BoolProperty(name="store", default=False)
    show_name = bpy.props.StringProperty(name="show name", default="")
    var_name = bpy.props.StringProperty(name="var name", default="")


class SvGetNodeDefaultsDeviations(bpy.types.Operator):
    """ Get all values that deviate from the node's factory defaults """
    bl_idname = "node.sv_get_node_defaults_deviations"
    bl_label = "Get Node Snapshot"

    node_name = bpy.props.StringProperty(default='')
    node_tree_name = bpy.props.StringProperty(default='')

    def execute(self, context):

        node = context.active_node
        node.id_data.sv_configure_defaults = True
        collection = node.id_data.SvNodeDefaultBools
        cached_store_values = get_cache_dict(collection)    # doesn't yet test active node bl_idname
        collection.clear()

        for prop_name, prop_val in node.items():
            if prop_name == 'n_id':
                continue

            show_name = node.bl_rna.properties[prop_name].name or prop_name
            item = collection.add()
            item.name = node.bl_idname
            item.show_name = show_name
            item.var_name = prop_name
            item.store = cached_store_values.get(item.var_name) or False

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

    icon_to_show = ["RIGHTARROW", "DOWNARROW_HLT"][show]
    row.label(icon=icon_to_show)
    row.operator("node.sv_get_node_defaults_deviations")

    if show == False:
        return

    for item in node.id_data.SvNodeDefaultBools:
        if not item.name == bl_idname:
            # this is frowned upon.. setting from within a draw function.. but it's allowed!
            node.id_data.sv_configure_defaults = False
            return # break
        row = box.row(align=True)
        split = row.split(0.7)
        r1 = split.row()
        r1.enabled = False
        # row.label(item.show_name + ':')
        r1.prop(node, item.var_name)
        r2 = split.split().row()
        r2.prop(item, 'store', text='')
        r2.operator('node.sv_restore_a_default', text='', icon='X').prop_name=item.var_name

    row = box.row()
    row.operator("node.sv_save_node_defaults")
    row.prop(node.id_data, 'sv_configure_defaults', text='close tab', toggle=True, icon='X')


def register():
    bpy.utils.register_class(SvRestoreADefault)
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
    bpy.utils.unregister_class(SvRestoreADefault)
    del bpy.types.SverchCustomTreeType.sv_configure_defaults
    del bpy.types.SverchCustomTreeType.SvNodeDefaultBools
