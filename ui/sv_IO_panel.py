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
from sverchok.node_tree import SverchCustomTree
from sverchok.node_tree import SverchCustomTreeNode

from sverchok.utils.sv_IO_panel_tools import (
		_EXPORTER_REVISION_, get_file_obj_from_zip, find_enumerators,
		compile_socket, write_json, has_state_switch_protection,
		create_dict_of_tree, import_tree
		)


class SverchokIOLayoutsMenu(bpy.types.Panel):
    bl_idname = "Sverchok_iolayouts_menu"
    bl_label = "SV import/export"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    bl_options = {'DEFAULT_CLOSED'}
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.node_tree.bl_idname == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        layout = self.layout
        ntree = context.space_data.node_tree
        row = layout.row()
        row.scale_y = 0.5
        row.label(_EXPORTER_REVISION_)

        ''' export '''

        col = layout.column(align=False)
        row1 = col.row(align=True)
        row1.scale_y = 1.4
        row1.prop(ntree, 'compress_output', text='Zip', toggle=True)
        imp = row1.operator('node.tree_exporter', text='Export', icon='FILE_BACKUP')
        imp.id_tree = ntree.name
        imp.compress = ntree.compress_output

        ''' import '''

        col = layout.column(align=True)
        row3 = col.row(align=True)
        row3.scale_y = 1
        row3.prop(ntree, 'new_nodetree_name', text='')
        row2 = col.row(align=True)
        row2.scale_y = 1.2
        exp1 = row2.operator('node.tree_importer', text='Here', icon='RNA')
        exp1.id_tree = ntree.name

        exp2 = row2.operator('node.tree_importer', text='New', icon='RNA_ADD')
        exp2.id_tree = ''
        exp2.new_nodetree_name = ntree.new_nodetree_name


def register():
    bpy.utils.register_class(SverchokIOLayoutsMenu)


def unregister():
    bpy.utils.unregister_class(SverchokIOLayoutsMenu)


if __name__ == '__main__':
    register()
