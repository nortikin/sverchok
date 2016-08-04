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
from bpy.types import Panel

from sverchok.utils.sv_monad_tools import set_multiple_attrs

class SvCustomGroupInterface(Panel):
    bl_idname = "SvCustomGroupInterface"
    bl_label = "Sv Custom Group Interface"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    # bl_options = {'DEFAULT_CLOSED'}
    use_pin = True

    @classmethod
    def poll(cls, context):
        print('edit_tree: ', context.space_data.edit_tree)
        try:
            path = context.space_data.path
            return len(path) == 2 and path[1].node_tree.get('sub_group')
        except:
            return False

    def draw(self, context):
        ntree = context.space_data.edit_tree
        nodes = ntree.nodes

        layout = self.layout
        row = layout.row()

        # draw left and right columns corresponding to sockets_types, display_name, move_operator
        in_node = nodes.get('Group Inputs Exp')
        out_node = nodes.get('Group Outputs Exp')
        
        if not (in_node and out_node):
            return

        width = context.region.width
        # should ideally take dpi into account, 
        if width > 310:
            row = layout.row()
            split = row.split(percentage=0.5)
            column1 = split.box().column()
            split = split.split()
            column2 = split.box().column()
        else:
            column1 = layout.row().box().column()
            layout.separator()
            column2 = layout.row().box().column()

        move = 'node.sverchok_move_socket_exp'
        rename = 'node.sverchok_rename_socket_exp'
        edit = 'node.sverchok_edit_socket_exp'

        def draw_socket_row(_column, s, index):
            if s.bl_idname == 'SvDummySocket':
                return

            # < type | (re)name     | /\  \/  X >
            
            # lots of repetition here...
            socket_ref = dict(pos=index, node_name=s.node.name)

            r = _column.row(align=True)
            r.template_node_socket(color=s.draw_color(s.node, context))

            m = r.operator(edit, icon='PLUGIN', text='')
            set_multiple_attrs(m, **socket_ref)

            m = r.operator(rename, text=s.name)
            set_multiple_attrs(m, **socket_ref)

            m = r.operator(move, icon='TRIA_UP', text='')
            set_multiple_attrs(m, **socket_ref, direction=-1)
            
            m = r.operator(move, icon='TRIA_DOWN', text='')
            set_multiple_attrs(m, **socket_ref, direction=1)

            m = r.operator(move, icon='X', text='')
            set_multiple_attrs(m, **socket_ref, direction=0)


        column1.label('inputs')
        for i, s in enumerate(in_node.outputs):
            draw_socket_row(column1, s, i)

        column2.label('outputs')
        for i, s in enumerate(out_node.inputs):
            draw_socket_row(column2, s, i)
