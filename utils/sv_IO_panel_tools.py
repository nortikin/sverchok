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
from time import gmtime, strftime

import bpy
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy.utils import register_class, unregister_class

from sverchok import old_nodes
from sverchok.utils import sv_gist_tools, sv_iodict_builder
from sverchok.utils.sv_IO_monad_helpers import unpack_monad
from sverchok.utils.logging import debug, info, warning, error, exception

# pylint: disable=c0325

def perform_scripted_node_inject(node, node_ref):
    '''
    Scripted Node will no longer create alternative versions of a file.
    If a scripted node wants to make a file called 'inverse.py' and the
    current .blend already contains such a file, then for simplicity the
    importer will not try to create 'inverse.001.py' and reference that.
    It will instead do nothing and assume the existing python file is
    functionally the same.

    If you have files that work differently but have the same name, stop.

    '''
    texts = bpy.data.texts
    params = node_ref.get('params')
    if params:

        script_name = params.get('script_name')
        script_content = params.get('script_str')

        if script_name and not (script_name in texts):
            new_text = texts.new(script_name)
            new_text.from_string(script_content)
        elif script_name and (script_name in texts):
            # This was added to fix existing texts with the same name but no / different content.
            if texts[script_name].as_string() == script_content:
                debug("SN skipping text named `%s' - their content are the same", script_name)
            else:
                info("SN text named `%s' already found in current, but content differs", script_name)
                new_text = texts.new(script_name)
                new_text.from_string(script_content)
                script_name = new_text.name
                info('SN text named replaced with %s', script_name)

        node.script_name = script_name
        node.script_str = script_content

    if node.bl_idname == 'SvScriptNode':
        node.user_name = "templates"               # best would be in the node.
        node.files_popup = "sv_lang_template.sn"   # import to reset easy fix
        node.load()
    elif node.bl_idname == 'SvScriptNodeLite':
        node.load()
        # node.storage_set_data(node_ref)
    else:
        node.files_popup = node.avail_templates(None)[0][0]
        node.load()


def perform_profile_node_inject(node, node_ref):
    texts = bpy.data.texts
    new_text = texts.new(node_ref['params']['filename'])
    new_text.from_string(node_ref['path_file'])
    node.update()


def perform_svtextin_node_object(node, node_ref):
    '''
    as it's a beta service, old IO json may not be compatible - in this interest
    of neat code we assume it finds everything.
    '''
    texts = bpy.data.texts
    params = node_ref.get('params')
    current_text = params['current_text']

    # it's not clear from the exporter code why textmode parameter isn't stored
    # in params.. for now this lets us look in both places. ugly but whatever.
    textmode = params.get('textmode')
    if not textmode:
        textmode = node_ref.get('textmode')
    node.textmode = textmode

    if not current_text:
        info("`%s' doesn't store a current_text in params", node.name)

    elif not current_text in texts:
        new_text = texts.new(current_text)
        text_line_entry = node_ref['text_lines']

        if node.textmode == 'JSON':
            if isinstance(text_line_entry, str):
                debug('loading old text json content / backward compatibility mode')
            elif isinstance(text_line_entry, dict):
                text_line_entry = json.dumps(text_line_entry['stored_as_json'])

        new_text.from_string(text_line_entry)

    else:
        # reaches here if  (current_text) and (current_text in texts)
        # can probably skip this..
        # texts[current_text].from_string(node_ref['text_lines'])
        debug('%s seems to reuse a text block loaded by another node - skipping', node.name)


def apply_superficial_props(node, node_ref):
    '''
    copies the stored values from the json onto the new node's corresponding values.
    '''
    props = ['location', 'height', 'width', 'label', 'hide']
    for p in props:
        setattr(node, p, node_ref[p])

    if node_ref.get('use_custom_color'):
        node.use_custom_color = True
        node.color = node_ref.get('color', (1, 1, 1))


def gather_remapped_names(node, n, name_remap):
    '''
    When n is assigned to node.name, blender will decide whether or
    not it can do that, if there exists already a node with that name,
    then the assignment to node.name is not n, but n.00x. Hence on the
    following line we check if the assignment was accepted, and store a
    remapped name if it wasn't.
    '''
    node.name = n
    if not (node.name == n):
        name_remap[n] = node.name


