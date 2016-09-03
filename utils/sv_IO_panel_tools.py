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

import json
import os
import re
import zipfile
import traceback
from urllib.request import urlopen

from os.path import basename
from os.path import dirname
from itertools import chain

import bpy
from bpy.types import EnumProperty
from bpy.props import StringProperty
from bpy.props import BoolProperty
from sverchok import old_nodes
from sverchok.utils import sv_gist_tools


SCRIPTED_NODES = {'SvScriptNode', 'SvScriptNodeMK2'}

_EXPORTER_REVISION_ = '0.062'

'''
0.062 monad export properly
0.061 codeshuffle 76f04f9
0.060 understands sockets with props <o/

0.056 fixing SN1 script importing upon json load, will not duplicate
      existing .py files by the same name. This tends to be preferred, one should
      never have two files named the same which perform different operations.
      main fixes SN1, SN2, ProfileNode, TextInput (json-mode only verified)

0.055 - (import) fix : SN reset (files_popup, username) params
      - (import) add : deals with importing from gist id.

0.054 group support, hash of text files
0.053 support old_nodes on demand
0.052 respect selection
0.051 fake node removed, freeze and unfreeze used instead
0.05 fake node inserted to stop updates
0.043 remap dict for duplicates (when importing into existing tree)
0.042 add fake user to imported layouts + switch to new tree.


'''


def get_file_obj_from_zip(fullpath):
    '''
    fullpath must point to a zip file.
    usage:
        nodes_json = get_file_obj_from_zip(fullpath)
        print(nodes_json['export_version'])
    '''
    with zipfile.ZipFile(fullpath, "r") as jfile:
        exported_name = ""
        for name in jfile.namelist():
            if name.endswith('.json'):
                exported_name = name
                break

        if not exported_name:
            print('zip contains no files ending with .json')
            return

        print(exported_name, '<')
        fp = jfile.open(exported_name, 'r')
        m = fp.read().decode()
        return json.loads(m)


def find_enumerators(node):
    ignored_enums = ['bl_icon', 'bl_static_type', 'type']
    node_props = node.bl_rna.properties[:]
    f = filter(lambda p: isinstance(p, EnumProperty), node_props)
    return [p.identifier for p in f if not (p.identifier in ignored_enums)]


def compile_socket(link):
    return (link.from_node.name, link.from_socket.name,
            link.to_node.name, link.to_socket.name)


def write_json(layout_dict, destination_path):
    m = json.dumps(layout_dict, sort_keys=True, indent=2)
    # optional post processing step
    post_processing = False
    if post_processing:
        flatten = lambda match: r' {}'.format(match.group(1), m)
        m = re.sub(r'\s\s+(\d+)', flatten, m)

    with open(destination_path, 'w') as node_tree:
        node_tree.writelines(m)


def has_state_switch_protection(node, k):
    ''' explict for debugging '''

    if not (k in {'current_mode', 'current_op'}):
        return False

    if k == 'current_mode':
        return node.bl_idname in {
            'SvGenFloatRange', 'GenListRangeIntNode',
            'SvKDTreeNode', 'SvMirrorNode', 'SvRotationNode'}

    if k == 'current_op':
        return node.bl_idname in {'VectorMathNode'}


