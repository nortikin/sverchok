# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy


class Show3DProperties:
    """
    Mixin for classes which should show their properties in 3D panel
    It is better to use this mixin because if any changes it simpler to fix them in one place
    """
    draw_3dpanel: bpy.props.BoolProperty(
        name="To 3D Panel",
        description="Show this node in 3D panel", 
        default=False,
        update=lambda n, c: bpy.context.scene.sv_ui_node_props.update_properties()  # automatically add/remove item
    )

    def draw_buttons_3dpanel(self, layout, in_menu=False):
        """
        This method should draw properties in 3D panel
        In current implementation UI should be drawn only in one row
        :param in_menu: in case if node draw properties more than in one row it can use popup menu
        """
        raise AttributeError(f'Method="draw_buttons_3dpanel" should be implemented in class="{type(self).__name__}"')

        # just example of popup menu
        if not in_menu:
            menu = layout.operator('node.popup_3d_menu', 'Sho props')
            menu.tree_name = self.id_data.name
            menu.node_name = self.name
        else:
            layout.prop(self, 'mu_prop')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'draw_3dpanel', icon='PLUGIN', text='to 3dview')
        if hasattr(super(), 'draw_buttons_ext'):
            super().draw_buttons_ext(context, layout)  # in case if mixin override other class with such method


class Popup3DMenu(bpy.types.Operator):
    """
    Popup menu for showing node properties in 3D panel
    It will call 'draw_buttons_3dpanel' method with extra argument 'in_menu=True'
    """
    bl_idname = "node.popup_3d_menu"
    bl_label = "Show properties"
    bl_options = {'INTERNAL'}

    tree_name: bpy.props.StringProperty()
    node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def draw(self, context):
        tree = bpy.data.node_groups.get(self.tree_name)
        node = tree.nodes.get(self.node_name)
        getattr(node, 'draw_buttons_3dpanel')(self.layout, in_menu=True)


register, unregister = bpy.utils.register_classes_factory([Popup3DMenu])
