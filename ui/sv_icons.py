import bpy
import os
import glob
import bpy.utils.previews

import sverchok

# custom icons dictionary
_icon_collection = {}

class SvIconProviderRecord(object):
    def __init__(self, provider_id, provider):
        self.provider_id = provider_id
        self.provider = provider
        self.provider_inited = False

    def init(self, custom_icons):
        if self.provider_inited:
            return
        for icon_id, path in self.provider.get_icons():
            try:
                custom_icons.load(icon_id, path, "IMAGE")
            except KeyError:
                pass

_icon_providers = dict()

addon_name = sverchok.__name__

def register_custom_icon_provider(provider_id, provider):
    global _icon_providers
    # make sure that _icon_collection["main"] is initialized
    load_custom_icons()
    record = SvIconProviderRecord(provider_id, provider)
    _icon_providers[provider_id] = record
    custom_icons = _icon_collection["main"]
    record.init(custom_icons)

def custom_icon(name):
    load_custom_icons()  # load in case they custom icons not already loaded

    custom_icons = _icon_collection["main"]

    default = lambda: None  # for no icon with given name will return zero
    default.icon_id = 0

    return custom_icons.get(name, default).icon_id


def load_custom_icons():
    if len(_icon_collection):  # return if custom icons already loaded
        #print("Icons were already loaded?")
        return

    custom_icons = bpy.utils.previews.new()

    iconsDir = os.path.join(os.path.dirname(__file__), "icons")
    iconPattern = "sv_*.png"
    iconPath = os.path.join(iconsDir, iconPattern)
    iconFiles = [os.path.basename(x) for x in glob.glob(iconPath)]

    for iconFile in iconFiles:
        iconName = os.path.splitext(iconFile)[0]
        iconID = iconName.upper()
        preview = custom_icons.load(iconID, os.path.join(iconsDir, iconFile), "IMAGE")

        # there is a problem of loading images (at least in Blender 3.3.1 on Windows)
        # some images for some reason are not displayed in UI, though ImagePreviews
        # return some icon_id. Such problem can be detected by checking the
        # icon_pixels, but iterating over them right after registration of a preview
        # demolish the problem, but it has big impact on add-on loading performance
        # father investigations: icons are not loaded only in add node menu
        # probably because icons are switched to rapidly and Blender can't manage
        # to load them and memorize if they were loaded.
        # any(preview.icon_pixels)
        # print(f"{iconID} => {any(preview.icon_pixels)}")

    for provider in _icon_providers.values():
        provider.init(custom_icons)

    _icon_collection["main"] = custom_icons


def remove_custom_icons():
    for custom_icons in _icon_collection.values():
        bpy.utils.previews.remove(custom_icons)
    _icon_collection.clear()

def get_icon_switch():
    """Return show_icons setting from addon preferences"""

    addon = bpy.context.preferences.addons.get(addon_name)

    if addon and hasattr(addon, "preferences"):
        return addon.preferences.show_icons


def icon(display_icon):
    '''returns empty dict if show_icons is False, else the icon passed'''
    kws = {}
    if display_icon.startswith('SV_'):
        kws = {'icon_value': custom_icon(display_icon)}
    else:
        kws = {'icon': display_icon}
    return kws


def node_icon(node_ref):
    """Returns empty dict if show_icons is False, else the icon passed."""
    if ic := getattr(node_ref, 'sv_icon', None):
        iconID = custom_icon(ic)
        return {'icon_value': iconID} if iconID else {}
    elif hasattr(node_ref, 'bl_icon'):
        iconID = node_ref.bl_icon
        return {'icon': iconID} if iconID else {}
    else:
        return {}


class ShowSvIconsOp(bpy.types.Operator):
    """Just shows list of all custom icons used in Sverchok. Open via F3 search"""
    bl_idname = "node.show_sv_icons"
    bl_label = "Sverchok Icons List"

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=600)

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(row_major=True, align=True, columns=30)
        for ic in _icon_collection['main'].values():
            grid.label(text='', icon_value=ic.icon_id)


def register():
    load_custom_icons()
    bpy.utils.register_class(ShowSvIconsOp)


def unregister():
    remove_custom_icons()
    bpy.utils.unregister_class(ShowSvIconsOp)
