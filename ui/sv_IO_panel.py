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

import zipfile
import os
import json
from os.path import basename, dirname
from time import localtime, strftime

import bpy

import sverchok
from sverchok.utils.logging import debug, info, warning, error, exception
from sverchok.utils.sv_IO_panel_tools import _EXPORTER_REVISION_
from sverchok.utils.sv_update_utils import version_and_sha
from sverchok.utils import sv_gist_tools
from sverchok.utils.sv_gist_tools import show_token_help, TOKEN_HELP_URL
from sverchok.utils.sv_IO_panel_tools import (
    propose_archive_filepath,
    create_dict_of_tree,
    load_json_from_gist,
    import_tree,
    write_json)
from sverchok.utils.sv_json_export import JSONExporter
from sverchok.utils.sv_json_import import JSONImporter


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

        col.operator('node.tree_export_to_gist', text='Export to GIST', icon='URL')
        col.operator('node.blend_to_archive', text='Archive .blend (zip/gz)')


class SV_PT_IOImportMenu(ExportImportPanels, bpy.types.Panel):
    bl_idname = "SV_PT_IOImportMenu"
    bl_label = "Import"
    bl_parent_id = 'SV_PT_IOLayoutsMenu'

    def draw(self, context):
        col = self.layout.column()

        op = col.operator('node.tree_importer', text='Import JSON file', icon='RNA')
        op.current_tree_name = context.space_data.node_tree.name if context.space_data.node_tree else ''

        op = col.operator('node.tree_import_from_gist', text='Import GIST link', icon='URL')
        op.gist_id = 'clipboard'
        op.id_tree = context.space_data.node_tree.name if context.space_data.node_tree else ''


class SvIOPanelProperties(bpy.types.PropertyGroup):

    def sv_tree_filter(self, context):
        return context.bl_idname == 'SverchCustomTreeType'

    gist_id: bpy.props.StringProperty(
        name='new_gist_id',
        default="Enter Gist ID here",
        description="This gist ID will be used to obtain the RAW .json from github")

    import_tree: bpy.props.PointerProperty(type=bpy.types.NodeTree, poll=sv_tree_filter)


class SvNodeTreeExporter(bpy.types.Operator):

    '''Export will let you pick a .json file name'''

    bl_idname = "node.tree_exporter"
    bl_label = "sv NodeTree Export Operator"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting too",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'})

    id_tree: bpy.props.StringProperty()
    compress: bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.node_tree)

    def execute(self, context):
        ng = bpy.data.node_groups[self.id_tree]

        destination_path = self.filepath
        if not destination_path.lower().endswith('.json'):
            destination_path += '.json'

        # future: should check if filepath is a folder or ends in \

        layout_dict = JSONExporter.get_structure(ng)

        if not layout_dict:
            msg = 'no update list found - didn\'t export'
            self.report({"WARNING"}, msg)
            warning(msg)
            return {'CANCELLED'}

        write_json(layout_dict, destination_path)
        msg = 'exported to: ' + destination_path
        self.report({"INFO"}, msg)
        info(msg)

        if self.compress:
            comp_mode = zipfile.ZIP_DEFLATED

            # destination path = /a../b../c../somename.json
            base = basename(destination_path)  # somename.json
            basedir = dirname(destination_path)  # /a../b../c../

            # somename.zip
            final_archivename = base.replace('.json', '') + '.zip'

            # /a../b../c../somename.zip
            fullpath = os.path.join(basedir, final_archivename)

            with zipfile.ZipFile(fullpath, 'w', compression=comp_mode) as myzip:
                myzip.write(destination_path, arcname=base)
                info('wrote:', final_archivename)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        self.layout.label(text=f'Save node tree "{self.id_tree}" into json:')

        try:
            col = self.layout.column(heading="Options")  # new syntax in >= 2.90
        except TypeError:
            col = self.layout.column()  # old syntax in <= 2.83

        col.use_property_split = True
        col.prop(self, 'compress', text="Create ZIP archive")


