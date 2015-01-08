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

_EXPORTER_REVISION_ = '0.055'

'''
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
    return [p.identifier for p in f if not p.identifier in ignored_enums]


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

        node_dict['params'] = node_items
        node_dict['location'] = node.location[:]
        node_dict['bl_idname'] = node.bl_idname
        node_dict['height'] = node.height
        node_dict['width'] = node.width
        node_dict['label'] = node.label
        node_dict['hide'] = node.hide
        node_dict['color'] = node.color[:]
        nodes_dict[node.name] = node_dict

    layout_dict['nodes'] = nodes_dict
    layout_dict['groups'] = groups_dict

    #''' get connections '''
    #links = (compile_socket(l) for l in ng.links)
    #connections_dict = {idx: link for idx, link in enumerate(links)}
    #layout_dict['connections'] = connections_dict

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


def import_tree(ng, fullpath='', nodes_json=None, create_texts=True):

    nodes = ng.nodes
    ng.use_fake_user = True

    def resolve_socket(from_node, from_socket, to_node, to_socket, name_dict={}):
        f_node = name_dict.get(from_node, from_node)
        t_node = name_dict.get(to_node, to_node)
        return (ng.nodes[f_node].outputs[from_socket],
                ng.nodes[t_node].inputs[to_socket])

    def generate_layout(fullpath, nodes_json):
        print('#' * 12, nodes_json['export_version'])

        ''' first create all nodes. '''
        nodes_to_import = nodes_json['nodes']
        groups_to_import = nodes_json.get('groups', {})

        group_name_remap = {}
        for name in groups_to_import:
            group_ng = bpy.data.node_groups.new(name, 'SverchGroupTreeType')
            if group_ng.name != name:
                group_name_remap[name] = ng.name
            import_tree(group_ng, '', groups_to_import[name])

        name_remap = {}
        texts = bpy.data.texts

        for n in sorted(nodes_to_import):
            node_ref = nodes_to_import[n]
            bl_idname = node_ref['bl_idname']
            try:
                if old_nodes.is_old(bl_idname):
                    old_nodes.register_old(bl_idname)
                node = nodes.new(bl_idname)
            except Exception as err:
                print(traceback.format_exc())
                print(bl_idname, 'not currently registered, skipping')
                continue

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

            params = node_ref['params']
            print(node.name, params)
            for p in params:
                val = params[p]
                setattr(node, p, val)

            node.location = node_ref['location']
            node.height = node_ref['height']
            node.width = node_ref['width']
            node.label = node_ref['label']
            node.hide = node_ref['hide']
            node.color = node_ref['color']

            ''' maintenance warning:
            for the creation of new text files. If this script is run in a
            file which contains these Text names already, then the script/file
            names stored in the node must be updated to reflect this.

            Also is a script/profile is used for more than one node it will lead
            to duplication. All names have to collected and then fixed at end
            '''
            if create_texts:
                if node.bl_idname in ('SvScriptNode', 'SvScriptNodeMK2'):
                    new_text = texts.new(node.script_name)
                    #  there is no gurantee that we get the name we request
                    if new_text.name != node.script_name:
                        node.script_name = new_text.name
                    new_text.from_string(node.script_str)
                    node.user_name = "templates"               # best would be in the node.
                    node.files_popup = "sv_lang_template.sn"   # import to reset easy fix
                    node.load()

                elif node.bl_idname == 'SvProfileNode':
                    new_text = texts.new(node.filename)
                    new_text.from_string(node_ref['path_file'])
                    #  needed!
                    node.update()
            '''
            Nodes that require post processing to work properly
            '''
            if node.bl_idname in {'SvGroupInputsNode', 'SvGroupOutputsNode'}:
                node.load()
            elif node.bl_idname in {'SvGroupNode'}:
                node.load()
                group_name = node.group_name
                node.group_name = group_name_remap.get(group_name, group_name)

        update_lists = nodes_json['update_lists']
        print('update lists:')
        for ulist in update_lists:
            print(ulist)

        ''' now connect them '''

        # naive
        # freeze updates while connecting the tree, otherwise
        # each connection will cause an update event
        ng.freeze(hard=True)

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

        ''' set frame parents '''
        finalize = lambda name: name_remap.get(name, name)
        framed_nodes = nodes_json['framed_nodes']
        for node_name, parent in framed_nodes.items():
            ng.nodes[finalize(node_name)].parent = ng.nodes[finalize(parent)]

        old_nodes.scan_for_old(ng)
        ng.unfreeze(hard=True)
        ng.update()
        #bpy.ops.node.sverchok_update_current(node_group=ng.name)

        # bpy.ops.node.select_all(action='DESELECT')
        # ng.update()
        # bpy.ops.node.view_all()

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

    def obtain_json(self, gist_id):

        # if it still has the full gist path, trim down to ID
        if '/' in gist_id:
            gist_id = gist_id.split('/')[-1]

        def get_raw_url_from_gist_id(gist_id):

            gist_id = str(gist_id)
            url = 'https://api.github.com/gists/' + gist_id
            found_json = urlopen(url).readall().decode()

            wfile = json.JSONDecoder()
            wjson = wfile.decode(found_json)

            # 'files' may contain several - this will mess up gist name.
            files_flag = 'files'
            file_names = list(wjson[files_flag].keys())
            file_name = file_names[0]
            return wjson[files_flag][file_name]['raw_url']

        def get_file(gist_id):
            url = get_raw_url_from_gist_id(gist_id)
            conn = urlopen(url).readall().decode()
            return conn

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

        found_json = self.obtain_json(self.gist_id)
        wfile = json.JSONDecoder()
        nodes_json = wfile.decode(found_json)
        import_tree(ng, nodes_json=nodes_json)

        # set new node tree to active
        context.space_data.node_tree = ng
        return {'FINISHED'}


def register():
    bpy.types.SverchCustomTreeType.new_nodetree_name = StringProperty(
        name='new_nodetree_name',
        default="Imported_name",
        description="The name to give the new NodeTree, defaults to: Imported")

    bpy.types.SverchCustomTreeType.compress_output = BoolProperty(
        default=0,
        name='compress_output',
        description='option to also compress the json, will generate both')

    bpy.types.SverchCustomTreeType.gist_id = StringProperty(
        name='new_gist_id',
        default="Enter Gist ID here",
        description="This gist ID will be used to obtain the RAW .json from github")

    bpy.utils.register_class(SvNodeTreeExporter)
    bpy.utils.register_class(SvNodeTreeImporter)
    bpy.utils.register_class(SvNodeTreeImportFromGist)


def unregister():
    bpy.utils.unregister_class(SvNodeTreeImportFromGist)
    bpy.utils.unregister_class(SvNodeTreeImporter)
    bpy.utils.unregister_class(SvNodeTreeExporter)
    del bpy.types.SverchCustomTreeType.new_nodetree_name
    del bpy.types.SverchCustomTreeType.compress_output
    del bpy.types.SverchCustomTreeType.gist_id


if __name__ == '__main__':
    register()
