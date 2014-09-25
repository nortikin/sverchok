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
import traceback
from itertools import chain

import bpy
from bpy.types import EnumProperty
from bpy.props import StringProperty
from node_tree import SverchCustomTreeNode


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


def create_dict_of_tree(ng):
    nodes = ng.nodes
    layout_dict = {}
    nodes_dict = {}

    skip_set = {'SvImportExport', 'Sv3DviewPropsNode'}

    ''' get nodes and params '''
    for node in nodes:

        if node.bl_idname in skip_set:
            continue

        node_dict = {}
        node_items = {}
        node_enums = find_enumerators(node)

        for k, v in node.items():
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

    ''' get connections '''
    links = (compile_socket(l) for l in ng.links)
    connections_dict = {idx: link for idx, link in enumerate(links)}
    layout_dict['connections'] = connections_dict

    ''' get framed nodes '''
    framed_nodes = {}
    for node in nodes:

        if node.bl_idname in skip_set:
            continue

        if node.parent:
            framed_nodes[node.name] = node.parent.name
    layout_dict['framed_nodes'] = framed_nodes

    ''' get update list (cache, order to link) '''
    # try/except for now, it can occur after f8 that the cache is dumped.
    # should issue an update if nodetree isn't found in the cache
    try:
        links_out = []
        for node in chain(*ng.get_update_lists()[0]):
            for socket in ng.nodes[node].inputs:
                if socket.links:
                    links_out.append(compile_socket(socket.links[0]))
        layout_dict['update_lists'] = links_out
    except Exception as err:
        print(traceback.format_exc())
        print('no update lists found or other error!')
        print(' - trigger an update and retry')
        return

    layout_dict['export_version'] = '0.01 pre alpha'
    return layout_dict


def import_tree(ng, fullpath):

    nodes = ng.nodes

    def resolve_socket(from_node, from_socket, to_node, to_socket):
        return (ng.nodes[from_node].outputs[from_socket],
                ng.nodes[to_node].inputs[to_socket])

    with open(fullpath) as fp:
        nodes_json = json.load(fp)

        print('#'*12, nodes_json['export_version'])

        ''' first create all nodes. '''
        nodes_to_import = nodes_json['nodes']
        for n in sorted(nodes_to_import):
            node_ref = nodes_to_import[n]

            bl_idname = node_ref['bl_idname']
            try:
                node = nodes.new(bl_idname)
            except Exception as err:
                print(traceback.format_exc())
                print(bl_idname, 'not currently registered, skipping')
                continue

            if not (node.name == n):
                node.name = n

            print(node.name, node_ref['params'])
            if not (bl_idname in {'ListJoinNode'}):
                params = node_ref['params']
                for p in params:
                    val = params[p]
                    setattr(node, p, val)

            perform_special_ops_if_tagged(node, bl_idname, params)

            node.location = node_ref['location']
            node.height = node_ref['height']
            node.width = node_ref['width']
            node.label = node_ref['label']
            node.hide = node_ref['hide']
            node.color = node_ref['color']

        update_lists = nodes_json['update_lists']
        print('update lists:')
        for ulist in update_lists:
            print(ulist)

        ''' now connect them '''

        # naive
        failed_connections = []
        for link in update_lists:
            try:
                ng.links.new(*resolve_socket(*link))
                #node = ng.nodes[link[2]]
                #hit_update(node)
            except Exception as err:
                print(traceback.format_exc())
                msg = 'failure: ' + str(link)
                print(msg)
                failed_connections.append(link)
                continue

        if failed_connections:
            # could retry pool in last attempt?
            print('failed total {0}'.format(len(failed_connections)))
            print(failed_connections)
        else:
            print('no failed connections! awesome.')

        ''' set frame parents '''
        framed_nodes = nodes_json['framed_nodes']
        for node_name, parent in framed_nodes.items():
            ng.nodes[node_name].parent = ng.nodes[parent]

        bpy.ops.node.sverchok_update_current(node_group=ng.name)


