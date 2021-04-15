# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

class SvNodeViewZoomBorder(bpy.types.Operator):
    """
    this is to be called from anywhere.
    """

    bl_idname = "node.sv_nodeview_zoom_border"
    bl_label = "NodeView Zoom Border Operator"
    bl_options = {'INTERNAL'}

    idname: bpy.props.StringProperty(default='')
    idtree: bpy.props.StringProperty(default='')

    def execute(self, context):
        """
        - [ ] locate the first nodeview window / area of the invoking node

        """
        if self.idtree and self.idname:
            ng = bpy.data.node_groups[self.idtree]
            node = ng.nodes[self.idname]
        else:
            try:
                node = context.node
            except:
                print("SvNodeViewZoomBorder -> context.node : not available")
                return {'CANCELLED'}


        node_x, node_y = node.absolute_location
        border_width = node.width * 4
        border_height = node.height * 3
        params = dict(
            xmin = node_x - border_width / 2,
            xmax = node_x + border_width / 2,
            ymin = node_y - border_height / 2,
            ymax = node_y + border_height / 2,
            wait_for_input = False,
            zoom_out = True
        )
        
        print("Reached the override section", params, node, ng)

        # https://docs.blender.org/api/current/bpy.ops.html#execution-context
        for window in bpy.context.window_manager.windows:
            screen = window.screen
    
            for area in screen.areas:        
                if area.type == 'NODE_EDITOR':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            override = {'window': window, 'screen': screen, 'area': area, 'region': region}
                            bpy.ops.view2d.zoom_border(override, **params)
                            break

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SvNodeViewZoomBorder)

def unregister():
    bpy.utils.unregister_class(SvNodeViewZoomBorder)
