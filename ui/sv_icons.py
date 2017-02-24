import bpy
import os
import glob
import bpy.utils.previews

# custom icons dictionary
_icon_collection = {}


def custom_icon(name):
    load_custom_icons()  # load in case they custom icons not already loaded

    custom_icons = _icon_collection["main"]

    default = lambda: None  # for no icon with given name will return zero
    default.icon_id = 0

    return custom_icons.get(name, default).icon_id


def load_custom_icons():
    if len(_icon_collection):  # return if custom icons already loaded
        return

    custom_icons = bpy.utils.previews.new()

    iconsDir = os.path.join(os.path.dirname(__file__), "icons")
    iconPattern = "sv_*.png"
    iconPath = os.path.join(iconsDir, iconPattern)
    iconFiles = [os.path.basename(x) for x in glob.glob(iconPath)]

    for iconFile in iconFiles:
        iconName = os.path.splitext(iconFile)[0]
        iconID = iconName.upper()
        custom_icons.load(iconID, os.path.join(iconsDir, iconFile), "IMAGE")

    _icon_collection["main"] = custom_icons


def remove_custom_icons():
    for custom_icons in _icon_collection.values():
        bpy.utils.previews.remove(custom_icons)
    _icon_collection.clear()


def register():
    load_custom_icons()


def unregister():
    remove_custom_icons()

if __name__ == '__main__':
    register()
