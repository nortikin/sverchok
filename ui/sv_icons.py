import bpy
import os
import glob
import bpy.utils.previews

DEBUG = False


def logDebug(message, extra=""):
    if DEBUG:
        print(message, extra)

# custom icons dictionary
_icon_collection = {}


def custom_icon(name):
    logDebug("custom_icon called: ", name)

    load_custom_icons()  # load in case they custom icons not already loaded

    custom_icons = _icon_collection["main"]

    if name in custom_icons:
        return custom_icons[name].icon_id
    else:
        logDebug("No custom icon found for name: ", name)
        return 0


def load_custom_icons():
    logDebug("load_custom_icons called")

    if len(_icon_collection):  # return if custom icons already loaded
        return

    custom_icons = bpy.utils.previews.new()

    iconsDir = os.path.join(os.path.dirname(__file__), "icons")
    iconPattern = "sv_*.png"
    iconPath = os.path.join(iconsDir, iconPattern)
    iconFiles = [os.path.basename(x) for x in glob.glob(iconPath)]
    logDebug(iconFiles)

    for iconFile in iconFiles:
        iconName = os.path.splitext(iconFile)[0]
        iconID = iconName.upper()
        logDebug(iconID)
        custom_icons.load(iconID, os.path.join(iconsDir, iconFile), "IMAGE")

    _icon_collection["main"] = custom_icons


def remove_custom_icons():
    logDebug("remove_custom_icons called")
    bpy.utils.previews.remove(custom_icons)


def register():
    logDebug("Registering SV custom icons")
    load_custom_icons()


def unregister():
    logDebug("Unregistering SV custom icons")
    remove_custom_icons()

if __name__ == '__main__':
    register()
