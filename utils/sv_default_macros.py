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
from sverchok.utils.sv_node_utils import nodes_bounding_box
from sverchok.utils.macros.math_macros import math_macros
from sverchok.utils.macros.join_macros import join_macros
from sverchok.utils.macros.switch_macros import switch_macros
from sverchok.utils.macros.gp_macros import gp_macro_one, gp_macro_two

# pylint: disable=c0301


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
        'ident': ['verbose_macro_handler', 'snl demo/petal_sine.py']},
    "> Subdiv to quads": {
        'display_name': "snlite w/ subdiv to quads",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'snl demo/subidivide_to_quads.py']},
    "> monad info": {
        'display_name': "output current idx / total",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'monad info']},
    "> multiply *": {
        'display_name': "multiply selected nodes",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'mathMUL']},
    "> add +": {
        'display_name': "add selected nodes",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'mathADD']},
    "> sub -": {
        'display_name': "subtract selected nodes",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'mathSUB']},
    "> join1": {
        'display_name': "selected nodes to List Join",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'join1']},
    "> join123": {
        'display_name': "selected nodes to List Join",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'join123']},
    "> join12": {
        'display_name': "selected nodes to List Join",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'join12']},
    "> join13": {
        'display_name': "selected nodes to List Join",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'join13']},
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
        'ident': ['verbose_macro_handler', 'gp +']},
    "> gp + 2": {
        'display_name': "grease pencil setup",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'gp + 2']},
    "> url": {
        'display_name': "download archive from url",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'url']},
    "> all numpy True": {
        'display_name': "existing nodes to numpy",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'output numpy True']},
    "> all numpy False": {
        'display_name': "existing nodes to python",
        'file': 'macro',
        'ident': ['verbose_macro_handler', 'output numpy False']}
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
            vd_node = nodes.new('SvVDExperimental')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[2])
            links.new(obj_in_node.outputs[3], vd_node.inputs[3])

        elif term == 'objs vd':
            obj_in_node = nodes.new('SvObjectsNodeMK3')
            obj_in_node.get_objects_from_scene(operator)
            vd_node = nodes.new('SvVDExperimental')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[2])
            links.new(obj_in_node.outputs[3], vd_node.inputs[3])

        elif term == 'zen':
            full_url_term = 'https://gist.github.com/zeffii/d843b985b0db97af56dfa9c30cd54712'
            webbrowser.open(full_url_term)

        elif 'snl' in term:
            file = term.split(' ')[1]
            snlite = nodes.new('SvScriptNodeLite')
            snlite.location = context.space_data.cursor_location
            sn_loader(snlite, script_name=file)

        elif term == 'monad info':
            x, y = context.space_data.cursor_location[:]
            monad_info = nodes.new('SvMonadInfoNode')
            monad_info.location = x, y

        elif "join" in term:
            join_macros(context, operator, term, nodes, links)
            
        elif "math" in term:
            math_macros(context, operator, term, nodes, links)
            return {'FINISHED'}
            
        elif "switch" in term:
            switch_macros(context, operator, term, nodes, links)
            return {'FINISHED'}

        elif 'output numpy' in term:
            #stop processing to avoid one update per property
            previous_state = tree.sv_process
            tree.sv_process = False

            state_ = term.split(' ')[2]
            state = state_ == 'True'
            for node in nodes:
                # most of cases
                if hasattr(node, 'output_numpy'):
                    node.output_numpy = state
                # line node
                if hasattr(node, 'as_numpy'):
                    node.as_numpy = state
                # box node
                if hasattr(node, 'out_np'):
                    for i in range(len(node.out_np)):
                        node.out_np[i] = state
                # vector in
                if hasattr(node, 'implementation'):
                    try:
                        node.implementation = 'NumPy' if state else 'Python'
                    except TypeError:
                        pass

            # establish previous processing state
            tree.sv_process = previous_state
            tree.update()

        elif term == 'gp +':
            gp_macro_one(context, operator, term, nodes, links)

        elif term == 'gp + 2':
            gp_macro_two(context, operator, term, nodes, links)

        elif term == 'url':
            bpy.ops.node.sv_load_archived_blend_url()


# EOF
