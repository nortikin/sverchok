import traceback

import bpy
from bpy.app.handlers import persistent

from sverchok import old_nodes
from sverchok import data_structure
from sverchok.core import upgrade_nodes, undo_handler_node_count
from sverchok.core.update_system import (
    set_first_run, clear_system_cache, reset_timing_graphs)
from sverchok.ui import bgl_callback_nodeview, bgl_callback_3dview
from sverchok.utils import app_handler_ops
from sverchok.utils.logging import debug
from sverchok.utils import dummy_nodes

_state = {'frame': None}

pre_running = False
sv_depsgraph = []
depsgraph_need = False

def get_sv_depsgraph():
    global sv_depsgraph
    global depsgraph_need

    if not depsgraph_need:
        sv_depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph_need = True
    elif not sv_depsgraph:
        sv_depsgraph = bpy.context.evaluated_depsgraph_get()

    return sv_depsgraph

def set_sv_depsgraph_need(val):
    global depsgraph_need
    depsgraph_need = val

def update_all_monads_found():
    for monad in (ng for ng in bpy.data.node_groups if ng.bl_idname == 'SverchGroupTreeType'):
        if monad.input_node and monad.output_node:
            monad.update_cls()    

def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            yield ng

def get_all_sverchok_affiliated_trees():
    sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType', 'SvGroupTree'}
    return list(ng for ng in bpy.data.node_groups if ng.bl_idname in sv_types and ng.nodes)    

def has_frame_changed(scene):
    last_frame = _state['frame']
    _state['frame'] = scene.frame_current
    return not last_frame == scene.frame_current

#
#  app.handlers.undo_post and app.handlers.undo_pre are necessary to help remove stale
#  draw callbacks (bgl / gpu / blf). F.ex the rightlick menu item "attache viewer draw"
#  will invoke a number of commands as one event, if you undo that event (ctrl+z) then
#  there is never a point where the node can ask "am i connected to anything, do i need
#  to stop drawing?". When the Undo event causes a node to be removed, its node.free function
#  is not called. (maybe it should be...)
#
#  If at any time the undo system is fixed and does call "node.free()" when a node is removed
#  after ctrl+z. then these two functions and handlers are no longer needed.

@persistent
def sv_handler_undo_pre(scene):
    from sverchok.core import undo_handler_node_count

    for ng in sverchok_trees():
        undo_handler_node_count['sv_groups'] += len(ng.nodes)


@persistent
def sv_handler_undo_post(scene):
    # this function appears to be hoisted into an environment that does not have the same locals()
    # hence this dict must be imported. (jan 2019)

    from sverchok.core import undo_handler_node_count

    num_to_test_against = 0
    links_changed = False
    for ng in sverchok_trees():
        num_to_test_against += len(ng.nodes)
        ng.sv_links.create_new_links(ng)
        links_changed = ng.sv_links.links_have_changed(ng)
        if links_changed:
            break

    if links_changed or not (undo_handler_node_count['sv_groups'] == num_to_test_against):
        print('looks like a node was removed, cleaning')
        sv_clean(scene)
        for ng in sverchok_trees():
            ng.nodes_dict.load_nodes(ng)
            ng.has_changed = True
        sv_main_handler(scene)

    undo_handler_node_count['sv_groups'] = 0

    import sverchok.core.group_handlers as gh
    gh.ContextTrees.reset_data()



@persistent
def sv_update_handler(scene):
    """
    Update sverchok node groups on frame change events.
    """
    if not has_frame_changed(scene):
        return

    reset_timing_graphs()

    for ng in sverchok_trees():
        try:
            # print('sv_update_handler')
            ng.process_ani()
        except Exception as e:
            print('Failed to update:', str(e))  # name,


@persistent
def sv_main_handler(scene):
    """
    On depsgraph update (pre)
    """
    global pre_running
    global sv_depsgraph
    global depsgraph_need

    # when this handler is called from inside another call to this handler we end early
    # to avoid stack overflow.
    if pre_running:
        return

    pre_running = True
    if depsgraph_need:
        sv_depsgraph = bpy.context.evaluated_depsgraph_get()

    pre_running = False


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
def sv_pre_load(scene):
    clear_system_cache()
    sv_clean(scene)

    import sverchok.core.group_handlers as gh
    gh.NodesStatuses.reset_data()
    gh.ContextTrees.reset_data()

    set_first_run(True)


@persistent
def sv_post_load(scene):
    """
    Upgrade nodes, apply preferences and do an update.
    """

    set_first_run(False)
    from sverchok import node_tree, settings
    
    # ensure current nodeview view scale / location parameters reflect users' system settings
    node_tree.SverchCustomTree.update_gl_scale_info(None, "sv_post_load")

    update_all_monads_found()
    sv_trees = get_all_sverchok_affiliated_trees()

    for ng in sv_trees:
        with ng.throttle_update():
            try:
                old_nodes.load_old(ng)
            except:
                traceback.print_exc()
            try:
                dummy_nodes.load_dummy(ng)
            except:
                traceback.print_exc()
            try:
                upgrade_nodes.upgrade_nodes(ng)
            except:
                traceback.print_exc()

    settings.apply_theme_if_necessary()

    for ng in sv_trees:
        if ng.bl_idname == 'SverchCustomTreeType' and ng.nodes:
            ng.update()


def set_frame_change(mode):
    post = bpy.app.handlers.frame_change_post
    pre = bpy.app.handlers.frame_change_pre

    # remove all
    if sv_update_handler in post:
        post.remove(sv_update_handler)
    if sv_update_handler in pre:
        pre.remove(sv_update_handler)

    # apply the right one
    if mode == "POST":
        post.append(sv_update_handler)
    elif mode == "PRE":
        pre.append(sv_update_handler)


handler_dict = {
    'undo_pre': sv_handler_undo_pre,
    'undo_post': sv_handler_undo_post,
    'load_pre': sv_pre_load,
    'load_post': sv_post_load,
    'depsgraph_update_pre': sv_main_handler
}


@persistent
def call_user_functions_on_post_load_event(scene):
    for function in data_structure.post_load_call.registered_functions:
        function()


def register():

    app_handler_ops(append=handler_dict)

    data_structure.setup_init()
    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        set_frame_change(addon.preferences.frame_change_mode)
    else:
        print("Couldn't setup Sverchok frame change handler")

    bpy.app.handlers.load_post.append(call_user_functions_on_post_load_event)


def unregister():
    app_handler_ops(remove=handler_dict)
    set_frame_change(None)
    bpy.app.handlers.load_post.remove(call_user_functions_on_post_load_event)
