import bpy
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, FloatVectorProperty, EnumProperty

from sverchok import data_structure
from sverchok.core import handlers
from sverchok.utils import sv_panels_tools
from sverchok.utils import color_def

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

    
    auto_apply_theme = BoolProperty(
        name="Apply theme", description="Apply theme automaticlly",
        default=False)
        

    sv_color_viz = FloatVectorProperty(
        name="Viz", description='',
        size=3, min=0.0, max=1.0,
        default=(1, 0.3, 0), subtype='COLOR',
        update=update_theme)

    sv_color_tex = FloatVectorProperty(
        name="Tex", description='',
        size=3, min=0.0, max=1.0,
        default=(0.5, 0.5, 1), subtype='COLOR',
        update=update_theme)
    
    sv_color_sce = FloatVectorProperty(
        name="Sce", description='',
        size=3, min=0.0, max=1.0,
        default=(0, 0.5, 0.2), subtype='COLOR',
        update=update_theme)

    sv_color_lay = FloatVectorProperty(
        name="Lay", description='',
        size=3, min=0.0, max=1.0,
        default=(0.674, 0.242, 0.363), subtype='COLOR',
        update=update_theme)

    sv_color_gen = FloatVectorProperty(
        name="Gen", description='',
        size=3, min=0.0, max=1.0,
        default=(0,0.5,0.5), subtype='COLOR',
        update=update_theme)

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
        name="Show icons",
        default=False,
        description="Use icons in ctrl+space menu")

    scene_update = BoolProperty(
        name="Scene update handler",
        default=False,
        description="Update sverchok on scene changes. Warning can be slow!",
        update=set_frame_change)


    def draw(self, context):
        layout = self.layout
        row = layout.split(percentage=0.33)
        
        col = row.column(align=True)
        col.label(text="General:")
        col.label(text="Frame change handler:")
        row1 = col.row()
        row1.prop(self, "frame_change_mode", expand=True)
        col.prop(self, "show_icons")
        col.separator()
        col.label(text='Sverchok Node Theme:')
        split = col.split(percentage=0.20, align=True)
        split.prop(self, 'sv_color_viz')
        split.prop(self, 'sv_color_tex')
        split.prop(self, 'sv_color_sce')
        split.prop(self, 'sv_color_lay')
        split.prop(self, 'sv_color_gen')
        row2 = col.row()
        row2.prop(self, 'auto_apply_theme')
        row2.operator('node.sverchok_apply_theme')
        
        col = row.column(align=True)
        col.label(text="Debug:")
        col.prop(self, "show_debug")

        col.prop(self, "heat_map")
        col1 = col.split(percentage=0.5, align=True)
        col1.active = self.heat_map
        col1.prop(self, "heat_map_hot")
        col1.prop(self, "heat_map_cold")

        col = row.column(align=True)
        col.label(text="Misc:")
        col1 = col.column(align=True)
        col1.scale_y=2.0
        col1.operator('wm.url_open', text='Home!').url = 'http://nikitron.cc.ua/blend_scripts.html'
        if context.scene.sv_new_version:
            col1.operator('node.sverchok_update_addon', text='Upgrade Sverchok addon')
        else:
            col1.operator('node.sverchok_check_for_upgrades', text='Check for new version')


def register():
    bpy.utils.register_class(SverchokPreferences)


def unregister():
    bpy.utils.unregister_class(SverchokPreferences)

if __name__ == '__main__':
    register()
