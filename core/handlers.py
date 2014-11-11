import traceback

import bpy
from bpy.app.handlers import persistent

from sverchok import data_structure
from sverchok.core import upgrade_nodes
from sverchok.ui import (viewer_draw, viewer_draw_mk2, index_viewer_draw,
                         nodeview_bgl_viewer_draw, color_def)
from sverchok import old_nodes


@persistent
def sv_update_handler(scene):
    """
    Update sverchok node groups on frame change events.
    """
    for name, tree in bpy.data.node_groups.items():
        if tree.bl_idname == 'SverchCustomTreeType' and tree.nodes:
            try:
                tree.update_ani()
            except Exception as e:
                print('Failed to update:', name, str(e))
    scene.update()


@persistent
def sv_scene_handler(scene):
    """
    Avoid using this.
    Update sverchok node groups on scene update events.
    Not used yet.
    """
    for name, tree in bpy.data.node_groups.items():
        if tree.bl_idname == 'SverchCustomTreeType' and tree.nodes:
            try:
                tree.update_ani()
            except Exception as e:
                print('Failed to update:', name, str(e))


@persistent
def sv_clean(scene):
    """
    Cleanup callbacks, clean dicts.
    """
    viewer_draw.callback_disable_all()
    viewer_draw_mk2.callback_disable_all()
    index_viewer_draw.callback_disable_all()
    nodeview_bgl_viewer_draw.callback_disable_all()
    data_structure.sv_Vars = {}
    data_structure.temp_handle = {}


@persistent
def sv_post_load(scene):
    """
    Upgrade nodes, apply preferences and do an update.
    """
    sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
    sv_trees = list(ng for ng in bpy.data.node_groups if ng.bl_idname in sv_types and ng.nodes)
    for ng in sv_trees:
        ng.freeze(True)
        try:
            old_nodes.load_old(ng)
        except:
            traceback.print_exc()
        ng.freeze(True)
        try:
            upgrade_nodes.upgrade_nodes(ng)
        except:
            traceback.print_exc()
        ng.unfreeze(True)

    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.user_preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        pref = addon.preferences
        if pref.apply_theme_on_open:
            color_def.apply_theme()
    '''
    unsafe_nodes = {
        'SvScriptNode',
        'FormulaNode',
        'Formula2Node',
        'EvalKnievalNode',
    }

    unsafe = False
    for tree in sv_trees:
        if any((n.bl_idname in unsafe_nodes for n in tree.nodes)):
            unsafe = True
            break
    # do nothing with this for now
    #if unsafe:
    #    print("unsafe nodes found")
    #else:
    #    print("safe")

    #print("post load .update()")
    # do an update
    '''
    for ng in sv_trees:
        if ng.bl_idname == 'SverchCustomTreeType' and ng.nodes:
            ng.update()


def set_frame_change(mode):
    post = bpy.app.handlers.frame_change_post
    pre = bpy.app.handlers.frame_change_pre

    scene = bpy.app.handlers.scene_update_post
    # remove all
    if sv_update_handler in post:
        post.remove(sv_update_handler)
    if sv_update_handler in pre:
        pre.remove(sv_update_handler)
    if sv_scene_handler in scene:
        scene.remove(sv_scene_handler)

    # apply the right one
    if mode == "POST":
        post.append(sv_update_handler)
    elif mode == "PRE":
        pre.append(sv_update_handler)


def register():
    bpy.app.handlers.load_pre.append(sv_clean)
    bpy.app.handlers.load_post.append(sv_post_load)
    data_structure.setup_init()
    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.user_preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        set_frame_change(addon.preferences.frame_change_mode)
    else:
        print("Couldn't setup Sverchok frame change handler")


def unregister():
    bpy.app.handlers.load_pre.remove(sv_clean)
    bpy.app.handlers.load_post.remove(sv_post_load)
    set_frame_change(None)
