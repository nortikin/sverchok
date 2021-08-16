# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator


class SvNodeViewZoomBorder(bpy.types.Operator, SvGenericNodeLocator):
    """
    This operator takes a tree name and a node name and scans through the open nodeviews to find 
    the node and select it and set active, and then executes the view_selected operator
    """

    bl_idname = "node.sv_nodeview_zoom_border"
    bl_label = "NodeView Zoom Border Operator"
    bl_options = {'INTERNAL'}

    def sv_execute(self, context, node):

        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == 'NODE_EDITOR':
                    for space in area.spaces:
                        if hasattr(space, "edit_tree"):
                            ng = space.edit_tree
                            if ng == self.get_tree():
                                # unselect all first.
                                for treenode in ng.nodes:
                                    treenode.select = False

                                # set active, and select to get the thicker border around the node
                                ng.nodes.active = node
                                node.select = True
                            else:
                                continue

                    for region in area.regions:
                        if region.type == 'WINDOW': 
                            override = {
                                'window': window,
                                'screen': screen,
                                'area': area,
                                'region': region
                            }
                            bpy.ops.node.view_selected(override)
                            break


classes = [SvNodeViewZoomBorder]
register, unregister = bpy.utils.register_classes_factory(classes)
