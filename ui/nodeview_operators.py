# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.sv_operator_utils import SvGenericNodeLocator
import bpy

class SvNodeViewZoomBorder(bpy.types.Operator, SvGenericNodeLocator):
    """
    this is to be called from anywhere.
    """

    bl_idname = "node.sv_nodeview_zoom_border"
    bl_label = "NodeView Zoom Border Operator"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        """
        - [ ] locate the first nodeview window / area of the invoking node

        """
        node = self.get_node(context)
        if not node:
            print("SvNodeViewZoomBorder was not able to locate the node")
            return {'CANCELLED'}

        """
        ng_view = space.edit_tree

        # ng_view can be None
        if not ng_view:
            return

        ng_name = space.edit_tree.name
        """

        # https://docs.blender.org/api/current/bpy.ops.html#execution-context
        for window in bpy.context.window_manager.windows:
            screen = window.screen
    
            for area in screen.areas:        
                if area.type == 'NODE_EDITOR':  # and nodeeditor is Sverchok and nodetree is nodetree.
                    for region in area.regions:
                        if region.type == 'WINDOW': 
                            override = {
                                'window': window,
                                'screen': screen,
                                'area': area,
                                'region': region
                            }
                            # bpy.ops.node.view_all(override)
                            # bpy.ops.view2d.zoom_border(override, **params)
                            bpy.ops.node.view_selected(override)
                            break

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SvNodeViewZoomBorder)

def unregister():
    bpy.utils.unregister_class(SvNodeViewZoomBorder)
