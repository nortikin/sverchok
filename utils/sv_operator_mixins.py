# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from bpy.props import StringProperty

class SvGenericNodeLocator():
    """
    usage:
    add this to an Operator class definition if you need to track the origin
    of a click.

    see at the bottom of this file in " class SvGenericCallbackOldOp " how to use it.
    you can then use the "node.wrapper_tracked_ui_draw_op", in the UI draw function..

    f.ex:
        callback = "node.sverchok_mesh_baker_mk3"
        self.wrapper_tracked_ui_draw_op(row, callback, icon='', text='')

    """
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

    def sv_execute(self, context, node):
        """ 
        you override this, inside this function you place the code you want to execute 
        if the locator finds the node.
        
        - you can use a return statement to end the sv_execute function early.
        - return can be one of two things. success or failure

            success:  (these are all equal)
                return False,
                return 0
                return None
                return
                return {'FINISHED'}

            failure:
                return {'CANCELLED'} as a regular execute function
        """
        pass

    def execute(self, context):
        node = self.get_node(context)
        if node:
            response = self.sv_execute(context, node)
            if response:
                return response
            return {'FINISHED'}

        msg = f'{self.bl_idname} was unable to locate the node <{self.tree_name}|{self.node_name}>'
        self.report({'ERROR'}, msg)
        return {'CANCELLED'}

class SvGenericCallbackWithParams():

    bl_idname = "node.sv_generic_callback_with_params"
    bl_label = "SvGeneric callback (with params)"

    '''
    #### using SvGenericCallbackWithParams(bpy.types.Operator) #####

    class SomeNode..


        def draw_buttons(self, context, layout):
            callback = "node.sv_generic_callback_with_params"
            my_op = layout.operator(callback, text='display_name').fn_name='some_function'
            my_op.your_custom_param_name = 'something'


        def some_function(self, operator):
            print(operator.your_custom_param_name)
            operator.report({  ...})
            return {'FINISHED'}

    '''    

    fn_name: bpy.props.StringProperty(default='')


    def execute(self, context):
        try:
            f = getattr(context.node, self.fn_name)(self)
            return f or {'FINISHED'}

        except Exception as err:
            print(repr(err))
            return {'CANCELLED'}

        # return just in case, else let the content of the called function decide the return value
        return {'FINISHED'}



class SvGenericFileSelector():

    bl_idname = "node.sv_generic_file_selector"
    bl_label = "sv File Select"

    '''

    #### using SvGenericFileSelector(bpy.types.Operator) #####

    class SomeNode..

        def draw_buttons(self, context, layout):
            callback = "node.sv_generic_file_selector"
            my_op = layout.operator(callback, text='pick file').fn_name='some_function'


        def some_function(self, operator):
            print(operator.filepath)   <---- will contain full path to the file selected from the dialogue
            operator.report({  ...})
            return {'FINISHED'}


    '''    

    fn_name: bpy.props.StringProperty(default='')
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for getting the file path",
        maxlen=1024, default="", subtype='FILE_PATH')

    def execute(self, context):
        try:
            f = getattr(self.node, self.fn_name)(self)
            return f or {'FINISHED'}

        except Exception as err:
            print(repr(err))
            return {'CANCELLED'}

        # return just in case, else let the content of the called function decide the return value
        return {'FINISHED'}


    def invoke(self, context, event):
        self.node = context.node
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvGenericDirectorySelector():

    bl_idname = "node.sv_generic_dir_selector"
    bl_label = "sv Dir Select"

    '''

    #### using SvGenericDirectorySelector(bpy.types.Operator) #####

    class SomeNode..

        def draw_buttons(self, context, layout):
            callback = "node.sv_generic_dir_selector"
            my_op = layout.operator(callback, text='pick directory').fn_name='some_function'


        def some_function(self, operator):
            print(operator.path)   <---- will contain full directory path selected from the dialogue
            operator.report({  ...})
            return {'FINISHED'}


    '''    

    fn_name: bpy.props.StringProperty(default='')
    directory: bpy.props.StringProperty(
        name="Base Path",
        description="Directory selected",
        maxlen=1024, default="", subtype='DIR_PATH')

    def execute(self, context):
        node = self.node   # definitely have the node here
        try:
            f = getattr(node, self.fn_name)(self)
            return f or {'FINISHED'}

        except Exception as err:
            print(repr(err))
            return {'CANCELLED'}

        # return just in case, else let the content of the called function decide the return value
        return {'FINISHED'}


    def invoke(self, context, event):
        self.node = context.node
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


class SvGenericCallbackOldOp(bpy.types.Operator, SvGenericNodeLocator):
    """ 
    This operator is generic and will call .fn_name on the instance of the caller node
    """
    bl_idname = "node.sverchok_generic_callback_old"
    bl_label = "Sverchok text input"
    bl_options = {'REGISTER', 'UNDO'}

    fn_name: StringProperty(name='function name')

    def execute(self, context):
        n = self.get_node(context)
        if not n:
            return {'CANCELLED'}

        f = getattr(n, self.fn_name, None)
        if not f:
            msg = f"{n.name} has no function named '{self.fn_name}'"
            self.report({"WARNING"}, msg)
            return {'CANCELLED'}
        f()

        return {'FINISHED'}


def register():
    bpy.utils.register_class(SvGenericCallbackOldOp)


def unregister():
    bpy.utils.unregister_class(SvGenericCallbackOldOp)
