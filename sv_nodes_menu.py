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


from nodeitems_utils import NodeItem
from sverchok.node_tree import SverchNodeCategory
from sverchok.sv_menu import make_node_cats

def juggle_and_join(node_cats):
    '''
    this step post processes the extended catagorization used
    by ctrl+space dynamic menu, and attempts to merge previously
    joined catagories. Why? Because the default menu gets very
    long if there are too many catagories.

    The only real alternative to this approach is to write a
    replacement for nodeitems_utils which respects catagories
    and submenus.

    '''
    node_cats = node_cats.copy()

    # join beta and alpha node cats
    alpha = node_cats.pop('Alpha Nodes')
    node_cats['Beta Nodes'].extend(alpha)

    # put masks into list main
    masks = node_cats.pop("List Masks")
    node_cats["List main"].extend(masks)

    # add extended gens to Gens menu
    gen_ext = node_cats.pop("Extended Generators")
    node_cats["Generators"].extend(gen_ext)

    return node_cats


def make_categories():
    original_categories = make_node_cats()
    node_cats = juggle_and_join(original_categories)

    node_categories = []
    howmanynodesare = 0
    for category, nodes in node_cats.items():
        name_big = "SVERCHOK_" + category.replace(' ', '_')
        node_categories.append(SverchNodeCategory(
            name_big, category,
            # bl_idname, name
            items=[NodeItem(props[0], props[1]) for props in nodes]))
        howmanynodesare += len(nodes)

    return node_categories, howmanynodesare
