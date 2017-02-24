import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty

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

    over_sized_buttons = BoolProperty(default=False, name="Big buttons",
                                      description="Very big buttons")

    enable_live_objin = BoolProperty(
        description="Objects in edit mode will be updated in object-in Node")

    #  bgl viewer settings

    custom_font_id = IntProperty()


    def draw(self, context):
        layout = self.layout
        # row = layout.split(percentage=0.33)
        row = layout

        col = row.column(align=True)
        col.label(text="General:")
        col.label(text="Frame change handler:")
        row1 = col.row()
        row1.prop(self, "frame_change_mode", expand=True)
        col.prop(self, "show_icons")
        col.prop(self, "over_sized_buttons")
        col.prop(self, "enable_live_objin", text='Enable Live Object-In')
        col.separator()

        col.label(text="Sverchok node theme settings")

        row2 = col.row()
        row2.prop(self, 'auto_apply_theme', text="Auto apply theme changes")
        row2.prop(self, 'apply_theme_on_open', text="Apply theme when opening file")

        row2.operator('node.sverchok_apply_theme', text="Apply theme to layouts")

        col1 = col.split(percentage=.5, align=True)
        col1.prop(self, 'sv_theme')
        col.separator()

        split = col.split(percentage=0.5, align=True)

        col1 = split.column()

        for name in ['color_viz', 'color_tex', 'color_sce']:
            r = col1.row()
            r.prop(self, name)
        col2 = split.column()
        for name in ['color_lay', 'color_gen']:
            r = col2.row()
            r.prop(self, name)

        # debug
        col = row.column(align=True)
        col.label(text="Debug:")
        col.prop(self, "show_debug")

        col.label("Error colors")
        row1 = col.row()
        row1.prop(self, "exception_color")
        row1.prop(self, "no_data_color")

        col.prop(self, "heat_map")
        row1 = col.row()
        row1.active = self.heat_map

        row1.prop(self, "heat_map_hot")
        row1.prop(self, "heat_map_cold")

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