def create_dict_of_tree(ng, skip_set={}, selected=False):
    nodes = ng.nodes
    layout_dict = {}
    nodes_dict = {}
    groups_dict = {}
    texts = bpy.data.texts
    if not skip_set:
        skip_set = {'SvImportExport', 'Sv3DviewPropsNode'}

    if selected:
        nodes = list(filter(lambda n: n.select, nodes))

    ''' get nodes and params '''
    for node in nodes:

        if node.bl_idname in skip_set:
            continue

        node_dict = {}
        node_items = {}
        node_enums = find_enumerators(node)

        ObjectsNode = (node.bl_idname == 'ObjectsNode')
        ProfileParamNode = (node.bl_idname == 'SvProfileNode')
        IsGroupNode = (node.bl_idname == 'SvGroupNode')
        IsMonadInstanceNode = (node.bl_idname.startswith('SvGroupNodeMonad'))
        TextInput = (node.bl_idname == 'SvTextInNode')

        for k, v in node.items():

            if k == 'n_id':
                # used to store the hash of the current Node,
                # this is created along with the Node anyway. skip.
                continue

            if k in {'typ', 'newsock'}:
                ''' these are reserved variables for changeable socks '''
                continue

            if has_state_switch_protection(node, k):
                continue

            # this silences the import error when items not found.
            if ObjectsNode and (k == "objects_local"):
                continue

            if TextInput and (k == 'current_text'):
                node_dict['current_text'] = node.text
                node_dict['textmode'] = node.textmode
                if node.textmode == 'JSON':
                    # let us add the json as full member to the tree :)
                    text_str = texts[node.text].as_string()
                    json_as_dict = json.loads(text_str)
                    node_dict['text_lines'] = {}
                    node_dict['text_lines']['stored_as_json'] = json_as_dict
                else:
                    node_dict['text_lines'] = texts[node.text].as_string()

            if ProfileParamNode and (k == "filename"):
                '''add file content to dict'''
                node_dict['path_file'] = texts[node.filename].as_string()

            if IsGroupNode and (k == "group_name"):
                if v not in groups_dict:
                    group_ng = bpy.data.node_groups[v]
                    group_dict = create_dict_of_tree(group_ng)
                    group_json = json.dumps(group_dict)
                    groups_dict[v] = group_json

            if isinstance(v, (float, int, str)):
                node_items[k] = v
            else:
                node_items[k] = v[:]

            if k in node_enums:
                v = getattr(node, k)
                node_items[k] = v

        # we can not rely on .items() to be present for various reasons, so we must gather
        # something to fill .params with - due to dynamic nature of node. 
        if IsMonadInstanceNode and node.monad:
            name = node.monad.name
            node_items['monad'] = name
            node_items['cls_dict'] = {}
            node_items['cls_dict']['cls_bl_idname'] = node.bl_idname

            for template in ['input_template', 'output_template']:
                node_items['cls_dict'][template] = getattr(node, template)

            if name not in groups_dict:
                group_ng = bpy.data.node_groups[name]
                group_dict = create_dict_of_tree(group_ng)
                group_dict['bl_idname'] = group_ng.bl_idname  # uhmm..
                group_dict['cls_bl_idname'] = node.bl_idname
                group_json = json.dumps(group_dict)
                groups_dict[name] = group_json

            # [['Y', 'StringsSocket', {'prop_name': 'y'}], [....
            for socket_name, socket_type, prop_dict in node.input_template:
                socket = node.inputs[socket_name]
                if not socket.is_linked and prop_dict:

                    prop_name = prop_dict['prop_name']
                    v = getattr(node, prop_name)
                    if not isinstance(v, (float, int, str)):
                        v = v[:]

                    node_items[prop_name] = v
        

        # collect socket properties
        # inputs = node.inputs
        # for s in inputs:
        #     if (s.bl_label == 'Vertices') and hasattr(node, s.prop_name):
        #         prop = s.prop_name
        #         if prop:
        #            node_dict['custom_socket_props'][prop] = getattr(node, prop)[:]

        node_dict['params'] = node_items

        node_dict['height'] = node.height
        node_dict['width'] = node.width
        node_dict['label'] = node.label
        node_dict['hide'] = node.hide
        
        if IsMonadInstanceNode:
            node_dict['bl_idname'] = 'SvMonadGenericNode'
        else:
            node_dict['bl_idname'] = node.bl_idname

        if node.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'}:
            node_dict[node.node_kind] = node.stash()

        node_dict['location'] = node.location[:]
        node_dict['color'] = node.color[:]
        nodes_dict[node.name] = node_dict

    layout_dict['nodes'] = nodes_dict
    layout_dict['groups'] = groups_dict

    # ''' get connections '''
    # links = (compile_socket(l) for l in ng.links)
    # connections_dict = {idx: link for idx, link in enumerate(links)}
    # layout_dict['connections'] = connections_dict

    ''' get framed nodes '''
    framed_nodes = {}
    for node in nodes:

        if node.bl_idname in skip_set:
            continue

        if node.parent:
            if selected and node.parent.select:
                framed_nodes[node.name] = node.parent.name
            elif not selected:
                framed_nodes[node.name] = node.parent.name

    layout_dict['framed_nodes'] = framed_nodes

    ''' get update list (cache, order to link) '''
    # try/except for now, node tree links might be invalid
    # among other things. auto rebuild on F8
    try:
        ng.build_update_list()
        links_out = []
        for name in chain(*ng.get_update_lists()[0]):
            for socket in ng.nodes[name].inputs:
                if selected and not ng.nodes[name].select:
                    continue
                if socket.links:
                    link = socket.links[0]
                    if selected and not link.from_node.select:
                        continue
                    links_out.append(compile_socket(link))
        layout_dict['update_lists'] = links_out
    except Exception as err:
        print(traceback.format_exc())
        print('no update lists found or other error!')
        print(' - trigger an update and retry')
        return

    layout_dict['export_version'] = _EXPORTER_REVISION_
    return layout_dict


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

        node.script_name = script_name
        node.script_str = script_content

    if node.bl_idname == 'SvScriptNode':
        node.user_name = "templates"               # best would be in the node.
        node.files_popup = "sv_lang_template.sn"   # import to reset easy fix
        node.load()
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
    node.textmode = params['textmode']

    if not current_text:
        print(node.name, "doesn't store a current_text in params")

    elif not current_text in texts:
        new_text = texts.new(current_text)
        if node.textmode == 'JSON':
            json_str = json.dumps(node_ref['text_lines']['stored_as_json'])
            new_text.from_string(json_str)
        else:
            new_text.from_string(node_ref['text_lines'])

    else:
        # reaches here if  (current_text) and (current_text in texts)
        # can probably skip this..
        # texts[current_text].from_string(node_ref['text_lines'])
        print(node.name, 'seems to reuse a text block loaded by another node - skipping')



