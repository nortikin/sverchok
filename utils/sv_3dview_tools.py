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


def get_center(self, context):

    try:
        node = context.nodes.active
        if hasattr(node, 'get_center'):
            return node.get_center()

    except:
        self.report({'INFO'}, 'no active node found')


class Sv3DviewAlign(bpy.types.Operator):
    """ Zoom to viewer output """
    bl_idname = "node.view3d_align_from"
    bl_label = "Align 3dview to Viewer"
    # bl_options = {'REGISTER', 'UNDO'}

    fn_name = bpy.props.StringProperty(default='')
    # obj_type = bpy.props.StringProperty(default='MESH')

    def execute(self, context):

        vector_3d = get_center(self, context)
        if not vector_3d:
            return {'CANCELLED'}

        context.scene.cursor_location = vector_3d

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                ctx = bpy.context.copy()
                ctx['area'] = area
                ctx['region'] = area.regions[-1]
                bpy.ops.view3d.view_center_cursor(ctx)        

        return {'FINISHED'}



classes = [Sv3DviewAlign,]


def register():
    _ = [bpy.utils.register_class(cls) for cls in classes]


def unregister():
    _ = [bpy.utils.unregister_class(cls) for cls in classes[::-1]]


# if __name__ == '__main__':
#    register()
