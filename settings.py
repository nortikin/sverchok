import os

import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty, FloatProperty, StringProperty

from sverchok import data_structure
from sverchok.core import handlers
from sverchok.core import update_system
from sverchok.utils import sv_panels_tools
from sverchok.ui import color_def


class SverchokPreferences(AddonPreferences):

    bl_idname = __package__

    def update_debug_mode(self, context):
        data_structure.DEBUG_MODE = self.show_debug

    def update_heat_map(self, context):
        data_structure.heat_map_state(self.heat_map)

    def set_frame_change(self, context):
        handlers.set_frame_change(self.frame_change_mode)

    def update_theme(self, context):
        color_def.rebuild_color_cache()
        if self.auto_apply_theme:
            color_def.apply_theme()

    tab_modes = [(k, k, '', i) for i, k in enumerate(["General", "Node Defaults", "Theme"])]
    
    selected_tab = bpy.props.EnumProperty(
        items=tab_modes,
        description="pick viewing mode",
        default="General"
    )

    #  debugish...
    show_debug = BoolProperty(
        name="Print update timings",
        description="Print update timings in console",
        default=False, subtype='NONE',
        update=update_debug_mode)

    no_data_color = FloatVectorProperty(
        name="No data", description='When a node can not get data',
        size=3, min=0.0, max=1.0,
        default=(1, 0.3, 0), subtype='COLOR',
        update=update_system.update_error_colors)

    exception_color = FloatVectorProperty(
        name="Error", description='When node has an exception',
        size=3, min=0.0, max=1.0,
        default=(0.8, 0.0, 0), subtype='COLOR',
        update=update_system.update_error_colors)

    #  heat map settings
    heat_map = BoolProperty(
        name="Heat map",
        description="Color nodes according to time",
        default=False, subtype='NONE',
        update=update_heat_map)

    heat_map_hot = FloatVectorProperty(
        name="Heat map hot", description='',
        size=3, min=0.0, max=1.0,
        default=(.8, 0, 0), subtype='COLOR')

    heat_map_cold = FloatVectorProperty(
        name="Heat map cold", description='',
        size=3, min=0.0, max=1.0,
        default=(1, 1, 1), subtype='COLOR')

    #  theme settings

    sv_theme = EnumProperty(
        items=color_def.themes,
        name="Theme preset",
        description="Select a theme preset",
        update=color_def.color_callback,
        default="default_theme")

    auto_apply_theme = BoolProperty(
        name="Apply theme", description="Apply theme automaticlly",
        default=False)

    apply_theme_on_open = BoolProperty(
        name="Apply theme", description="Apply theme automaticlly",
        default=False)

    color_viz = FloatVectorProperty(
        name="Visualization", description='',
        size=3, min=0.0, max=1.0,
        default=(1, 0.3, 0), subtype='COLOR',
        update=update_theme)

    color_tex = FloatVectorProperty(
        name="Text", description='',
        size=3, min=0.0, max=1.0,
        default=(0.5, 0.5, 1), subtype='COLOR',
        update=update_theme)

    color_sce = FloatVectorProperty(
        name="Scene", description='',
        size=3, min=0.0, max=1.0,
        default=(0, 0.5, 0.2), subtype='COLOR',
        update=update_theme)

    color_lay = FloatVectorProperty(
        name="Layout", description='',
        size=3, min=0.0, max=1.0,
        default=(0.674, 0.242, 0.363), subtype='COLOR',
        update=update_theme)

    color_gen = FloatVectorProperty(
        name="Generator", description='',
        size=3, min=0.0, max=1.0,
        default=(0, 0.5, 0.5), subtype='COLOR',
        update=update_theme)

    #  frame change
    frame_change_modes = [
        ("PRE", "Pre", "Update Sverchok before frame change", 0),
        ("POST", "Post", "Update Sverchok after frame change", 1),
        ("NONE", "None", "Sverchok doesn't update on frame change", 2)
    ]

    frame_change_mode = EnumProperty(
        items=frame_change_modes,
        name="Frame change",
        description="Select frame change handler",
        default="POST",
        update=set_frame_change)

    #  ctrl+space settings

    show_icons = BoolProperty(
        name="Show icons in ctrl+space menu",
        default=False,
        description="Use icons in ctrl+space menu")

    over_sized_buttons = BoolProperty(
        default=False, name="Big buttons", description="Very big buttons")

    enable_live_objin = BoolProperty(
        description="Objects in edit mode will be updated in object-in Node")

    stethoscope_view_scale = FloatProperty(
        default=1.0, min=0.01, step=0.01, description='default stethoscope scale')
    stethoscope_view_xy_multiplier = FloatProperty(
        default=1.0, min=0.01, step=0.01, description='default stethoscope scale')

    datafiles = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    defaults_location = StringProperty(default=datafiles, description='usually ..data_files\\sverchok\\defaults\\nodes.json')


    def draw(self, context):

        layout = self.layout
        layout.row().prop(self, 'selected_tab', expand=True)

        if self.selected_tab == "General":

            col = layout.row().column()
            col_split = col.split(0.5)
            col1 = col_split.column()
            col1.label(text="UI:")
            col1.prop(self, "show_icons")
            col1.prop(self, "over_sized_buttons")
            col1.prop(self, "enable_live_objin", text='Enable Live Object-In')

            col2 = col_split.split().column()
            col2.label(text="Frame change handler:")
            col2.row().prop(self, "frame_change_mode", expand=True)
            col2.separator()

            col2box = col2.box()
            col2box.label(text="Debug:")
            col2box.prop(self, "show_debug")
            col2box.prop(self, "heat_map")

        if self.selected_tab == "Node Defaults":

            row = layout.row()
            col = row.column(align=True)
            row_sub1 = col.row().split(0.5)
            box_sub1 = row_sub1.box()
            box_sub1_col = box_sub1.column(align=True)
            box_sub1_col.label('stethoscope mk2 settings')
            box_sub1_col.prop(self, 'stethoscope_view_scale', text='scale')
            box_sub1_col.prop(self, 'stethoscope_view_xy_multiplier', text='xy multiplier')

            col3 = row_sub1.split().column()
            col3.label('Location of custom defaults')
            col3.prop(self, 'defaults_location', text='')


        if self.selected_tab == "Theme":

            row = layout.row()
            col = row.column(align=True)
            split = col.row().split(0.66)
            split2 = col.row().split(0.66)
            left_split = split.row()
            right_split = split.row()

            split_viz_colors = left_split.column().split(percentage=0.5, align=True)

            if True:
                col1 = split_viz_colors.column()
                for name in ['color_viz', 'color_tex', 'color_sce']:
                    r = col1.row()
                    r.prop(self, name)

                col2 = split_viz_colors.column()
                for name in ['color_lay', 'color_gen']:
                    r = col2.row()
                    r.prop(self, name)

            split_extra_colors = split2.column().split()
            col_x1 = split_extra_colors.column()
            col_x1.label("Error colors: ( error / no data )")
            row_x1 = col_x1.row()
            row_x1.prop(self, "exception_color", text='')
            row_x1.prop(self, "no_data_color", text='')

            col_x2 = split_extra_colors.split().column()
            col_x2.label("Heat map colors: ( hot / cold )")
            row_x2 = col_x2.row()
            row_x2.active = self.heat_map
            row_x2.prop(self, "heat_map_hot", text='')
            row_x2.prop(self, "heat_map_cold", text='')

            col3 = right_split.column()
            col3.label('Theme:')
            col3.prop(self, 'sv_theme', text='')
            col3.separator()
            col3.prop(self, 'auto_apply_theme', text="Auto apply theme changes")
            col3.prop(self, 'apply_theme_on_open', text="Apply theme when opening file")
            col3.operator('node.sverchok_apply_theme', text="Apply theme to layouts")


        # FOOTER

        row = layout.row()
        col = row.column(align=True)
        col.label(text="Links:")
        row1 = col.row(align=True)
        row1.scale_y = 2.0
        row1.operator('wm.url_open', text='Sverchok home page').url = 'http://nikitron.cc.ua/blend_scripts.html'
        row1.operator('wm.url_open', text='Documentation').url = 'http://nikitron.cc.ua/sverch/html/main.html'

        if context.scene.sv_new_version:
            row1.operator('node.sverchok_update_addon', text='Upgrade Sverchok addon')
        else:
            row1.operator('node.sverchok_check_for_upgrades_wsha', text='Check for new version')


def register():
    bpy.utils.register_class(SverchokPreferences)


def unregister():
    bpy.utils.unregister_class(SverchokPreferences)

if __name__ == '__main__':
    register()