def apply_superficial_props(node, node_ref):
    '''
    copies the stored values from the json onto the new node's corresponding values.
    '''
    props = ['location', 'height', 'width', 'label', 'hide', 'color']
    for p in props:
        setattr(node, p, node_ref[p])


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
    # print(node.name, params)
    if 'cls_dict' in params:
        return
    for p in params:
        val = params[p]
        setattr(node, p, val)


def add_texts(node, node_ref):
    if node.bl_idname in SCRIPTED_NODES:
        perform_scripted_node_inject(node, node_ref)

    elif node.bl_idname == 'SvProfileNode':
        perform_profile_node_inject(node, node_ref)

    elif node.bl_idname == 'SvTextInNode':
        perform_svtextin_node_object(node, node_ref)


def apply_post_processing(node, node_ref):
    '''
    Nodes that require post processing to work properly
    '''
    if node.bl_idname in {'SvGroupInputsNode', 'SvGroupOutputsNode'}:
        node.load()
    elif node.bl_idname in {'SvGroupNode'}:
        node.load()
        group_name = node.group_name
        node.group_name = group_name_remap.get(group_name, group_name)
    elif node.bl_idname == 'SvTextInNode':
        node.load()
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
            node = nodes.new(bl_idname)
            params = node_ref.get('params')
            cls_dict = params.get('cls_dict')
            monad_name = params.get('monad')
            monad = bpy.data.node_groups[monad_name]
            node.input_template = cls_dict['input_template']
            node.output_template = cls_dict['output_template']
            setattr(node, 'cls_bl_idname', cls_dict['cls_bl_idname'])
            setattr(monad, 'cls_bl_idname', cls_dict['cls_bl_idname'])

            # node.bl_idname = node.cls_bl_idname
        else:
            node = nodes.new(bl_idname)
    except Exception as err:
        print(traceback.format_exc())
        print(bl_idname, 'not currently registered, skipping')
        return

    if create_texts:
        add_texts(node, node_ref)

    gather_remapped_names(node, n, name_remap)
    apply_core_props(node, node_ref)
    apply_superficial_props(node, node_ref)
    apply_post_processing(node, node_ref)


def add_nodes(nodes_to_import, nodes, create_texts):
    '''
    return the dictionary that tracks which nodes got renamed due to conflicts
    '''
    name_remap = {}
    for n in sorted(nodes_to_import):
        add_node_to_tree(nodes, n, nodes_to_import, name_remap, create_texts)
    return name_remap


def add_groups(groups_to_import):
    '''
    return the dictionary that tracks which groups got renamed due to conflicts
    '''
    group_name_remap = {}
    for name in groups_to_import:
        group_ng = bpy.data.node_groups.new(name, 'SverchGroupTreeType')
        if group_ng.name != name:
            group_name_remap[name] = ng.name
        import_tree(group_ng, '', groups_to_import[name])
    return group_name_remap


