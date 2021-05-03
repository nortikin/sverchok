# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import StringProperty

class SvGenericNodeLocator():
    tree_name: StringProperty(default='', description="name of the node tree")
    node_name: StringProperty(default='', description="name of the node")

    def get_node(self, context):
        """ context.node is usually provided, else tree_name/node_name must be passed """
        if self.tree_name and self.node_name:
            return bpy.data.node_groups[self.tree_name].nodes[self.node_name]

        if hasattr(context, "node"):
            return context.node

        print("treename or nodename not supplied, node not found in available trees")
        print(f"received tree_name: {tree_name} and node_name: {node_name}")
        return None

    def get_tree(self):
        return bpy.data.node_groups.get(self.tree_name)


class SvGenericCallbackOldOp(bpy.types.Operator):
    """ 
    This operator is generic and will call .fn_name on the instance of the caller node
    """
    bl_idname = "node.sverchok_generic_callback_old"
    bl_label = "Sverchok text input"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name: StringProperty(name='function name')

    # this information is not communicated unless you trigger it from a node
    # in the case the operator button appears on a 3dview panel, it will need to pass these too.
    tree_name: StringProperty(default='')
    node_name: StringProperty(default='')

    def get_node(self, context):
        """ context.node is usually provided, else tree_name/node_name must be passed """
        if self.tree_name and self.node_name:
            return bpy.data.node_groups[self.tree_name].nodes[self.node_name]

        return context.node

    def execute(self, context):
        n = self.get_node(context)

        f = getattr(n, self.fn_name, None)
        if not f:
            msg = "{0} has no function named '{1}'".format(n.name, self.fn_name)
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}
        f()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SvGenericCallbackOldOp)


def unregister():
    bpy.utils.unregister_class(SvGenericCallbackOldOp)
