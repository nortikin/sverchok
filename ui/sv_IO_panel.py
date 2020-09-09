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

from sverchok.utils.sv_IO_panel_tools import _EXPORTER_REVISION_


class ExportImportPanels:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'

    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


class SV_PT_IOLayoutsMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOLayoutsMenu"
    bl_label = f"Import/Export  (v {_EXPORTER_REVISION_})"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):
        pass


class SV_PT_IOExportMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOExportMenu"
    bl_label = "Export"
    bl_category = 'Sverchok'
    bl_parent_id = 'SV_PT_IOLayoutsMenu'

    def draw(self, context):
        col = self.layout.column()

        imp = col.operator('node.tree_exporter', text='Export to JSON', icon='FILE_BACKUP')
        imp.id_tree = context.space_data.node_tree.name if context.space_data.node_tree else ''

        col.operator('node.tree_export_to_gist', text='Export to gist', icon='URL')
        col.operator('node.blend_to_archive', text='Save .blend')


class SV_PT_IOImportMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOImportMenu"
    bl_label = "Import"
    bl_parent_id = 'SV_PT_IOLayoutsMenu'

    def draw(self, context):
        col = self.layout.column()

        op = col.operator('node.tree_import_from_gist', text='Import GIST link', icon='URL')
        op.gist_id = 'clipboard'
        op.id_tree = context.space_data.node_tree.name if context.space_data.node_tree else ''

        op = col.operator('node.tree_importer', text='Import JSON file', icon='RNA')
        op.current_tree_name = context.space_data.node_tree.name if context.space_data.node_tree else ''


class SvIOPanelProperties(bpy.types.PropertyGroup):

    def sv_tree_filter(self, context):
        return context.bl_idname == 'SverchCustomTreeType'

    gist_id: bpy.props.StringProperty(
        name='new_gist_id',
        default="Enter Gist ID here",
        description="This gist ID will be used to obtain the RAW .json from github")

    import_tree: bpy.props.PointerProperty(type=bpy.types.NodeTree, poll=sv_tree_filter)


classes = [SV_PT_IOLayoutsMenu, SV_PT_IOExportMenu, SV_PT_IOImportMenu, SvIOPanelProperties]


def register():
    [bpy.utils.register_class(cls) for cls in classes]
    bpy.types.Scene.io_panel_properties = bpy.props.PointerProperty(type=SvIOPanelProperties)


def unregister():
    del bpy.types.Scene.io_panel_properties
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
