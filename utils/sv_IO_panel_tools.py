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
from os.path import basename, dirname
from time import gmtime, strftime
import zipfile
import json
import re
import urllib
from urllib.request import urlopen
from itertools import chain

import bpy

from sverchok import old_nodes
from sverchok.utils.sv_node_utils import recursive_framed_location_finder
from sverchok.utils.sv_IO_monad_helpers import pack_monad, unpack_monad
from sverchok.utils.logging import debug, info, warning, error, exception

# pylint: disable=w0621


SCRIPTED_NODES = {'SvScriptNode', 'SvScriptNodeMK2', 'SvScriptNodeLite'}
PROFILE_NODES = {'SvProfileNode', 'SvProfileNodeMK2'}

_EXPORTER_REVISION_ = '0.072'

IO_REVISION_HISTORY = r"""
0.072 export now stores the absolute node location (incase framed-n)
0.072 new route for node.storage_get/set_data. no change to json format
0.07  add initial support for socket properties.
0.065 general refactoring to get the monad pack/unpack into one file
0.064 prop_types as a property is now tracked for scalarmath and logic node, this uses boolvec.
0.063 add support for obj_in_lite obj serialization.
0.062 (no revision change) - fixes import of sn texts that are present already in .blend
0.062 (no revision change) - looks in multiple places for textmode param.
0.062 monad export properly

revisions below this are your own problem.

"""


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
            error('zip contains no files ending with .json')
            return

        debug(exported_name + ' <')
        fp = jfile.open(exported_name, 'r')
        m = fp.read().decode()
        return json.loads(m)


def find_enumerators(node):
    ignored_enums = ['bl_icon', 'bl_static_type', 'type']
    node_props = node.bl_rna.properties[:]
    f = filter(lambda p: isinstance(p, bpy.types.EnumProperty), node_props)
    return [p.identifier for p in f if not (p.identifier in ignored_enums)]


def compile_socket(link):

    try:
        link_data = (link.from_node.name, link.from_socket.index, link.to_node.name, link.to_socket.index)
    except Exception as err:
        if "'NodeSocketColor' object has no attribute 'index'" in repr(err):
            debug('adding node reroute using socketname instead if index')
        else:
            error(repr(err))
        link_data = (link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name)

    return link_data


def write_json(layout_dict, destination_path):

    try:
        m = json.dumps(layout_dict, sort_keys=True, indent=2)
    except Exception as err:
        error(repr(err))
        info(layout_dict)

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


def get_superficial_props(node_dict, node):
    node_dict['height'] = node.height
    node_dict['width'] = node.width
    node_dict['label'] = node.label
    node_dict['hide'] = node.hide

    _x, _y = recursive_framed_location_finder(node, node.location[:])
    node_dict['location'] = _x, _y

    if node.use_custom_color:
        node_dict['color'] = node.color[:]
        node_dict['use_custom_color'] = True


def collect_custom_socket_properties(node, node_dict):
    # print("** PROCESSING custom properties for node: ", node.bl_idname)
    input_socket_storage = {}
    for socket in node.inputs:

        # print("Socket %d of %d" % (socket.index + 1, len(node.inputs)))

        storable = {}
        tracked_props = 'use_expander', 'use_quicklink', 'expanded', 'use_prop'

        for tracked_prop_name in tracked_props:
            if not hasattr(socket, tracked_prop_name):
                continue

            value = getattr(socket, tracked_prop_name)
            defaultValue = socket.bl_rna.properties[tracked_prop_name].default
            # property value same as default ? => don't store it
            if value == defaultValue:
                continue

            # print("Processing custom property: ", tracked_prop_name, " value = ", value)
            storable[tracked_prop_name] = value

            if tracked_prop_name == 'use_prop' and value:
                # print("prop type:", type(socket.prop))
                storable['prop'] = socket.prop[:]

        if storable:
            input_socket_storage[socket.index] = storable

    if input_socket_storage:
        node_dict['custom_socket_props'] = input_socket_storage
    # print("**\n")


def can_skip_property(node, k):
    """
    n_id:
        used to store the hash of the current Node,
        this is created along with the Node anyway. skip.
    typ, newsock:
        reserved variables for changeable sockets
    dynamic_strings:
        reserved by exec node
    frame_collection_name / type_collection_name both store Collection properties..avoiding for now
    """

    if k in {'n_id', 'typ', 'newsock', 'dynamic_strings', 'frame_collection_name', 'type_collection_name'}:
        return True

    elif node.bl_idname == 'SvProfileNodeMK2' and k in {'SvLists', 'SvSubLists'}:
        # these are CollectionProperties, populated later.
        return True

    elif node.bl_idname == 'ObjectsNode' and (k == "objects_local"):
        # this silences the import error when items not found.
        return True

    elif node.bl_idname == 'SvObjectsNodeMK3' and (k == 'object_names'):
        # this supresses this k, in favour of hitting node.storage_get_data later
        return True

    elif node.bl_idname in {'SvTextInNode', 'SvTextInNodeMK2'} and (k == 'current_text'):
        return True


