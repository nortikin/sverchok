import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty, FloatProperty, StringProperty

from sverchok import data_structure
from sverchok.core import handlers
from sverchok.core import update_system
from sverchok.ui.sv_icons import custom_icon
from sverchok.ui import sv_themes

tab_items = [
    ("GENERAL", "General", "General settings", custom_icon("SV_PREFS_GENERAL"), 0),
    ("THEMES", "Themes", "Update nodes theme colors", custom_icon("SV_PREFS_THEMES"), 1)
]


DEBUG = False


def debugPrint(*args):
    if DEBUG:
        print(*args)


def make_color_prop(name, update_callback):
    ''' Color Property Factory '''
    params = dict(name=name, description=name + " node color",
                  size=3, min=0.0, max=1.0, default=(1.0, 1.0, 1.0),
                  subtype="COLOR", update=update_callback)
    # add type specific parameters
    return getattr(bpy.props, "FloatVectorProperty")(**params)


class SverchokPreferences(AddonPreferences):
    """
    Handle Sverchock Preferences
    """
    bl_idname = __package__

    def select_theme(self, context):
        debugPrint("selecting theme: ", self.theme_preset)
        sv_themes.set_current_themeID(self.theme_preset)
        sv_themes.update_prefs_colors()
        if self.auto_apply_theme:
            sv_themes.apply_theme()
        colors_changed = False

    def update_debug_mode(self, context):
        data_structure.DEBUG_MODE = self.show_debug

    def set_frame_change(self, context):
        handlers.set_frame_change(self.frame_change_mode)

    def update_node_color(self, context):
        debugPrint("Updating node color")
        colors_changed = True
        if self.auto_apply_theme:
            sv_themes.apply_theme()
        update_system.update_error_colors(self, context)
        data_structure.heat_map_state(self.heat_map)

    def update_heatmap(self, context):
        debugPrint("Updating heatmap")
        data_structure.heat_map_state(self.heat_map)

    def theme_preset_items(self, context):
        themeItems = sv_themes.get_theme_preset_list()
        return themeItems

    colors_changed = BoolProperty(default=False)

    #  debugish...
    show_debug = BoolProperty(
        name="Print update timings",
        description="Print update timings in console",
        default=False, subtype='NONE',
        update=update_debug_mode)

    #  heat map settings
    heat_map = BoolProperty(
        name="Heat map", description="Color nodes according to processing time",
        default=False, subtype='NONE',
        update=update_heatmap)

    #  theme settings
    theme_preset = EnumProperty(
        items=theme_preset_items,
        name="Theme preset", description="Select a theme preset",
        update=select_theme)

    auto_apply_theme = BoolProperty(
        name="Apply theme", description="Apply theme automatically",
        default=False)

    apply_theme_on_open = BoolProperty(
        name="Apply theme", description="Apply theme automatically on open",
        default=False)

    #  frame change
    frame_change_modes = [
        ("PRE", "Pre", "Update Sverchok before frame change", 0),
        ("POST", "Post", "Update Sverchok after frame change", 1),
        ("NONE", "None", "Sverchok doesn't update on frame change", 2)
    ]

    frame_change_mode = EnumProperty(
        items=frame_change_modes,
        name="Frame change", description="Select frame change handler",
        default="POST",
        update=set_frame_change)

    #  ctrl+space settings

    show_icons = BoolProperty(
        name="Show icons in ctrl+space menu",
        default=False,
        description="Use icons in ctrl+space menu")

    enable_icon_manager = BoolProperty(
        name="Enable Icon Manager",
        default=False,
        description="Enable SV icon manager node")

    over_sized_buttons = BoolProperty(
        name="Big buttons", description="Very big buttons",
        default=False)

    enable_live_objin = BoolProperty(
        name="Enable Live Object-In",
        description="Objects in edit mode will be updated in object-in Node")

    tabs = EnumProperty(
        name="Sections", description="Setting Sections",
        default="GENERAL", items=tab_items)

    enable_center = BoolProperty(
        name="Centering ON", description="Set centering to ON in various nodes",
        default=False)

    # create COLOR props for the theme colors
    for group, categories in sv_themes.theme_color_attrs().items():
        for category, attr in categories.items():
            vars()[attr] = make_color_prop(category, update_node_color)

    def split_columns(self, panel, ratios):
        """
        Splits the given panel into columns based on the given set of ratios.
        e.g ratios = [1, 2, 1] or [.2, .3, .2] etc
        Note: The sum of all ratio numbers doesn't need to be normalized
        """
        col2 = panel
        cols = []
        for n in range(len(ratios)):
            n1 = ratios[n]  # size of the current column
            n2 = sum(ratios[n + 1:])  # size of all remaining columns
            p = n1 / (n1 + n2)  # percentage split of current vs remaming columns
            split = col2.split(percentage=p, align=True)
            col1 = split.column()
            col2 = split.column()
            cols.append(col1)
        return cols

    def draw_general_tab_ui(self, tab):
        # debugPrint("Draw the GENERAL tab UI")
        cols = self.split_columns(tab, [1, 1, 1])

        col = cols[0]
        col.label(text="Debug:")
        box = col.box()
        box.prop(self, "show_debug")
        box.prop(self, "enable_live_objin")
        box.prop(self, "heat_map")

        col = cols[1]
        col.label(text="Frame change handler:")
        box = col.box()
        row = box.row()
        row.prop(self, "frame_change_mode", expand=True)

        col = cols[2]
        col.label(text="Enable:")
        box = col.box()
        box.prop(self, "enable_center")

    def draw_theme_tab_ui(self, tab):
        # debugPrint("Draw the THEME tab UI")
        colA, colB = self.split_columns(tab, [1, 2])

        colA.label(text="")
        colA.label(text="Theme update settings:")
        box = colA.box()
        box.prop(self, 'auto_apply_theme', text="Auto apply theme changes")
        box.prop(self, 'apply_theme_on_open', text="Apply theme when opening file")
        box.separator()
        box.operator('node.sverchok_apply_theme2', text="Apply theme to layouts")

        colA.label(text="UI settings:")
        box = colA.box()
        box.prop(self, "show_icons")
        box.prop(self, "over_sized_buttons")
        box.prop(self, "enable_icon_manager")

        row = colB.row(align=True)
        row.prop(self, 'theme_preset')
        row.operator("node.sv_add_theme", text="", icon='ZOOMIN')
        row.operator("node.sv_remove_theme", text="", icon='ZOOMOUT')

        colB1, colB2 = self.split_columns(colB, [1, 1])

        # add UI for the theme color props (spread over two columns)
        for group, categories in sv_themes.theme_color_attrs().items():
            col = colB1 if group == sv_themes.NODE_COLORS else colB2
            col.label(group + ":")
            box = col.box()
            for category, attr in sorted(categories.items()):
                box.row().prop(self, attr)

    def draw(self, context):
        layout = self.layout

        # HEADER (tabs)
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tabs", expand=True)
        row.scale_y = 1.5
        row = col.row(align=True)

        # SETTINGS (tab content)
        if self.tabs == "THEMES":
            self.draw_theme_tab_ui(row)

        elif self.tabs == "GENERAL":
            self.draw_general_tab_ui(row)

        # FOOTER (links)
        col = layout.column(align=True)
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