def apply_core_props(node, node_ref):
    params = node_ref['params']
    if 'cls_dict' in params:
        return
    for p in params:
        val = params[p]
        try:
            setattr(node, p, val)
        except Exception as e:
            # FIXME: this is ugly, need to find better approach
            error_message = repr(e)  # for reasons
            error(error_message)
            msg = 'failed to assign value to the node'
            debug("`%s': %s = %s: %s", node.name, p, val, msg)
            if "val: expected sequence items of type boolean, not int" in error_message:
                debug("going to convert a list of ints to a list of bools and assign that instead")
                setattr(node, p, [bool(i) for i in val])


def apply_socket_props(socket, socket_info):
    debug("applying socket props")
    for tracked_prop_name, tracked_prop_value in socket_info.items():
        try:
            setattr(socket, tracked_prop_name, tracked_prop_value)

        except Exception as err:
            error("Error while setting node socket: %s | %s", socket.node.name, socket.index)
            error("the following failed | %s <- %s", tracked_prop_name, tracked_prop_value)
            exception(err)


def apply_custom_socket_props(node, node_ref):
    debug("applying node props for node: %s", node.bl_idname)
    socket_properties = node_ref.get('custom_socket_props')
    if socket_properties:
        for idx, socket_info in socket_properties.items():
            try:
                socket = node.inputs[int(idx)]
                apply_socket_props(socket, socket_info)
            except Exception as err:
                error("socket index: %s, trying to pass: %s, num_sockets: %s", idx, socket_info, len(node.inputs))
                exception(err)


def add_texts(node, node_ref):
    if node.bl_idname in sv_iodict_builder.SCRIPTED_NODES:
        perform_scripted_node_inject(node, node_ref)

    elif node.bl_idname in sv_iodict_builder.PROFILE_NODES:
        perform_profile_node_inject(node, node_ref)

    elif (node.bl_idname in {'SvTextInNode', 'SvTextInNodeMK2'}):
        perform_svtextin_node_object(node, node_ref)


def apply_post_processing(node, node_ref):
    '''
    Nodes that require post processing to work properly
    '''
    if node.bl_idname in {'SvGroupInputsNode', 'SvGroupOutputsNode', 'SvTextInNode', 'SvTextInNodeMK2'}:
        node.load()
    elif node.bl_idname in {'SvGroupNode'}:
        node.load()
        group_name = node.group_name
        node.group_name = group_name_remap.get(group_name, group_name)
    elif node.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'}:
        socket_kinds = node_ref.get(node.node_kind)
        node.repopulate(socket_kinds)


def add_node_to_tree(nodes, n, nodes_to_import, name_remap, create_texts):
    node_ref = nodes_to_import[n]
    bl_idname = node_ref['bl_idname']

    try:
        if old_nodes.is_old(bl_idname):
            old_nodes.register_old(bl_idname)

        if bl_idname == 'SvMonadGenericNode':
            node = unpack_monad(nodes, node_ref)
            if not node:
                raise Exception("It seems no valid node was created for this Monad {0}".format(node_ref))
        else:
            node = nodes.new(bl_idname)

    except Exception as err:
        exception(err)
        error('%s not currently registered, skipping', bl_idname)
        return

    if create_texts:
        add_texts(node, node_ref)

    if hasattr(node, 'storage_set_data'):
        node.storage_set_data(node_ref)

    if bl_idname == 'SvObjectsNodeMK3':
        for named_object in node_ref.get('object_names', []):
            node.object_names.add().name = named_object

    gather_remapped_names(node, n, name_remap)
    apply_core_props(node, node_ref)
    apply_superficial_props(node, node_ref)
    apply_post_processing(node, node_ref)
    apply_custom_socket_props(node, node_ref)


def add_nodes(ng, nodes_to_import, nodes, create_texts):
    '''
    return the dictionary that tracks which nodes got renamed due to conflicts.
    setting 'ng.limited_init' supresses any custom defaults associated with nodes in the json.
    '''
    name_remap = {}
    ng.limited_init = True
    try:
        for n in sorted(nodes_to_import):
            add_node_to_tree(nodes, n, nodes_to_import, name_remap, create_texts)
    except Exception as err:
        exception(err)

    ng.limited_init = False
    return name_remap