def perform_special_ops_if_tagged(node, bl_idname, params):
    if bl_idname in {'SvGenFloatRange'}:
        mode = params.get('mode', None)
        if mode:
            # get any other mode first, then back again.
            # not cool hacks.
            mode_cur = {mode, }
            options = {"FRANGE", "FRANGE_COUNT", "FRANGE_STEP"}
            any_other_mode = list(mode_cur ^ options)[0]
            node.mode = any_other_mode
            node.mode = mode

    #if bl_idname in {'ListJoinNode'}:
    #    pass


def hit_update(node):
    if node.bl_idname in {'ListJoinNode'}:
        print('triggered update')
        node.update()


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

    def execute(self, context):
        ng = bpy.data.node_groups[self.id_tree]
        destination_path = self.filepath

        layout_dict = create_dict_of_tree(ng)
        if not layout_dict:
            msg = 'no update list found - didn\'t export'
            self.report({"WARNING"}, msg)
            print(msg)
            return {'CANCELLED'}

        write_json(layout_dict, destination_path)
        msg = 'exported to: ' + self.filepath
        self.report({"INFO"}, msg)
        print(msg)
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
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvNodeTest(bpy.types.Operator):
    '''Importing operation will test various scenarios'''

    bl_idname = "node.tree_test_importer"
    bl_label = "sv NodeTree Test Import Operator"

    id_tree = StringProperty()

    def execute(self, context):
        ng = bpy.data.node_groups[self.id_tree]
        nodes = ng.nodes

        l1 = nodes.new('LineNode')
        l2 = nodes.new('LineNode')
        LJ = nodes.new('ListJoinNode')

        l1.location = -105.1, 141.6
        l2.location = -106.3, 2.3
        LJ.location = 174.1, 154.5

        ng.links.new(l1.outputs[0], LJ.inputs[0])
        ng.links.new(l2.outputs[0], LJ.inputs[1])

        return {'FINISHED'}


class SvImportExport(bpy.types.Node, SverchCustomTreeNode):
    ''' SvImportExportNodeTree '''
    bl_idname = 'SvImportExport'
    bl_label = 'Sv Import Export'
    bl_icon = 'OUTLINER_OB_EMPTY'

    new_nodetree_name = StringProperty(
        name='new_nodetree_name',
        default="ImportedNodeTree")

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):

        ''' export '''

        col = layout.column(align=True)
        box1 = col.box()
        box1.label('pick file name and location')
        imp = box1.operator(
            'node.tree_exporter',
            text='export current',
            icon='FILE_BACKUP')
        imp.id_tree = self.id_data.name

        ''' import '''

        box2 = col.box()
        box2.label('pick file name from location')
        col = box2.column()
        exp1 = col.operator(
            'node.tree_importer',
            text='import here',
            icon='RNA_ADD')
        exp1.id_tree = self.id_data.name

        col.separator()

        col.prop(self, 'new_nodetree_name', text='tree name')
        exp2 = col.operator(
            'node.tree_importer',
            text='import to new',
            icon='RNA')
        exp2.id_tree = ''
        exp2.new_nodetree_name = self.new_nodetree_name

        ''' import special '''

        box3 = col.box()
        box3.label('test limited python cases')
        col = box3.column()
        exp3 = col.operator(
            'node.tree_test_importer',
            text='import scenario',
            icon='RNA_ADD')
        exp3.id_tree = self.id_data.name

    def update(self):
        pass


def register():
    bpy.utils.register_class(SvNodeTreeExporter)
    bpy.utils.register_class(SvNodeTreeImporter)
    bpy.utils.register_class(SvNodeTest)
    bpy.utils.register_class(SvImportExport)


def unregister():
    bpy.utils.unregister_class(SvImportExport)
    bpy.utils.unregister_class(SvNodeTest)
    bpy.utils.unregister_class(SvNodeTreeImporter)
    bpy.utils.unregister_class(SvNodeTreeExporter)
