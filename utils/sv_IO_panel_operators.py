# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import zipfile
import json
import os
from os.path import basename, dirname

import bpy
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, BoolProperty

from sverchok.utils import sv_gist_tools
from sverchok.utils.sv_IO_panel_tools import (
    propose_archive_filepath,
    create_dict_of_tree,
    load_json_from_gist,
    import_tree,
    write_json)
from sverchok.utils.sv_gist_tools import show_token_help, TOKEN_HELP_URL
from sverchok.utils.logging import debug, info, warning, error, exception


# pylint: disable=w0613

class SvNodeTreeExporter(bpy.types.Operator):

    '''Export will let you pick a .json file name'''

    bl_idname = "node.tree_exporter"
    bl_label = "sv NodeTree Export Operator"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting too",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'})

    id_tree: StringProperty()
    compress: BoolProperty()

    def execute(self, context):
        ng = bpy.data.node_groups[self.id_tree]

        destination_path = self.filepath
        if not destination_path.lower().endswith('.json'):
            destination_path += '.json'

        # future: should check if filepath is a folder or ends in \

        layout_dict = create_dict_of_tree(ng)
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


class SvNodeTreeImporter(bpy.types.Operator):

    '''Importing operation will let you pick a file to import from'''

    bl_idname = "node.tree_importer"
    bl_label = "sv NodeTree Import Operator"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob: StringProperty(
        default="*.json",
        options={'HIDDEN'})

    id_tree: StringProperty()
    new_nodetree_name: StringProperty()

    def execute(self, context):
        if not self.id_tree:
            ng_name = self.new_nodetree_name
            ng_params = {
                'name': ng_name or 'unnamed_tree',
                'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
        else:
            ng = bpy.data.node_groups[self.id_tree]
        import_tree(ng, self.filepath)

        # set new node tree to active
        context.space_data.node_tree = ng
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvNodeTreeImportFromGist(bpy.types.Operator):
    ''' Import tree json by link in clipboard (ctrl+C) '''
    bl_idname = "node.tree_import_from_gist"
    bl_label = "sv NodeTree Gist Import Operator"

    id_tree: StringProperty()
    new_nodetree_name: StringProperty()
    gist_id: StringProperty()

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
    bl_label = "sv NodeTree Gist Export Operator"

    selected_only: BoolProperty(name="Selected only", default=False)

    def execute(self, context):
        ng = context.space_data.node_tree
        gist_filename = ng.name
        gist_description = 'to do later? 2018'
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
            gist_url = sv_gist_tools.main_upload_function(gist_filename, gist_description, gist_body, show_browser=False)
            if not gist_url:
                self.report({'ERROR'}, "You have not specified GitHub API access token, which is " +
                                "required to create gists from Sverchok. Please see " +
                                TOKEN_HELP_URL +
                                " for more information.")
                return {'CANCELLED'}
            
            context.window_manager.clipboard = gist_url   # full destination url
            info(gist_url)
            self.report({'WARNING'}, "Copied gist URL to clipboad")

            sv_gist_tools.write_or_append_datafiles(gist_url, gist_filename)
            return {'FINISHED'}
        except Exception as err:
            exception(err)
            self.report({'ERROR'}, "Error 222: net connection or github login failed!")

        return {'CANCELLED'}


def show_selected_in_OSfilebrowsesr(file_path):
    if os.name == 'nt':
        import subprocess
        subprocess.Popen(r'explorer /select,"{}"'.format(file_path))



class SvBlendToArchive(bpy.types.Operator):
    """ Archive this blend file as zip or gz """

    bl_idname = "node.blend_to_archive"
    bl_label = "Archive .blend"

    archive_ext: bpy.props.StringProperty(default='zip')
    

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
            show_selected_in_OSfilebrowsesr(file_path=blend_archive_path)
            return {'FINISHED'}

        elif self.archive_ext == 'gz':

            import gzip
            import shutil

            with open(blendpath, 'rb') as f_in:
                with gzip.open(blend_archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.complete_msg(blend_archive_path)
            show_selected_in_OSfilebrowsesr(file_path=blend_archive_path)
            return {'FINISHED'}

        return {'CANCELLED'}

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
    SvNodeTreeExporter,
    SvNodeTreeExportToGist,
    SvNodeTreeImporter,
    SvNodeTreeImporterSilent,
    SvNodeTreeImportFromGist,
    SvBlendToArchive,
    SvOpenTokenHelpOperator
]


def register():
    _ = [register_class(cls) for cls in classes]


def unregister():
    _ = [unregister_class(cls) for cls in classes[::-1]]
