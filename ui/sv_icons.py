import bpy
import os
import glob
import bpy.utils.previews

DEBUG = False
def logDebug(message, extra=""):
    if DEBUG:
        print(message, extra)

# global variable to store icons in
_custom_icons = None

def customIcon(name):
    logDebug("customIcon called: ", name)
    global _custom_icons

    if name in _custom_icons:
        return _custom_icons[name].icon_id
    else:
        logDebug("No custom icon found for name: ", name)
        return 0

def loadCustomIcons():
    logDebug("loadIcons called")
    global _custom_icons

    _custom_icons = bpy.utils.previews.new()

    iconsDir = os.path.join(os.path.dirname(__file__), "icons")
    iconPattern = "sv_*.png"
    iconPath = os.path.join(iconsDir, iconPattern)
    iconFiles = [os.path.basename(x) for x in glob.glob(iconPath)]
    logDebug(iconFiles)

    iconIDs=[]
    for iconFile in iconFiles:
        iconName = os.path.splitext(iconFile)[0]
        iconID = iconName.upper()
        iconIDs.append(iconID)
        logDebug(iconID)
        _custom_icons.load(iconID, os.path.join(iconsDir, iconFile), "IMAGE")

def removeCustomIcons():
    logDebug("unloadIcons called")
    global _custom_icons
    bpy.utils.previews.remove(_custom_icons)

def register():
    logDebug("Registering SV custom icons")
    loadCustomIcons()

def unregister():
    logDebug("Unregistering SV custom icons")
    removeCustomIcons()

if __name__ == '__main__':
    register()

