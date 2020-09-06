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
        return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'


class SV_PT_IOLayoutsMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOLayoutsMenu"
    bl_label = ""
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=f"SV Import/Export  (v {_EXPORTER_REVISION_})")

    def draw(self, context):
        pass


class SV_PT_IOExportMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOExportMenu"
    bl_category = 'Sverchok'
    bl_parent_id = 'SV_PT_IOLayoutsMenu'

    def draw(self, context):
        ntree = context.space_data.node_tree
        io_props = ntree.io_panel_properties

        col = self.layout.column(heading="Options")

        imp = col.operator('node.tree_exporter', text='Export to JSON', icon='FILE_BACKUP')
        imp.id_tree = ntree.name
        imp.compress = io_props.compress_output

        exp = col.operator('node.tree_export_to_gist', text='Export to gist', icon='URL')
        exp.selected_only = io_props.export_selected_only

        col.operator('node.blend_to_archive', text='Archive .blend as .zip').archive_ext = 'zip'
        col.operator('node.blend_to_archive', text='Archive .blend as .gz').archive_ext = 'gz'

        col.use_property_split = True
        col.prop(io_props, 'export_selected_only')
        col.prop(io_props, 'compress_output', text='Zip')


class SV_PT_IOImportMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOImportMenu"
    bl_label = "Import"
    bl_parent_id = 'SV_PT_IOLayoutsMenu'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ntree = context.space_data.node_tree
        io_props = ntree.io_panel_properties

        col = self.layout.column()

        op = col.operator('node.tree_import_from_gist', text='from gist link', icon='URL')
        op.gist_id = 'clipboard'
        op.id_tree = ntree.name

        op = col.operator('node.tree_importer', text='Import into this tree', icon='RNA')
        op.id_tree = ntree.name

        op = col.operator('node.tree_importer', text='Import into new tree', icon='RNA_ADD')
        op.id_tree = ''
        op.new_nodetree_name = io_props.new_nodetree_name

        col.use_property_split = True
        col.prop(io_props, 'new_nodetree_name', text='Tree name:')


register, unregister = bpy.utils.register_classes_factory([SV_PT_IOLayoutsMenu, SV_PT_IOExportMenu, SV_PT_IOImportMenu])
