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
from sverchok.utils.macros.hotswap_macros import swap_vd_mv
from sverchok.utils.macros.get_objects_data import objdata_macro_one

# pylint: disable=c0301

def simple_macro(description="", term="", macro_handler="verbose_macro_handler"):
    return {
        'display_name': description,
        'file': 'macro',
        'ident': [macro_handler, term]}    

macros = {
    "> obj vd": simple_macro(description="active_obj into objlite + vdmk2", term='obj vd'),
    "> objs vd": simple_macro(description="multi obj in + vdmk2", term='objs vd'),
    "> objs socket to get-Obj-Data": simple_macro(description="objsocket -> get objects data", term='objs socket to data'),
    "> zen": simple_macro(description="zen of Sverchok", term='zen'),
    "> nuke python++": simple_macro(description="like f8", term='nuke python++'),
    "> 3d cursor to Vector In": simple_macro(description="makes new node", term="3dcursor_to_vector_in"),
    "> 3d cursor to Matrix Input": simple_macro(description="makes new node", term="3dcursor_to_matrix"),
    "> sn petal": simple_macro(description="load snlite w/ petalsine", term='snl demo/petal_sine.py'),
    "> Subdiv to quads": simple_macro(description="snlite w/ subdiv to quads", term='snl demo/subidivide_to_quads.py'),
    "> multiply *": simple_macro(description="multiply selected nodes", term='mathMUL'),
    "> add +": simple_macro(description="add selected nodes", term='mathADD'),
    "> sub -": simple_macro(description="subtract selected nodes", term='mathSUB'),
    "> join1": simple_macro(description="selected nodes to List Join", term='join1'),
    "> join123": simple_macro(description="selected nodes to List Join", term='join123'),
    "> join12": simple_macro(description="selected nodes to List Join", term='join12'),
    "> join13": simple_macro(description="selected nodes to List Join", term='join13'),
    "> rnd col": simple_macro(description="list of n-random colors", term='rndcol'),
    "> sw1": simple_macro(description="connect nodes to switch", term='switch1'),
    "> sw12": simple_macro(description="connect nodes to switch", term='switch12'),
    "> sw13": simple_macro(description="connect nodes to switch", term='switch13'),
    "> sw123": simple_macro(description="connect nodes to switch", term='switch123'),
    "> gp +": simple_macro(description="grease pencil setup", term='gp +'),
    "> gp + 2": simple_macro(description="grease pencil setup", term='gp + 2'),
    "> hotswap vd mv": simple_macro(description="hotswap vd->meshviewer", term='hotswap'),    
    "> url": simple_macro(description="download archive from url", term='url'),
    "> blend 2 zip": simple_macro(description="archive blend as zip", term='blend 2 zip'),
    "> all numpy True": simple_macro(description="existing nodes to numpy", term='output numpy True'),
    "> all numpy False": simple_macro(description="existing nodes to python", term='output numpy False')
}


def sn_loader(snlite, script_name=None):
    sv_path = os.path.dirname(sv_get_local_path()[0])
    snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')
    fullpath = os.path.join(snlite_template_path, script_name)

    txt = bpy.data.texts.load(fullpath)
    snlite.script_name = os.path.basename(txt.name)
    snlite.load()

def set_node_props(node, prop_dict):
    for prop, val in prop_dict.items():
        setattr(node, prop, val)

