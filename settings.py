import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty, IntProperty, FloatProperty

from sverchok import data_structure
from sverchok.core import handlers
from sverchok.core import update_system
from sverchok.utils import sv_panels_tools
from sverchok.ui import color_def
from sverchok.ui.sv_icons import custom_icon

tab_items = [
    ("GENERAL", "General", "General settings", custom_icon("SV_PREFS_GENERAL"), 0),
    ("THEMES", "Themes", "Update nodes theme colors", custom_icon("SV_PREFS_THEMES"), 1),
    ("DEFAULTS", "Defaults", "Various node default values", custom_icon("SV_PREFS_DEVELOPER"), 2),
]


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

    def update_defaults(self, context):
        print("Update Defaults")

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

    color_genx = FloatVectorProperty(
        name="Generator X", description='',
        size=3, min=0.0, max=1.0,
        default=(0.4, 0.7, 0.7), subtype='COLOR',
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

    enable_icon_manager = BoolProperty(
        name="Enable Icon Manager",
        default=False,
        description="Enable SV icon manager node")

    over_sized_buttons = BoolProperty(
        name="Big buttons",
        default=False,
        description="Very big buttons")

    enable_live_objin = BoolProperty(
        description="Objects in edit mode will be updated in object-in Node")

    tabs = EnumProperty(
        name="Sections", description="Setting Sections",
        default="GENERAL", items=tab_items)

    # node default values
    color_verts = FloatVectorProperty(
        name="Verts", description='Vertex Color',
        size=3, min=0.0, max=1.0,
        default=(1.0, 1.0, 1.0), subtype='COLOR',
        update=update_defaults)

    color_edges = FloatVectorProperty(
        name="Edges", description='Edge Color',
        size=3, min=0.0, max=1.0,
        default=(0.5, 0.75, 0.9), subtype='COLOR',
        update=update_defaults)

    color_polys = FloatVectorProperty(
        name="Polys", description='Poly Color',
        size=3, min=0.0, max=1.0,
        default=(0.0, 0.5, 0.9), subtype='COLOR',
        update=update_defaults)

    vert_size = FloatProperty(
        name="Vert size", description="Vertex size",
        min=0.0, max=10.0, default=3.2)

    edge_width = FloatProperty(
        name="Edge width", description="Edge width",
        min=1.0, max=10.0, default=2.0)

    enable_center = BoolProperty(
        name="Enable Center", description="Enable Center",
        default=False)

    def split_columns(self, panel, sizes):
        # normalize sizes
        col2 = panel
        cols = []
        print("")
        print("sizes = ", sizes)
        for n in range(len(sizes)):
            n1 = sizes[n]
            n2 = sum(sizes[n + 1:])
            p = n1 / (n1 + n2)
            print("n = ", n, " n1 = ", n1, " n2 = ", n2)
            print("ratio ", n, " = ", p)
            split = col2.split(percentage=p, align=True)
            col1 = split.column()
            col2 = split.column()
            cols.append(col1)
        return cols

    def draw_general_tab_ui(self, tab):
        # print("Draw the GENERAL tab UI")
        cols = self.split_columns(tab, [1, 1, 1])

        col = cols[0]

        col.label(text="Debug:")
        box = col.box()
        box.prop(self, "show_debug")
        box.prop(self, "enable_live_objin", text='Enable Live Object-In')
        box.prop(self, "heat_map", text="Heat Map")

        col = cols[1]

        col.label(text="Frame change handler:")
        box = col.box()
        row = box.row()
        row.prop(self, "frame_change_mode", expand=True)

    def draw_theme_tab_ui(self, tab):
        # print("Draw the THEME tab UI")
        colA, colB = self.split_columns(tab, [1, 2])

        # colA.label(text="")
        colA.label(text="Theme update settings:")
        box = colA.box()
        box.prop(self, 'auto_apply_theme', text="Auto apply theme changes")
        box.prop(self, 'apply_theme_on_open', text="Apply theme when opening file")
        box.separator()
        box.operator('node.sverchok_apply_theme', text="Apply theme to layouts")

        colA.label(text="UI settings:")
        box = colA.box()
        box.prop(self, "show_icons")
        box.prop(self, "over_sized_buttons")
        box.prop(self, "enable_icon_manager")

        colB.prop(self, 'sv_theme')

        colB1, colB2 = self.split_columns(colB, [1, 1])

        colB1.label("Nodes Colors:")
        box = colB1.box()
        for name in ['color_viz', 'color_tex', 'color_sce', 'color_lay', 'color_gen', 'color_genx']:
            row = box.row()
            row.prop(self, name)

        colB2.label("Error Colors:")
        box = colB2.box()
        for name in ['exception_color', 'no_data_color']:
            row = box.row()
            row.prop(self, name)

        colB2.label("Heat Map Colors:")
        box = colB2.box()
        box.active = self.heat_map
        for name in ['heat_map_hot', 'heat_map_cold']:
            row = box.row()
            row.prop(self, name)

    def draw_defaults_tab_ui(self, tab):
        # print("Draw the DEFAULTS tab UI")
        cols = self.split_columns(tab, [1, 1, 1, 1])

        col = cols[0]
        col.label(text="Viewer Colors:")
        box = col.box()
        for name in ['color_verts', 'color_edges', 'color_polys']:
            row = box.row()
            row.prop(self, name)

        col = cols[1]
        col.label(text="Viewer Sizes:")
        box = col.box()
        for name in ['vert_size', 'edge_width']:
            row = box.row()
            row.prop(self, name)

        col = cols[2]
        col.label(text="Enable:")
        box = col.box()
        box.prop(self, "enable_center")

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "tabs", expand=True)
        row.scale_y = 1.5
        row = col.row(align=True)

        if self.tabs == "THEMES":
            self.draw_theme_tab_ui(row)

        elif self.tabs == "GENERAL":
            self.draw_general_tab_ui(row)

        elif self.tabs == "DEFAULTS":
            self.draw_defaults_tab_ui(row)

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
