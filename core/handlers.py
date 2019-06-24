import traceback

import bpy
from bpy.app.handlers import persistent

from sverchok import old_nodes
from sverchok import data_structure
from sverchok.core import upgrade_nodes, upgrade_group
from sverchok.utils.context_managers import hard_freeze
from sverchok.core.update_system import process_from_node

from sverchok.ui import (
    viewer_draw,
    viewer_draw_mk2,
    index_viewer_draw,
    nodeview_bgl_viewer_draw,
    nodeview_bgl_viewer_draw_mk2,
    bgl_callback_3dview,
    color_def
)

objects_nodes_set = {'ObjectsNode', 'ObjectsNodeMK2', 'SvObjectsNodeMK3'}
_state = {'frame': None}

def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            yield ng


def has_frame_changed(scene):
    last_frame = _state['frame']
    _state['frame'] = scene.frame_current
    return not last_frame == scene.frame_current


@persistent
def sv_update_handler(scene):
    """
    Update sverchok node groups on frame change events.
    """
    if not has_frame_changed(scene):
        return
    
    for ng in sverchok_trees():
        try:
            # print('sv_update_handler')
            ng.process_ani()
        except Exception as e:
            print('Failed to update:', str(e)) #name,

    scene.update()


@persistent
def sv_scene_handler(scene):
    """
    Avoid using this.
    Update sverchok node groups on scene update events.
    Not used yet.
    """
    # print('sv_scene_handler')
    for ng in sverchok_trees():
        try:
            ng.process_ani()
        except Exception as e:
            print('Failed to update:', ng, str(e))


@persistent
def sv_main_handler(scene):
    """
    Main Sverchok handler for updating node tree upon editor changes
    """
    for ng in sverchok_trees():
        # print("Scene handler looking at tree {}".format(ng.name))
        if ng.has_changed:
            # print('sv_main_handler')
            # print("Edit detected in {}".format(ng.name))
            ng.process()


@persistent
def sv_object_live_update(scene):
    # This handler is created especially for objects in nodes. When live updated is enabled in 3d panel this handler
    # detects user changes of objects and call process of appropriate objects in node.
    if not scene.SvShowIn3D_active:
        return

    obj_nodes = []
    for ng in bpy.data.node_groups:
        # search of objects in nodes
        if ng.bl_idname == 'SverchCustomTreeType':
            if ng.sv_process:
                nodes = []
                for n in ng.nodes:
                    if n.bl_idname in objects_nodes_set:
                        nodes.append(n)
                if nodes:
                    obj_nodes.append(nodes)

    for nodes in obj_nodes:
        # Nodes of current node tree
        for node in nodes:
            for i in node.object_names:
                # object_names is collections of names of objects of SvObjectsNodeMK3
                try:
                    obj = bpy.data.objects[i.name]
                except KeyError:
                    continue
                if obj.is_updated or obj.is_updated_data or obj.data.is_updated:
                    # check changes of object
                    with hard_freeze(node):
                        # freeze node tree for avoiding updating whole nodes of the tree
                        # print('calling process on:', node.name, node.id_data)
                        process_from_node(node)
                    # calling process_from_node switch node tree condition to has changed, that is not true
                    node.id_data.has_changed = False

@persistent
def sv_clean(scene):
    """
    Cleanup callbacks, clean dicts.
    """
    viewer_draw.callback_disable_all()
    viewer_draw_mk2.callback_disable_all()
    index_viewer_draw.callback_disable_all()
    nodeview_bgl_viewer_draw.callback_disable_all()
    nodeview_bgl_viewer_draw_mk2.callback_disable_all()
    bgl_callback_3dview.callback_disable_all()

    data_structure.sv_Vars = {}
    data_structure.temp_handle = {}


@persistent
def sv_post_load(scene):
    """
    Upgrade nodes, apply preferences and do an update.
    """

    for monad in (ng for ng in bpy.data.node_groups if ng.bl_idname == 'SverchGroupTreeType'):
        if monad.input_node and monad.output_node:
            monad.update_cls()
        else:
            upgrade_group.upgrade_group(monad)

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
    bpy.app.handlers.scene_update_pre.append(sv_main_handler)
    bpy.app.handlers.scene_update_post.append(sv_object_live_update)
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
    bpy.app.handlers.scene_update_pre.remove(sv_main_handler)
    bpy.app.handlers.scene_update_post.remove(sv_object_live_update)
    set_frame_change(None)
