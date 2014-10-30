import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty

import data_structure
from core import handlers
from utils import sv_panels_tools
SVERCHOK_NAME = __package__


# the way this works is backwards and should be redone
class SverchokPreferences(AddonPreferences):

    bl_idname = __package__

    def update_debug_mode(self, context):
        #print(dir(context))
        data_structure.DEBUG_MODE = self.show_debug

    def update_heat_map(self, context):
        data_structure.heat_map_state(self.heat_map)

    def set_frame_change(self, context):
        handlers.set_frame_change(self.frame_change_mode)

    show_debug = BoolProperty(
        name="Print update timings",
        description="Print update timings in console",
        default=False, subtype='NONE',
        update=update_debug_mode)

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

    show_icons = BoolProperty(
        name="show_icons",
        default=False,
        description="Use icons in menu")

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        col.label(text="General")
        col.label(text="Frame change handler:")
        row = col.row()
        row.prop(self, "frame_change_mode", expand=True)
        col.separator()
        col.label(text="Debug")
        col.prop(self, "show_debug")
        col.prop(self, "heat_map")
        col.prop(self, "show_icons")
        row = col.row()
        row.active = self.heat_map
        row.prop(self, "heat_map_hot")
        row.prop(self, "heat_map_cold")

        col.separator()
        row = layout.row()
        row.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        if sv_panels_tools.sv_new_version:
            row.operator('node.sverchok_update_addon', text='Upgrade Sverchok addon')
        else:
            row.operator('node.sverchok_check_for_upgrades', text='Check for new version')


def register():
    bpy.utils.register_class(SverchokPreferences)


def unregister():
    bpy.utils.unregister_class(SverchokPreferences)