def add_groups(groups_to_import):
    '''
    return the dictionary that tracks which groups got renamed due to conflicts
    '''
    group_name_remap = {}
    for name in groups_to_import:
        group_ng = bpy.data.node_groups.new(name, 'SverchGroupTreeType')
        if group_ng.name != name:
            group_name_remap[name] = group_ng.name
        import_tree(group_ng, '', groups_to_import[name])
    return group_name_remap


def print_update_lists(update_lists):
    debug('update lists:')
    for ulist in update_lists:
        debug(ulist)


def place_frames(ng, nodes_json, name_remap):
    finalize = lambda name: name_remap.get(name, name)
    framed_nodes = nodes_json['framed_nodes']
    for node_name, parent in framed_nodes.items():
        ng.nodes[finalize(node_name)].parent = ng.nodes[finalize(parent)]


def import_tree(ng, fullpath='', nodes_json=None, create_texts=True):

    nodes = ng.nodes
    ng.use_fake_user = True

    def resolve_socket(from_node, from_socket, to_node, to_socket, name_dict={}):
        f_node = name_dict.get(from_node, from_node)
        t_node = name_dict.get(to_node, to_node)
        return (ng.nodes[f_node].outputs[from_socket],
                ng.nodes[t_node].inputs[to_socket])

    def make_links(update_lists, name_remap):
        print_update_lists(update_lists)

        failed_connections = []
        for link in update_lists:
            try:
                ng.links.new(*resolve_socket(*link, name_dict=name_remap))
            except Exception as err:
                exception(err)
                failed_connections.append(link)
                continue

        if failed_connections:
            error("failed total: %s", len(failed_connections))
            error(failed_connections)
        else:
            debug('no failed connections! awesome.')

    def generate_layout(fullpath, nodes_json):
        '''cummulative function '''

        # it may be necessary to store monads as dicts instead of string/json
        # this will handle both scenarios
        if isinstance(nodes_json, str):
            nodes_json = json.loads(nodes_json)
            debug('==== loading monad ====')
        info(('#' * 12) + nodes_json['export_version'])

        ''' create all nodes and groups '''

        update_lists = nodes_json['update_lists']
        nodes_to_import = nodes_json['nodes']
        groups_to_import = nodes_json.get('groups', {})

        add_groups(groups_to_import)  # this return is not used yet
        name_remap = add_nodes(ng, nodes_to_import, nodes, create_texts)

        ''' now connect them '''

        # prevent unnecessary updates
        ng.freeze(hard=True)
        make_links(update_lists, name_remap)

        ''' set frame parents '''

        place_frames(ng, nodes_json, name_remap)

        ''' clean up '''

        old_nodes.scan_for_old(ng)
        ng.unfreeze(hard=True)
        ng.update()

    ''' ---- read files (.json or .zip) or straight json data----- '''

    if fullpath.endswith('.zip'):
        nodes_json = get_file_obj_from_zip(fullpath)
        generate_layout(fullpath, nodes_json)

    elif fullpath.endswith('.json'):
        with open(fullpath) as fp:
            nodes_json = json.load(fp)
            generate_layout(fullpath, nodes_json)

    elif nodes_json:
        generate_layout('', nodes_json)


