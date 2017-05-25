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
        'file':'macro', 
        'ident': ['verbose_macro_handler', 'objs vd']},
    "> zen": {
        'display_name': "zen of Sverchok",
        'file':'macro', 
        'ident': ['verbose_macro_handler', 'zen']},
    "> sn petal": {
        'display_name': "load snlite w/ petalsine",
        'file':'macro', 
        'ident': ['verbose_macro_handler', 'sn petal']},
    "> monad info": {
        'display_name': "output current idx / total",
        'file':'macro', 
        'ident': ['verbose_macro_handler', 'monad info']}        
}



sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}


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
            # set location of snlite based on mouse?

            sv_path = os.path.dirname(sv_get_local_path()[0])
            snlite_template_path = os.path.join(sv_path, 'node_scripts', 'SNLite_templates')
            fullpath = os.path.join(snlite_template_path, 'petal_sine.py')
            
            txt = bpy.data.texts.load(fullpath)
            snlite.script_name = os.path.basename(txt.name)
            snlite.load()
        elif term == 'monad info':
            x, y = context.space_data.cursor_location[:]
            monad_info = nodes.new('SvMonadInfoNode')
            monad_info.location = x, y