class SvNodeTreeImporter(bpy.types.Operator):

    '''Importing operation will let you pick a file to import from'''

    bl_idname = "node.tree_importer"
    bl_label = "sv NodeTree Import Operator"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'})

    current_tree_name: bpy.props.StringProperty()  # from where it was called
    new_nodetree_name: bpy.props.StringProperty()

    def execute(self, context):
        ng = context.scene.io_panel_properties.import_tree
        if not ng:
            self.report(type={'WARNING'}, message="The tree was not chosen, have a look at property (N) panel")
            return {'CANCELLED'}

        importer = JSONImporter.init_from_path(self.filepath)
        importer.import_into_tree(ng)

        # set new node tree to active
        context.space_data.node_tree = ng
        return {'FINISHED'}

    def invoke(self, context, event):
        # it will set current tree as default
        current_tree = bpy.data.node_groups.get(self.current_tree_name)
        context.scene.io_panel_properties.import_tree = current_tree
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        col = self.layout.column()
        col.label(text="Destination tree to import JSON:")
        col.template_ID(context.scene.io_panel_properties, 'import_tree', new='node.new_import_tree')


class SvNodeTreeImportFromGist(bpy.types.Operator):
    ''' Import tree json by link in clipboard (ctrl+C) '''
    bl_idname = "node.tree_import_from_gist"
    bl_label = "sv NodeTree Gist Import Operator"

    id_tree: bpy.props.StringProperty()
    new_nodetree_name: bpy.props.StringProperty()
    gist_id: bpy.props.StringProperty()

    def execute(self, context):
        if not self.id_tree:
            ng_name = self.new_nodetree_name
            ng_params = {
                'name': ng_name or 'unnamed_tree',
                'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
        else:
            ng = bpy.data.node_groups[self.id_tree]

        if self.gist_id == 'clipboard':
            self.gist_id = context.window_manager.clipboard

        nodes_json = load_json_from_gist(self.gist_id.strip(), self)
        if not nodes_json:
            return {'CANCELLED'}

        # import tree and set new node tree to active
        import_tree(ng, nodes_json=nodes_json)
        context.space_data.node_tree = ng
        return {'FINISHED'}


class SvNodeTreeExportToGist(bpy.types.Operator):
    """Export to anonymous gist and copy id to clipboard"""
    bl_idname = "node.tree_export_to_gist"
    bl_label = "Export to GIST (github account)"

    selected_only: bpy.props.BoolProperty(name="Selected only", default=False)

    @classmethod
    def poll(cls, context):
        return bool(context.space_data.node_tree)

    def execute(self, context):
        ng = context.space_data.node_tree
        gist_filename = ng.name

        app_version = bpy.app.version_string.replace(" ", "")
        time_stamp = strftime("%Y.%m.%d | %H:%M", localtime())
        gist_description = f"Sverchok.{version_and_sha} | Blender.{app_version} | {ng.name} | {time_stamp}"

        layout_dict = create_dict_of_tree(ng, skip_set={}, selected=self.selected_only)

        try:
            gist_body = json.dumps(layout_dict, sort_keys=True, indent=2)
        except Exception as err:
            if 'not JSON serializable' in repr(err):
                error(layout_dict)
            exception(err)
            self.report({'WARNING'}, "See terminal/Command prompt for printout of error")
            return {'CANCELLED'}

        try:
            gist_url = sv_gist_tools.main_upload_function(gist_filename, gist_description, gist_body,
                                                          show_browser=False)
            if not gist_url:
                self.report({'ERROR'}, "You have not specified GitHub API access token, which is " +
                            "required to create gists from Sverchok. Please see " +
                            TOKEN_HELP_URL +
                            " for more information.")
                return {'CANCELLED'}

            context.window_manager.clipboard = gist_url  # full destination url
            info(gist_url)
            self.report({'WARNING'}, "Copied gist URL to clipboad")

            sv_gist_tools.write_or_append_datafiles(gist_url, gist_filename)
            return {'FINISHED'}
        except Exception as err:
            exception(err)
            self.report({'ERROR'}, "Error 222: net connection or github login failed!")

        return {'CANCELLED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        addon = context.preferences.addons.get(sverchok.__name__)
        token = addon.preferences.github_token

        col = self.layout.column()
        if not token:
            row_info = col.row(align=True)
            row_info.label(text="You should generate token before importing")
            row_link = row_info.row(align=True)
            row_link.ui_units_x = 2.5
            row_link.operator("node.sv_github_api_token_help", text="Learn", icon='URL')
            col.prop(addon.preferences, "github_token", text="Token")

        try:
            col = self.layout.column(heading="Options")  # new syntax in >= 2.90
        except TypeError:
            col = self.layout.column()  # old syntax in <= 2.83

        col.use_property_split = True
        col.prop(self, 'selected_only')


class SvBlendToArchive(bpy.types.Operator):
    """ Archive this blend file as zip or gz """

    bl_idname = "node.blend_to_archive"
    bl_label = "Archive .blend"

    # _archive_ext: bpy.props.StringProperty(default='zip')
    archive_ext: bpy.props.EnumProperty(items=[(i, i, '') for i in ['zip', 'gz']])

    def complete_msg(self, blend_archive_path):
        msg = 'saved current .blend as archive at ' + blend_archive_path
        self.report({'INFO'}, msg)
        info(msg)

    def execute(self, context):

        blendpath = bpy.data.filepath

        if not blendpath:
            msg = 'you must save the .blend first before we can compress it'
            self.report({'INFO'}, msg)
            return {'CANCELLED'}

        blend_archive_path, blendname = propose_archive_filepath(blendpath, extension=self.archive_ext)
        context.window_manager.clipboard = blend_archive_path

        if self.archive_ext == 'zip':
            with zipfile.ZipFile(blend_archive_path, 'w', zipfile.ZIP_DEFLATED) as myzip:
                myzip.write(blendpath, blendname)
            self.complete_msg(blend_archive_path)
            self.show_selected_in_OSfilebrowsesr(file_path=blend_archive_path)
            return {'FINISHED'}

        elif self.archive_ext == 'gz':

            import gzip
            import shutil

            with open(blendpath, 'rb') as f_in:
                with gzip.open(blend_archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.complete_msg(blend_archive_path)
            self.show_selected_in_OSfilebrowsesr(file_path=blend_archive_path)
            return {'FINISHED'}

        return {'CANCELLED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        try:
            col = self.layout.column(heading="Options")  # new syntax in >= 2.90
        except TypeError:
            col = self.layout.column()  # old syntax in <= 2.83

        col.use_property_split = True
        row = col.row(align=True)
        row.prop(self, 'archive_ext', text="Extension", expand=True)

    @staticmethod
    def show_selected_in_OSfilebrowsesr(file_path):
        if os.name == 'nt':
            import subprocess
            subprocess.Popen(r'explorer /select,"{}"'.format(file_path))


class SvNewImportTree(bpy.types.Operator):
    """Add new tree into node collection for importing json file"""
    bl_idname = "node.new_import_tree"
    bl_label = "Add new SV tree"

    def execute(self, context):
        tree = bpy.data.node_groups.new(name="Import tree", type='SverchCustomTreeType')
        context.scene.io_panel_properties.import_tree = tree
        return {'FINISHED'}


class SvOpenTokenHelpOperator(bpy.types.Operator):
    """Open a wiki page with information about GitHub API tokens creation
    in the browser"""

    bl_idname = "node.sv_github_api_token_help"
    bl_label = "GitHub API token help"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        show_token_help()
        return {'FINISHED'}


classes = [
    SV_PT_IOLayoutsMenu,
    SV_PT_IOExportMenu,
    SV_PT_IOImportMenu,
    SvIOPanelProperties,
    SvNodeTreeExporter,
    SvNodeTreeImporter,
    SvNodeTreeImportFromGist,
    SvNodeTreeExportToGist,
    SvBlendToArchive,
    SvNewImportTree,
    SvOpenTokenHelpOperator
]


def register():
    [bpy.utils.register_class(cls) for cls in classes]
    bpy.types.Scene.io_panel_properties = bpy.props.PointerProperty(type=SvIOPanelProperties)


def unregister():
    del bpy.types.Scene.io_panel_properties
    [bpy.utils.unregister_class(cls) for cls in classes[::-1]]