class SvNodeTreeExporter(bpy.types.Operator):

    '''Export will let you pick a .json file name'''

    bl_idname = "node.tree_exporter"
    bl_label = "sv NodeTree Export Operator"

    filepath = StringProperty(
        name="File Path",
        description="Filepath used for exporting too",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob = StringProperty(
        default="*.json",
        options={'HIDDEN'})

    id_tree = StringProperty()
    compress = BoolProperty()

    def execute(self, context):
        ng = bpy.data.node_groups[self.id_tree]

        destination_path = self.filepath
        if not destination_path.lower().endswith('.json'):
            destination_path += '.json'

        # future: should check if filepath is a folder or ends in \

        layout_dict = sv_iodict_builder.create_dict_of_tree(ng)
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

    filepath = StringProperty(
        name="File Path",
        description="Filepath used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    id_tree = StringProperty()

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

    filepath = StringProperty(
        name="File Path",
        description="Filepath used to import from",
        maxlen=1024, default="", subtype='FILE_PATH')

    filter_glob = StringProperty(
        default="*.json",
        options={'HIDDEN'})

    id_tree = StringProperty()
    new_nodetree_name = StringProperty()

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

    bl_idname = "node.tree_import_from_gist"
    bl_label = "sv NodeTree Gist Import Operator"

    id_tree = StringProperty()
    new_nodetree_name = StringProperty()
    gist_id = StringProperty()

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

        nodes_json = sv_gist_tools.load_json_from_gist(self.gist_id.strip(), self)
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

    selected_only = BoolProperty(name = "Selected only", default=False)

    def execute(self, context):
        ng = context.space_data.node_tree
        gist_filename = ng.name
        gist_description = 'to do later?'
        layout_dict = sv_iodict_builder.create_dict_of_tree(ng, skip_set={}, selected=self.selected_only)

        try:
            gist_body = json.dumps(layout_dict, sort_keys=True, indent=2)
        except Exception as err:
            if 'not JSON serializable' in repr(err):
                error(layout_dict)
            else:
                exception(err)
            self.report({'WARNING'}, "See terminal/Command prompt for printout of error")
            return {'CANCELLED'}

        try:
            gist_url = sv_gist_tools.main_upload_function(gist_filename, gist_description, gist_body, show_browser=False)
            context.window_manager.clipboard = gist_url   # full destination url
            info(gist_url)
            self.report({'WARNING'}, "Copied gistURL to clipboad")

            sv_gist_tools.write_or_append_datafiles(gist_url, gist_filename)

        except:
            self.report({'ERROR'}, "Error uploading the gist, check your internet connection!")
        finally:
            return {'FINISHED'}


def propose_archive_filepath(blendpath, extension='zip'):
    """ disect existing filepath, add timestamp """
    blendname = os.path.basename(blendpath)
    blenddir = os.path.dirname(blendpath)
    blendbasename = blendname.split('.')[0]
    raw_time_stamp = strftime("%Y_%m_%d_%H_%M", gmtime())
    archivename = blendbasename + '_' + raw_time_stamp + '.' + extension

    return os.path.join(blenddir, archivename), blendname


class SvBlendToArchive(bpy.types.Operator):
    """ Archive this blend file as zip or gz """

    bl_idname = "node.blend_to_archive"
    bl_label = "Archive .blend"

    archive_ext = bpy.props.StringProperty(default='zip')
    

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
            return {'FINISHED'}

        elif self.archive_ext == 'gz':

            import gzip
            import shutil

            with open(blendpath, 'rb') as f_in:
                with gzip.open(blend_archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            self.complete_msg(blend_archive_path)
            return {'FINISHED'}

        return {'CANCELLED'}


class SvIOPanelProperties(bpy.types.PropertyGroup):

    new_nodetree_name = StringProperty(
        name='new_nodetree_name',
        default="Imported_name",
        description="The name to give the new NodeTree, defaults to: Imported")

    compress_output = BoolProperty(
        default=0,
        name='compress_output',
        description='option to also compress the json, will generate both')

    gist_id = StringProperty(
        name='new_gist_id',
        default="Enter Gist ID here",
        description="This gist ID will be used to obtain the RAW .json from github")

    io_options_enum = bpy.props.EnumProperty(
        items=[("Import", "Import", "", 0), ("Export", "Export", "", 1)],
        description="display import or export",
        default="Export"
    )

    export_selected_only = BoolProperty(
        name = "Selected Only",
        description = "Export selected nodes only",
        default = False
    )

classes = [
    SvIOPanelProperties,
    SvNodeTreeExporter,
    SvNodeTreeExportToGist,
    SvNodeTreeImporter,
    SvNodeTreeImporterSilent,
    SvNodeTreeImportFromGist,
    SvBlendToArchive
]


def register():
    _ = [register_class(cls) for cls in classes]
    bpy.types.NodeTree.io_panel_properties = PointerProperty(name="io_panel_properties", type=SvIOPanelProperties)


def unregister():
    del bpy.types.NodeTree.io_panel_properties
    _ = [unregister_class(cls) for cls in classes[::-1]]


# if __name__ == '__main__':
#    register()
