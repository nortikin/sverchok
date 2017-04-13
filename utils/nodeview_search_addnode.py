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
import nodeitems_utils
from bpy.types import Operator
from bpy.props import EnumProperty
from bl_operators.node import NodeAddOperator
from nodeitems_utils import _node_categories

from sverchok.ui.nodeview_space_menu import _items_to_remove



def ff_node_items_iter(context):
    cats = _items_to_remove.get('sverchok_popped')
    if not cats:
        return

    for cat in cats[0]:
        for item in cat.items(context):
            if isinstance(item, nodeitems_utils.NodeItem):
                yield item


# This is heavily borrowed  (almost verabatim) from 
# - nodeitems_utils 
# - bl_operators.node.  add_search

class SvNodeViewSearchNode(NodeAddOperator, Operator):
    '''Add a Sv node to the active tree'''
    bl_idname = "node.add_sverchok_search"
    bl_label = "Search and Add Node"
    bl_options = {'REGISTER', 'UNDO'}
    bl_property = "node_item"

    _enum_items = []


    def node_enum_items(self, context):
        enum_items = SvNodeViewSearchNode._enum_items
        enum_items.clear()

        for index, item in enumerate(ff_node_items_iter(context)):
            nodetype = getattr(bpy.types, item.nodetype)
            if nodetype:
                enum_items.append((str(index), item.label, nodetype.bl_rna.description, index))
        return enum_items


    def find_node_item(self, context):
        node_item = int(self.node_item)
        for index, item in enumerate(ff_node_items_iter(context)):
            if index == node_item:
                return item
        return None


    node_item = EnumProperty(name="Node Type", description="Node type", items=node_enum_items)


    def execute(self, context):
        item = self.find_node_item(context)
        self._enum_items.clear()

        if item:
            self.create_node(context, item.nodetype)

            if self.use_transform:
                bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
            return {'FINISHED'}

        return {'CANCELLED'}


    def invoke(self, context, event):
        self.store_mouse_cursor(context, event)
        context.window_manager.invoke_search_popup(self)
        return {'CANCELLED'}



classes = [SvNodeViewSearchNode,]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in classes]