def display_introspection_info(node, k, v):
    if not isinstance(v, (float, int, str)):
        debug('//')
        debug("%s -> property: %s: %s", node.name, k, type(v))
        if k in node.bl_rna.properties:
            debug(type(node.bl_rna.properties[k]))
        elif k in node:
            # something like node['lp']  , ID Property directly on the node instance.
            debug(type(node[k]))
        else:
            error('%s is not bl_rna or IDproperty.. please report this', k)

        debug('\\\\')


def handle_old_groupnode(node, k, v, groups_dict, create_dict_of_tree):
    if node.bl_idname == 'SvGroupNode' and (k == "group_name"):
        if v not in groups_dict:
            group_ng = bpy.data.node_groups[v]
            group_dict = create_dict_of_tree(group_ng)
            group_json = json.dumps(group_dict)
            groups_dict[v] = group_json


def handle_enum_property(node, k, v, node_items, node_enums):
    if k in node_enums:
        v = getattr(node, k)
        node_items[k] = v


def create_dict_of_tree(ng, skip_set={}, selected=False, identified_node=None):
    nodes = ng.nodes
    layout_dict = {}
    nodes_dict = {}
    groups_dict = {}

    if not skip_set:
        skip_set = {'Sv3DviewPropsNode'}

    if selected:
        nodes = list(filter(lambda n: n.select, nodes))

    if identified_node:
        # this mode will import one node only.
        nodes = [identified_node]

    # get nodes and params
    for node in nodes:

        if node.bl_idname in skip_set:
            continue

        node_dict = {}
        node_items = {}
        node_enums = find_enumerators(node)

        IsMonadInstanceNode = (node.bl_idname.startswith('SvGroupNodeMonad'))

        for k, v in node.items():

            display_introspection_info(node, k, v)

            if can_skip_property(node, k):
                continue
            elif has_state_switch_protection(node, k):
                continue

            handle_old_groupnode(node, k, v, groups_dict, create_dict_of_tree)            

            if isinstance(v, (float, int, str)):
                node_items[k] = v
            elif node.bl_idname in {'ScalarMathNode', 'SvLogicNode'} and k == 'prop_types':
                node_items[k] = getattr(node, k)[:]
                continue
            else:
                node_items[k] = v[:]

            handle_enum_property(node, k, v, node_items, node_enums)


        if IsMonadInstanceNode and node.monad:
            pack_monad(node, node_items, groups_dict, create_dict_of_tree)

        if hasattr(node, "storage_get_data"):
            node.storage_get_data(node_dict)

        node_dict['params'] = node_items

        collect_custom_socket_properties(node, node_dict)

        # if node.bl_idname == 'NodeFrame':
        #    frame_props = 'shrink', 'use_custom_color', 'label_size'
        #    node_dict['params'].update({fpv: getattr(node, fpv) for fpv in frame_props})

        if IsMonadInstanceNode:
            node_dict['bl_idname'] = 'SvMonadGenericNode'
        else:
            node_dict['bl_idname'] = node.bl_idname

        if node.bl_idname in {'SvGroupInputsNodeExp', 'SvGroupOutputsNodeExp'}:
            node_dict[node.node_kind] = node.stash()

        get_superficial_props(node_dict, node)
        nodes_dict[node.name] = node_dict

        # -------------------

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
        exception(err)
        error('no update lists found or other error!')
        error(' - trigger an update and retry')
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

    # original textin used 'current_text', textin+ uses 'text'
    current_text = params.get('current_text', params.get('text'))

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


def apply_socket_props(socket, info):
    debug("applying socket props")
    for tracked_prop_name, tracked_prop_value in info.items():
        try:
            setattr(socket, tracked_prop_name, tracked_prop_value)

        except Exception as err:
            error("Error while setting node socket: %s | %s", node.name, socket.index)
            error("the following failed | %s <- %s", tracked_prop_name, tracked_prop_value)
            exception(err)


def apply_custom_socket_props(node, node_ref):
    debug("applying node props for node: %s", node.bl_idname)
    socket_properties = node_ref.get('custom_socket_props')
    if socket_properties:
        for idx, info in socket_properties.items():
            try:
                socket = node.inputs[int(idx)]
                apply_socket_props(socket, info)
            except Exception as err:
                error("socket index: %s, trying to pass: %s, num_sockets: %s", idx, info, len(node.inputs))
                exception(err)


