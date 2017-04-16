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
from sverchok.utils.sv_default_macros import macros
from nodeitems_utils import _node_categories

sv_tree_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
node_cats = make_node_cats()
addon_name = sverchok.__name__

# pylint: disable=c0326

macros = {
    # trigger:  [descriptor, action route]
    "> obj vd": ["active_obj into objlite + vdmk2","<file:macro> <ident:obj_in_lite_and_vd>"],
    "> objs vd": ["multi obj in","<file:macro> <ident:ob3_and_vd>"]
}


def gather_items():
    fx = []
    idx = 0
    for _, node_list in node_cats.items():
        for item in node_list:
            if item[0] in {'separator', 'NodeReroute'}:
                continue
            nodetype = getattr(bpy.types, item[0])
            desc = nodetype.bl_rna.description
            show_string = nodetype.bl_label + ((' | ' + desc) if desc else '')
            fx.append((str(idx), show_string, '', idx))
            idx += 1

    for k, v in macros.items():
        fx.append((k, k + " | " + v[0], '', idx))
        idx += 1

    # extend(idx, fx, '/datafiles/sverchok/user_macros.fx')

    return fx

loop = {}

def item_cb(self, context):
    return loop.get('results')


class SvExtraSearch(bpy.types.Operator):
    """ Extra Search library """
    bl_idname = "node.sv_extra_search"
    bl_label = "Extra Search"
    bl_property = "my_enum"

    my_enum = bpy.props.EnumProperty(items=item_cb)

    def execute(self, context):
        self.report({'INFO'}, "Selected: %s" % self.my_enum)
        if self.my_enum.isnumeric():
            print(loop['results'][int(self.my_enum)])
        else:
            print(self.my_enum)
        return {'FINISHED'}

    def invoke(self, context, event):
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
