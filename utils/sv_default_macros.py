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
import webbrowser

import bpy

from sverchok.utils.sv_update_utils import sv_get_local_path


macros = {
    "> obj vd": {
        'display_name': "active_obj into objlite + vdmk2",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'obj vd']},
    "> objs vd": {
        'display_name': "multi obj in + vdmk2",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'objs vd']},
    "> zen": {
        'display_name': "zen of Sverchok",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'zen']},
    "> sn petal": {
        'display_name': "load snlite w/ petalsine",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'sn petal']},
    "> monad info": {
        'display_name': "output current idx / total",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'monad info']},
    "> sw1": {
        'display_name': "connect nodes to switch",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'switch1']},
    "> sw12": {
        'display_name': "connect nodes to switch",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'switch12']},
    "> sw13": {
        'display_name': "connect nodes to switch",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'switch13']},
    "> sw123": {
        'display_name': "connect nodes to switch",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'switch123']},
    "> gp +": {
        'display_name': "grease pencil setup",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'gp +']}
}


sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}


def sn_loader(snlite, script_name=None):
    sv_path = os.path.dirname(sv_get_local_path()[0])
    snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')
    fullpath = os.path.join(snlite_template_path, script_name)

    txt = bpy.data.texts.load(fullpath)
    snlite.script_name = os.path.basename(txt.name)
    snlite.load()


class DefaultMacros():

    @classmethod
    def ensure_nodetree(cls, operator, context):
        '''
        if no active nodetree
        add new empty node tree, set fakeuser immediately
        '''
        if not context.space_data.tree_type in sv_types:
            print('not running from a sv nodetree')
            return

        if not hasattr(context.space_data.edit_tree, 'nodes'):
            msg_one = 'going to add a new empty node tree'
            msg_two = 'added new node tree'
            print(msg_one)
            operator.report({"WARNING"}, msg_one)
            ng_params = {'name': 'NodeTree', 'type': 'SverchCustomTreeType'}
            ng = bpy.data.node_groups.new(**ng_params)
            ng.use_fake_user = True
            context.space_data.node_tree = ng
            operator.report({"WARNING"}, msg_two)

    @classmethod
    def verbose_macro_handler(cls, operator, context, term):

        cls.ensure_nodetree(operator, context)

        tree = context.space_data.edit_tree
        nodes, links = tree.nodes, tree.links

        if term == 'obj vd':
            obj_in_node = nodes.new('SvObjInLite')
            obj_in_node.dget()
            vd_node = nodes.new('ViewerNode2')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[1])
            links.new(obj_in_node.outputs[3], vd_node.inputs[2])

        elif term == 'objs vd':
            obj_in_node = nodes.new('SvObjectsNodeMK3')
            obj_in_node.get_objects_from_scene(operator)
            vd_node = nodes.new('ViewerNode2')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[1])
            links.new(obj_in_node.outputs[3], vd_node.inputs[2])

        elif term == 'zen':
            full_url_term = 'https://blenderpython.tumblr.com/post/91951323209/zen-of-sverchok'
            webbrowser.open(full_url_term)

        elif term == 'sn petal':
            snlite = nodes.new('SvScriptNodeLite')
            sn_loader(snlite, script_name='petal_sine.py')

        elif term == 'monad info':
            x, y = context.space_data.cursor_location[:]
            monad_info = nodes.new('SvMonadInfoNode')
            monad_info.location = x, y

        elif "switch" in term:
            selected_nodes = context.selected_nodes
            # get bounding box of all selected nodes
            minx = +1e10
            maxx = -1e10
            miny = +1e10
            maxy = -1e10
            for node in selected_nodes:
                minx = min(minx, node.location.x)
                maxx = max(maxx, node.location.x + node.width)
                miny = min(miny, node.location.y - node.height)
                maxy = max(maxy, node.location.y)

            switch_node = nodes.new('SvInputSwitchNode')
            switch_node.location = maxx + 100, maxy

            # find out which sockets to connect
            socket_numbers = term.replace("switch", "")
            if len(socket_numbers) == 1: # one socket
                socket_indices = [0]
            else: # multiple sockets
                socket_indices = [int(n) - 1 for n in socket_numbers]

            switch_node.set_size = len(socket_indices)

            sorted_nodes = sorted(selected_nodes, key=lambda n: n.location.y, reverse=True)

            # link the nodes to InputSwitch node
            for i, node in enumerate(sorted_nodes):
                label = switch_node.label_of_set(i)
                for j, n in enumerate(socket_indices):
                    links.new(node.outputs[n], switch_node.inputs[label + " " + str(j+1)])

            if all(node.outputs[0].bl_idname == "VerticesSocket" for node in sorted_nodes):
                viewer_node = nodes.new("ViewerNode2")
                viewer_node.location = switch_node.location.x + switch_node.width + 100, maxy

                # link the input switch node to the ViewerDraw node
                links.new(switch_node.outputs[0], viewer_node.inputs[0])
                if len(socket_indices) > 1:
                    links.new(switch_node.outputs[1], viewer_node.inputs[1])

        elif term == 'gp +':
            needed_nodes = [
                ['SvGetAssetProperties', (0.00, 0.00)],
                ['SvPathLengthNode', (250, 115)],
                ['SvScalarMathNodeMK2', (420, 115)],
                ['Float2IntNode', (590, 115)],
                ['SvGenFloatRange', (760, 115)],
                ['SvInterpolationNodeMK3', (930, 115)],
                ['LineConnectNodeMK2', (1100, 115)],
                ['ViewerNode2', (1290, 115)],
            ]

            made_nodes = []
            x, y = context.space_data.cursor_location[:]
            for node_bl_idname, node_location in needed_nodes:
                n = nodes.new(node_bl_idname)
                n.location = node_location[0] + x, node_location[1] + y
                made_nodes.append(n)

            # Path Length
            made_nodes[1].segment = False

            # ID Selector
            made_nodes[0].Mode = 'grease_pencil'  # the rest must be user driven
            links.new(made_nodes[0].outputs[0], made_nodes[1].inputs[0])

            # Scalar Math node
            made_nodes[2].current_op = 'MUL'
            made_nodes[2].y_ = 2.5
            links.new(made_nodes[1].outputs[0], made_nodes[2].inputs[0])   # path length -> math
            links.new(made_nodes[2].outputs[0], made_nodes[3].inputs[0])   # math -> float

            # Float2Int node
            # made_nodes[3]
            links.new(made_nodes[3].outputs[0], made_nodes[4].inputs[2])

            # Float range
            made_nodes[4].mode = 'FRANGE_COUNT'
            made_nodes[4].stop_ = 1.0
            links.new(made_nodes[4].outputs[0], made_nodes[5].inputs[1])

            # Vector Interpolate
            made_nodes[5]
            links.new(made_nodes[0].outputs[0], made_nodes[5].inputs[0])
            links.new(made_nodes[5].outputs[0], made_nodes[6].inputs[0])

            # UV connect
            made_nodes[6].polygons = 'Edges'
            made_nodes[6].slice_check = False
            made_nodes[6].dir_check = 'U_dir'

            # Viewer Draw
            made_nodes[7]
            links.new(made_nodes[6].outputs[0], made_nodes[7].inputs[0])
            links.new(made_nodes[6].outputs[1], made_nodes[7].inputs[1])
