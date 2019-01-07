import traceback

import bpy
from bpy.app.handlers import persistent

from sverchok import old_nodes
from sverchok import data_structure
from sverchok.core import upgrade_nodes, upgrade_group

from sverchok.ui import color_def, bgl_callback_nodeview, bgl_callback_3dview
from sverchok.utils import app_handler_ops


_state = {'frame': None}
_nodegroup_tracking = {'groups': 0}

def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            yield ng


def has_frame_changed(scene):
    last_frame = _state['frame']
    _state['frame'] = scene.frame_current
    return not last_frame == scene.frame_current

#
#
#  undo_post and undo_pre app.handlers exist in this preliminary form to
#  handle when a user invokes a scripted placement of a node which places
#  a node and hooks it up while freezing the nodetree prevents intermediate updates
#  The reason this specifically needs to be handled in the undo event is because
#  if the user presses ctrl+z to the point where it removes a node that's drawing
#  the node's own "free" function is not called by the undo system. ( i'll argue it should, 
#  and that that is a blender bug) . So because free is not called, the callback isn't 
#  removed from the draw handlers. Rather than moaning about it, this tracks the total
#  node count over the trees and only performs a clean if that changes.
#
#  If at any time the undo system is fixed and does call "node.free()" when a node is removed
#  after ctrl+z. then these two functions and handlers are no longer needed.

@persistent
def sv_handler_undo_pre(scene):
    for ng in sverchok_trees():
        _nodegroup_tracking['groups'] += len(ng.nodes)

@persistent
def sv_handler_undo_post(scene):
    num_to_test_against = 0
    for ng in sverchok_trees():
        num_to_test_against += len(ng.nodes)

    # only perform clean if the undo event triggered
    # a difference in total node count among trees.
    if not (_nodegroup_tracking['groups'] == num_to_test_against):
        print('looks like a node was removed, cleaning')
        sv_clean(scene)
        sv_main_handler(scene)

    _nodegroup_tracking = {'groups': 0}


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
            print('depsgraph_update_pre called - ng.has_changed -> ')
            # print('sv_main_handler')
            # print("Edit detected in {}".format(ng.name))
            ng.process()


@persistent
def sv_clean(scene):
    """
    Cleanup callbacks, clean dicts.
    """
    bgl_callback_nodeview.callback_disable_all()
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
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        pref = addon.preferences
        if pref.apply_theme_on_open:
            color_def.apply_theme()

    for ng in sv_trees:
        if ng.bl_idname == 'SverchCustomTreeType' and ng.nodes:
            ng.update()


def set_frame_change(mode):
    post = bpy.app.handlers.frame_change_post
    pre = bpy.app.handlers.frame_change_pre

    # scene = bpy.app.handlers.scene_update_post
    # remove all
    if sv_update_handler in post:
        post.remove(sv_update_handler)
    if sv_update_handler in pre:
        pre.remove(sv_update_handler)
    #if sv_scene_handler in scene:
    #    scene.remove(sv_scene_handler)

    # apply the right one
    if mode == "POST":
        post.append(sv_update_handler)
    elif mode == "PRE":
        pre.append(sv_update_handler)


handler_dict = {
    'undo_pre': sv_handler_undo_pre,
    'undo_post': sv_handler_undo_post,
    'load_pre': sv_clean,
    'load_post': sv_post_load,
    'depsgraph_update_pre': sv_main_handler
}


def register():

    app_handler_ops(append=handler_dict)

    data_structure.setup_init()
    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        set_frame_change(addon.preferences.frame_change_mode)
    else:
        print("Couldn't setup Sverchok frame change handler")


def unregister():
    app_handler_ops(remove=handler_dict)
    set_frame_change(None)
