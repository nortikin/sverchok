# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy

class SvWifiRenameOperator(bpy.types.Operator):

    bl_idname = "node.some_callback_identifier"
    bl_label = "Short Name"

    new_proposed_name: bpy.props.StringProperty(default='')
    fn_name: bpy.props.StringProperty(default='')
    ntree_name: bpy.props.StringProperty(default='')
    node_name: bpy.props.StringProperty(default='')

    def execute(self, context):

        # find active node, is it a wifi generator node?
        #   CANCELLED if not
        ng = 
        node =
        name = node.var_name

        # [ ] find all listeners in all nodegroups
        nodes = []
        for n in ng.nodes:
            if n.bl_idname == 'WifiInNode' and n.var_name == name:
                nodes.append(n)

        # [ ] test is the new proposed name already used?

        # [ ] freeze updates

        # [ ] rename


        return {'FINISHED'}


classes = [SvWifiRenameOperator]
register, unregister = bpy.utils.register_classes_factory(classes)