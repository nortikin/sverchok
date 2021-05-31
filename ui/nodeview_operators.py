# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from sverchok.core.update_system import reset_timing_graphs
from sverchok.utils.sv_operator_mixins import SvGenericNodeLocator
from sverchok.ui.bgl_callback_nodeview import callback_disable_filtered
from sverchok.utils.nodeview_time_graph_drawing import (
    start_time_graph, start_node_times, timer_config)


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

class SvNodeViewShowTimeInfo(bpy.types.Operator):

    bl_idname = "node.nodeview_timeinfo_callback"
    bl_label = "Start/Stop info display"
    bl_options = {'INTERNAL'}

    tree_name: bpy.props.StringProperty(default='')
    fn_name: bpy.props.StringProperty(default='')

    def disable_callbacks(self):
        callback_disable_filtered("_time_graph_overlay")
        callback_disable_filtered("_node_time_info")

    def execute(self, context):
        """
        set bgl callback for the timing graph + node info in following ways
        - (initialize and start) 
        - (stop)
        """
        ng = bpy.data.node_groups.get(self.tree_name)
        if self.fn_name == "start":
            if ng:
                self.disable_callbacks()
                reset_timing_graphs()
                bpy.ops.node.sverchok_update_current(node_group=self.tree_name)
                start_time_graph(ng)
                start_node_times(ng)
                timer_config.set_drawing_state(ng, True)
                timer_config.set_other_trees_to_false(ng)
            else:
                print("not found!")
        else:
            timer_config.set_drawing_state(ng, False)
            self.disable_callbacks()
            reset_timing_graphs()

        return {'FINISHED'}


classes = [SvNodeViewZoomBorder, SvNodeViewShowTimeInfo]
register, unregister = bpy.utils.register_classes_factory(classes)
