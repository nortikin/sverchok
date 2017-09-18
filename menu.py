# -*- coding: utf-8 -*-
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
from os.path import dirname
from collections import OrderedDict

import bpy
from nodeitems_utils import NodeCategory, NodeItem, NodeItemCustom
import nodeitems_utils

import sverchok
from sverchok.utils import get_node_class_reference
from sverchok.utils.sv_help import build_help_remap


class SverchNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'SverchCustomTreeType'


def make_node_cats():
    '''
    this loads the index.md file and converts it to an OrderedDict of node categories.

    '''

    index_path = os.path.join(dirname(__file__), 'index.md')

    node_cats = OrderedDict()
    with open(index_path) as md:
        category = None
        temp_list = []
        for line in md:
            if not line.strip():
                continue
            if line.strip().startswith('>'):
                continue
            elif line.startswith('##'):
                if category:
                    node_cats[category] = temp_list
                category = line[2:].strip()
                temp_list = []

            elif line.strip() == '---':
                temp_list.append(['separator'])
            else:
                bl_idname = line.strip()
                temp_list.append([bl_idname])

        # final append
        node_cats[category] = temp_list
    
    return node_cats


def juggle_and_join(node_cats):
    '''
    this step post processes the extended catagorization used
    by ctrl+space dynamic menu, and attempts to merge previously
    joined catagories. Why? Because the default menu gets very
    long if there are too many categories.

    The only real alternative to this approach is to write a
    replacement for nodeitems_utils which respects categories
    and submenus.

    '''
    node_cats = node_cats.copy()

    # join beta and alpha node cats
    alpha = node_cats.pop('Alpha Nodes')
    node_cats['Beta Nodes'].extend(alpha)

    # put masks into list main
    for ltype in ["List Masks", "List Mutators"]:
        node_refs = node_cats.pop(ltype)
        node_cats["List Main"].extend(node_refs)

    # add extended gens to Gens menu
    gen_ext = node_cats.pop("Generators Extended")
    node_cats["Generators"].extend(gen_ext)

    return node_cats



def sv_group_items(context):
    """
    Based on the built in node_group_items in the blender distrubution
    somewhat edited to fit.
    """
    if context is None:
        return
    space = context.space_data
    if not space:
        return
    ntree = space.edit_tree
    if not ntree:
        return

    yield NodeItemCustom(draw=draw_node_ops)

    def contains_group(nodetree, group):
        if nodetree == group:
            return True
        else:
            for node in nodetree.nodes:
                if node.bl_idname in node_tree_group_type.values() and node.node_tree is not None:
                    if contains_group(node.node_tree, group):
                        return True
        return False

    if ntree.bl_idname == "SverchGroupTreeType":
        yield NodeItem("SvMonadInfoNode", "Monad Info")

    for monad in context.blend_data.node_groups:
        if monad.bl_idname != "SverchGroupTreeType":
            continue
        # make sure class exists
        cls_ref = get_node_class_reference(monad.cls_bl_idname)

        if cls_ref and monad.cls_bl_idname:
            yield NodeItem(monad.cls_bl_idname, monad.name)
        elif monad.cls_bl_idname:
            monad_cls_template_dict = {"cls_bl_idname": "str('{}')".format(monad.cls_bl_idname)}
            yield NodeItem("SvMonadGenericNode", monad.name, monad_cls_template_dict)



def draw_node_ops(self,layout, context):

    make_monad = "node.sv_monad_from_selected"
    ungroup_monad = "node.sv_monad_expand"
    update_import = "node.sv_monad_class_update"
    layout.operator(make_monad, text='make group (+relink)', icon='RNA')
    layout.operator(make_monad, text='make group', icon='RNA').use_relinking = False
    layout.operator(ungroup_monad, text='ungroup', icon='RNA')
    layout.operator(update_import, text='update appended/linked', icon='RNA')
    layout.separator()

def make_categories():
    original_categories = make_node_cats()

    node_cats = juggle_and_join(original_categories)
    node_categories = []
    node_count = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(
            SverchNodeCategory(
                name_big,
                category,
                items=[NodeItem(props[0]) for props in nodes if not props[0] == 'separator']))
        node_count += len(nodes)
    node_categories.append(SverchNodeCategory("SVERCHOK_GROUPS", "Groups", items=sv_group_items))

    return node_categories, node_count, original_categories


def reload_menu():
    menu, node_count, original_categories = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu)
    
    build_help_remap(original_categories)


def register():
    menu, node_count, original_categories = make_categories()
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
    nodeitems_utils.register_node_categories("SVERCHOK", menu)

    build_help_remap(original_categories)

    print("\n** Sverchok loaded with {i} nodes **".format(i=node_count))


def unregister():
    if 'SVERCHOK' in nodeitems_utils._node_categories:
        nodeitems_utils.unregister_node_categories("SVERCHOK")