def print_update_lists(update_lists):
    print('update lists:')
    for ulist in update_lists:
        print(ulist)


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
                print(traceback.format_exc())
                failed_connections.append(link)
                continue

        if failed_connections:
            print('failed total {0}'.format(len(failed_connections)))
            print(failed_connections)
        else:
            print('no failed connections! awesome.')


    def generate_layout(fullpath, nodes_json):
        '''cummulative function ''' 
        
        # it may be necessary to store monads as dicts instead of string/json
        # this will handle both scenarios
        if isinstance(nodes_json, str):
            nodes_json = json.loads(nodes_json)
            print('==== loading monad ====')
        print('#' * 12, nodes_json['export_version'])

        ''' create all nodes and groups '''

        update_lists = nodes_json['update_lists']
        nodes_to_import = nodes_json['nodes']
        groups_to_import = nodes_json.get('groups', {})
        
        add_groups(groups_to_import)  # this return is not used yet
        name_remap = add_nodes(nodes_to_import, nodes, create_texts)

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

        layout_dict = create_dict_of_tree(ng)
        if not layout_dict:
            msg = 'no update list found - didn\'t export'
            self.report({"WARNING"}, msg)
            print(msg)
            return {'CANCELLED'}

        write_json(layout_dict, destination_path)
        msg = 'exported to: ' + destination_path
        self.report({"INFO"}, msg)
        print(msg)

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
                print('wrote:', final_archivename)

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
        ng = bpy.data.node_groups[self.id_tree]
        import_tree(ng, self.filepath)
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

    def read_n_decode(self, url):
        content_at_url = urlopen(url)
        found_json = content_at_url.read().decode()
        return found_json        

    def obtain_json(self, gist_id):

        # if it still has the full gist path, trim down to ID
        if '/' in gist_id:
            gist_id = gist_id.split('/')[-1]

        def get_file(gist_id):

            gist_id = str(gist_id)
            url = 'https://api.github.com/gists/' + gist_id
            found_json = self.read_n_decode(url)

            wfile = json.JSONDecoder()
            wjson = wfile.decode(found_json)

            # 'files' may contain several names, we pick the first (index=0)
            file_name = list(wjson['files'].keys())[0]
            nodes_str = wjson['files'][file_name]['content']
            return json.loads(nodes_str)

        return get_file(gist_id)

    def execute(self, context):
        if not self.id_tree:
            ng_name = self.new_nodetree_name
            ng_params = {
                'name': ng_name or 'unnamed_tree',
                'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
        else:
            ng = bpy.data.node_groups[self.id_tree]

        nodes_json = self.obtain_json(self.gist_id.strip())
        import_tree(ng, nodes_json=nodes_json)

        # set new node tree to active
        context.space_data.node_tree = ng
        return {'FINISHED'}


class SvNodeTreeExportToGist(bpy.types.Operator):
    """Export to anonymous gist and copy id to clipboard"""
    bl_idname = "node.tree_export_to_gist"
    bl_label = "sv NodeTree Gist Export Operator"

    def execute(self, context):
        ng = context.space_data.node_tree
        gist_filename = ng.name
        gist_description = 'to do later?'
        layout_dict = create_dict_of_tree(ng, skip_set={}, selected=False)
        gist_body = json.dumps(layout_dict, sort_keys=True, indent=2)
        try:
            gist_url = sv_gist_tools.main_upload_function(gist_filename, gist_description, gist_body, show_browser=False)
            context.window_manager.clipboard = gist_url   # full destination url
            self.report({'WARNING'}, "Copied gistURL to clipboad")
        except:
            self.report({'ERROR'}, "Error uploading the gist, check your internet connection!")
        finally:
            return {'FINISHED'}


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

classes = [
    SvIOPanelProperties,
    SvNodeTreeExporter,
    SvNodeTreeExportToGist,
    SvNodeTreeImporter,
    SvNodeTreeImporterSilent,
    SvNodeTreeImportFromGist
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.SverchCustomTreeType.io_panel_properties = bpy.props.PointerProperty(
        name="io_panel_properties", type=SvIOPanelProperties)


def unregister():
    del bpy.types.SverchCustomTreeType.io_panel_properties

    for cls in classes[::-1]:
        bpy.utils.unregister_class(cls)



if __name__ == '__main__':
    register()
