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

from node_tree import SverchCustomTreeNode


class Sv3DviewPropsNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Sv 3Dview Props Node '''
    bl_idname = 'Sv3DviewPropsNode'
    bl_label = 'Sv 3Dview Props Node'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def init(self, context):
        pass

    def draw_buttons(self, context, layout):
        context = bpy.context
        row = layout.row(align=True)

        idx = -1
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    idx += 1
                    n_panel = area.spaces[0]

                    row = layout.row(align=True)
                    row.label('3dview {idx}'.format(idx=idx))
                    row = layout.row(align=True)
                    row.prop(n_panel, 'show_only_render', text='show render')
                    row = layout.row(align=True)
                    row.prop(n_panel, 'show_floor', text='showg grid')

                    row = layout.row(align=True)
                    row.prop(n_panel, "show_axis_x", text="X", toggle=True)
                    row.prop(n_panel, "show_axis_y", text="Y", toggle=True)
                    row.prop(n_panel, "show_axis_z", text="Z", toggle=True)

        # bpy.context.scene.world?, should check properly
        world = bpy.data.worlds['World']
        theme = bpy.context.user_preferences.themes['Default']

        row = layout.row(align=True)
        row.prop(world, 'horizon_color', text='horizon color')

        row = layout.row(align=True)
        row.prop(theme, 'view_3d.grid', text='grid color')

        row = layout.row(align=True)
        gradients = theme.view_3d.space.gradients
        row.prop(gradients, 'show_grad', text='show gradient')

        row = layout.row(align=True)
        row.prop(gradients, 'high_gradient', text='high gradient')
        row.prop(gradients, 'gradient', text='low gradient')

    def update(self):
        pass

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(Sv3DviewPropsNode)


def unregister():
    bpy.utils.unregister_class(Sv3DviewPropsNode)