class DefaultMacros():

    @classmethod
    def ensure_nodetree(cls, operator, context):
        '''
        if no active nodetree
        add new empty node tree, set fakeuser immediately
        '''
        if not context.space_data.tree_type in {'SverchCustomTreeType', }:
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
            vd_node = nodes.new('SvViewerDrawMk4')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[2])
            links.new(obj_in_node.outputs[4], vd_node.inputs[3])

        elif term == 'objs vd':
            obj_in_node = nodes.new('SvGetObjectsData')
            obj_in_node.get_objects_from_scene(operator)
            vd_node = nodes.new('SvViewerDrawMk4')
            vd_node.location = obj_in_node.location.x + 180, obj_in_node.location.y

            # this macro could detect specifically if the node found edges or faces or both... 
            links.new(obj_in_node.outputs[0], vd_node.inputs[0])
            links.new(obj_in_node.outputs[2], vd_node.inputs[2])
            links.new(obj_in_node.outputs[8], vd_node.inputs[3])

        elif term == "objs socket to data":
            objdata_macro_one(context, operator, term, nodes, links)

        elif term == "3dcursor_to_vector_in":
            
            MOUSE_X, MOUSE_Y = context.space_data.cursor_location
            cursor = context.scene.cursor.location

            node = nodes.new("GenVectorsNode")
            node.location = MOUSE_X, MOUSE_Y
            node.x_, node.y_, node.z_ = tuple(cursor)

        elif term == "3dcursor_to_matrix":

            def flattened(matrix):
                return list(matrix[0]) + list(matrix[1]) + list(matrix[2]) + list(matrix[3])
            
            MOUSE_X, MOUSE_Y = context.space_data.cursor_location
            matrix = context.scene.cursor.matrix

            node = nodes.new("SvMatrixValueIn") # "SvMatrixInNodeMK4")
            node.location = MOUSE_X, MOUSE_Y
            node.matrix = flattened(matrix.transposed())

        elif term == 'rndcol':

            # all locations will be relative to cursor
            MOUSE_X, MOUSE_Y = context.space_data.cursor_location

            # add nodes to layout
            NUM = nodes.new("SvNumberNode")
            RR = nodes.new('NodeReroute')
            RND_0 = nodes.new('SvRndNumGen')
            RND_1 = nodes.new('SvRndNumGen')
            RND_2 = nodes.new('SvRndNumGen')
            COL = nodes.new('SvColorsInNodeMK1')

            # set locations
            COL.location = MOUSE_X + 140, MOUSE_Y + 40
            RND_0.location.x = MOUSE_X - 40
            RND_0.location.y = MOUSE_Y + 40
            RND_1.location.x = MOUSE_X - 40
            RND_1.location.y = MOUSE_Y
            RND_2.location.x = MOUSE_X - 40
            RND_2.location.y = MOUSE_Y - 40
            RR.location = MOUSE_X - 110, MOUSE_Y
            NUM.location = MOUSE_X - 280, MOUSE_Y + 20

            # configure nodes
            set_node_props(NUM, {
                'selected_mode': 'int', 'int_': 30})

            set_node_props(RND_0, {
                'type_selected_mode': 'Float',
                'seed': 20, 'hide': True})

            set_node_props(RND_1, {
                'type_selected_mode': 'Float',
                'seed': 30, 'hide': True})

            set_node_props(RND_2, {
                'type_selected_mode': 'Float',
                'seed': 40, 'hide': True})

            # link nodes
            links.new(NUM.outputs[0], RR.inputs[0])
            links.new(RR.outputs[0], RND_0.inputs[0])
            links.new(RR.outputs[0], RND_1.inputs[0])
            links.new(RR.outputs[0], RND_2.inputs[0])
            links.new(RND_0.outputs[0], COL.inputs[0])
            links.new(RND_1.outputs[0], COL.inputs[1])
            links.new(RND_2.outputs[0], COL.inputs[2])

        elif 'hotswap' in term:
            swap_vd_mv(context, operator, term, nodes, links)
            return

        elif term == 'nuke python++':
            bpy.ops.script.reload()

        elif term == 'zen':
            full_url_term = 'https://gist.github.com/zeffii/d843b985b0db97af56dfa9c30cd54712'
            webbrowser.open(full_url_term)

        elif 'snl' in term:
            file = term.split(' ')[1]
            snlite = nodes.new('SvScriptNodeLite')
            snlite.location = context.space_data.cursor_location
            sn_loader(snlite, script_name=file)

        elif "join" in term:
            join_macros(context, operator, term, nodes, links)

        elif "math" in term:
            math_macros(context, operator, term, nodes, links)
            return

        elif "switch" in term:
            switch_macros(context, operator, term, nodes, links)
            return

        elif 'output numpy' in term:
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

        elif term == 'gp +':
            gp_macro_one(context, operator, term, nodes, links)

        elif term == 'gp + 2':
            gp_macro_two(context, operator, term, nodes, links)

        elif term == 'url':
            bpy.ops.node.sv_load_archived_blend_url()

        elif term == 'blend 2 zip':
            bpy.ops.node.blend_to_archive(archive_ext="zip")


# EOF
