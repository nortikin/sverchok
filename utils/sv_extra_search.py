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


import bpy

import sverchok
import nodeitems_utils
from sverchok.menu import make_node_cats
from sverchok.ui.sv_icons import custom_icon
from sverchok.utils.sv_default_macros import macros, DefaultMacros
from nodeitems_utils import _node_categories

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
node_cats = make_node_cats()
addon_name = sverchok.__name__

loop = {}
loop_reverse = {}

# pylint: disable=c0326

def format_item(k, v):
    return k + " | " + v['display_name']

def slice_docstring(desc):
    if '///' in desc:
        desc = desc.strip().split('///')[0]
    return desc

def ensure_valid_show_string(item):
    '''  the font is not fixed width, it makes litle sense to calculate chars'''
    hardcoded_maxlen = 20
    nodetype = getattr(bpy.types, item[0])
    loop_reverse[nodetype.bl_label] = item[0]
    description = slice_docstring(nodetype.bl_rna.description).strip()

    # ensure it's not too long
    if description:
        if len(description) > hardcoded_maxlen:
            description = description[:hardcoded_maxlen]
        description = ' | ' + description
    
    return nodetype.bl_label + description

def gather_items():
    fx = []
    idx = 0
    for _, node_list in node_cats.items():
        for item in node_list:
            if item[0] in {'separator', 'NodeReroute'}:
                continue
            
            fx.append((str(idx), ensure_valid_show_string(item), '', idx))
            idx += 1

    for k, v in macros.items():
        fx.append((k, format_item(k, v), '', idx))
        idx += 1

    # extend(idx, fx, '/datafiles/sverchok/user_macros.fx')

    return fx


def item_cb(self, context):
    return loop.get('results')


class SvExtraSearch(bpy.types.Operator):
    """ Extra Search library """
    bl_idname = "node.sv_extra_search"
    bl_label = "Extra Search"
    bl_property = "my_enum"

    my_enum = bpy.props.EnumProperty(items=item_cb)

    def bl_idname_from_bl_label(self, context):
        macro_result = loop['results'][int(self.my_enum)]
        """
        if ' | ' in macro_result[1]:
            bl_label = macro_result[1].split(' | ')[0].strip()
        else:
            bl_label = macro_result[1].strip()
        """

        bl_label = macro_result[1].split(' | ')[0].strip()
        return loop_reverse[bl_label]

    def execute(self, context):
        self.report({'INFO'}, "Selected: %s" % self.my_enum)
        if self.my_enum.isnumeric():
            macro_bl_idname = self.bl_idname_from_bl_label(self)
            DefaultMacros.ensure_nodetree(self, context)
            bpy.ops.node.sv_macro_interpretter(macro_bl_idname=macro_bl_idname)
        else:
            print(self.my_enum)
            macro_reference = macros.get(self.my_enum)
            if macro_reference:
                handler, term = macro_reference.get('ident')
                getattr(DefaultMacros, handler)(self, context, term)

        return {'FINISHED'}

    def invoke(self, context, event):
        # event contains mouse xy, can pass too! 
        loop['results'] = gather_items()
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


classes = [SvExtraSearch,]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in classes:
        bpy.utils.unregister_class(class_name)