def add_texts(node, node_ref):
    if node.bl_idname in SCRIPTED_NODES:
        perform_scripted_node_inject(node, node_ref)

    elif node.bl_idname in PROFILE_NODES:
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

def center_nodes(nodes_json_dict, target_center=None):
    """
    Adjust location attributes of nodes, so that average
    location will be equal to target_center.

    nodes_json_dict: json dictionary of nodes
    target_center: 2-tuple (or 2-list) of floats, defaults to (0,0).
    """
    if target_center is None:
        target_center = [0,0]
    n = len(nodes_json_dict)
    locations = [node['location'] for node in nodes_json_dict.values()]
    location_sum = [sum(x) for x in zip(*locations)]
    average_location = [x / float(n) for x in location_sum]
    for key in nodes_json_dict:
        node = nodes_json_dict[key]
        node['location'] = [x - x0 + x1 for x, x0, x1 in zip(node['location'], average_location, target_center)]

def import_tree(ng, fullpath='', nodes_json=None, create_texts=True, center=None):

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

        # it may be necessary to store monads as dicts instead of string/json
        # this will handle both scenarios
        if isinstance(nodes_json, str):
            nodes_json = json.loads(nodes_json)
            debug('==== loading monad ====')
        info(('#' * 12) + nodes_json['export_version'])

        # create all nodes and groups '''
        update_lists = nodes_json['update_lists']
        nodes_to_import = nodes_json['nodes']
        if center is not None:
            center_nodes(nodes_to_import, center)
        groups_to_import = nodes_json.get('groups', {})

        add_groups(groups_to_import)  # this return is not used yet
        name_remap = add_nodes(ng, nodes_to_import, nodes, create_texts)

        # now connect them / prevent unnecessary updates
        ng.freeze(hard=True)
        make_links(update_lists, name_remap)

        # set frame parents '''
        place_frames(ng, nodes_json, name_remap)

        # clean up
        old_nodes.scan_for_old(ng)
        ng.unfreeze(hard=True)
        
        ng.update()
        ng.update_tag()

    # ---- read files (.json or .zip) or straight json data -----

    if fullpath.endswith('.zip'):
        nodes_json = get_file_obj_from_zip(fullpath)
        generate_layout(fullpath, nodes_json)

    elif fullpath.endswith('.json'):
        with open(fullpath) as fp:
            nodes_json = json.load(fp)
            generate_layout(fullpath, nodes_json)

    elif nodes_json:
        generate_layout('', nodes_json)


def load_json_from_gist(gist_id, operator=None):
    """
    Load JSON data from Gist by gist ID.

    gist_id: gist ID. Passing full URL is also supported.
    operator: optional instance of bpy.types.Operator. Used for errors reporting.

    Returns JSON dictionary.
    """

    def read_n_decode(url):
        try:
            content_at_url = urlopen(url)
            found_json = content_at_url.read().decode()
            return found_json
        except urllib.error.HTTPError as err:
            if err.code == 404:
                message = 'url: ' + str(url) + ' doesn\'t appear to be a valid url, copy it again from your source'
                error(message)
                if operator:
                    operator.report({'ERROR'}, message)
            else:
                message = 'url error:' + str(err.code)
                error(message)
                if operator:
                    operator.report({'ERROR'}, message)
        except Exception as err:
            exception(err)
            if operator:
                operator.report({'ERROR'}, 'unspecified error, check your internet connection')

        return

    # if it still has the full gist path, trim down to ID
    if '/' in gist_id:
        gist_id = gist_id.split('/')[-1]

    gist_id = str(gist_id)
    url = 'https://api.github.com/gists/' + gist_id
    found_json = read_n_decode(url)
    if not found_json:
        return

    wfile = json.JSONDecoder()
    wjson = wfile.decode(found_json)

    # 'files' may contain several names, we pick the first (index=0)
    file_name = list(wjson['files'].keys())[0]
    nodes_str = wjson['files'][file_name]['content']
    return json.loads(nodes_str)


def propose_archive_filepath(blendpath, extension='zip'):
    """ disect existing filepath, add timestamp """
    blendname = os.path.basename(blendpath)
    blenddir = os.path.dirname(blendpath)
    blendbasename = blendname.split('.')[0]
    raw_time_stamp = strftime("%Y_%m_%d_%H_%M", gmtime())
    archivename = blendbasename + '_' + raw_time_stamp + '.' + extension

    return os.path.join(blenddir, archivename), blendname
