# SPDX-License-Identifier: GPL-3.0-or-later
"""Socket-aware link-drag search for Sverchok's custom node editor.

The native link operator retains ownership of drawing, panning and connections.
A small observer opens our popup only after a drag finishes over empty space.
"""

import logging
import sys
from array import array
from collections import deque
from contextlib import contextmanager
from time import perf_counter

import bpy
import sverchok
from bpy.app.handlers import persistent
from bpy.props import (
    BoolProperty, EnumProperty, IntProperty, StringProperty,
)

from sverchok.ui.nodeview_space_menu import get_add_node_menu
from sverchok.utils.sv_link_search import (
    SearchEntry, configure_node, describe_socket, find_socket, operation_variants,
    ranked_entries, socket_available,
)


log = logging.getLogger(__name__)
_entries = []
_pending = []
_signature = None
_ready = False
_enabled = False
_keymaps = []
_sessions = {}
_generation = 0
_deferred = set()
_active_node_type = None
_active_variants = deque()
_catalogue_revision = 0
_catalogue_forced = False


def link_drag_search_enabled(context):
    """Read the saved preference on every gesture; manual search stays enabled."""
    addon = context.preferences.addons.get(sverchok.__name__)
    return bool(addon and getattr(addon.preferences, 'link_drag_search', True))


def _has_selected_outputs(tree):
    return any(socket.select for node in tree.nodes for socket in node.outputs)


def available_node_types():
    """Use the same menu registry as Sverchok's existing node search."""
    ids = set()
    menu = get_add_node_menu()
    if menu is None:
        return ()
    for category in menu.walk_categories():
        for item in category:
            name = getattr(item, 'bl_idname', '')
            if not name or name in {'NodeFrame', 'NodeReroute', 'NodeGroupInput', 'NodeGroupOutput', 'SvGroupTreeNode'}:
                continue
            cls = bpy.types.Node.bl_rna_get_subclass_py(name)
            if cls and not getattr(cls, 'missing_dependency', False):
                ids.add(name)
    # First build useful operations, then the remaining menu in stable order.
    priority = {name: i for i, name in enumerate((
        'SvScalarMathNodeMK4', 'SvVectorMathNodeMK3', 'SvLogicNodeMK2',
        'SvColorMixNode', 'SvComponentAnalyzerNode'))}
    return tuple(sorted(ids, key=lambda name: (priority.get(name, len(priority)), name)))


@contextmanager
def _index_tree():
    """Remove ALL scratch data before returning control to Blender.

    A scratch tree lives within one call only; it cannot be saved between timer
    ticks. No user tree, socket data or node process() method is used.
    """
    from sverchok.core.update_system import UpdateTree
    from sverchok.core.tasks import tasks

    groups_before = {group.as_pointer() for group in bpy.data.node_groups}
    helper = bpy.data.node_groups.get('sverchok_helper_group')
    helper_fake_user = helper.use_fake_user if helper else None
    tree = bpy.data.node_groups.new('.SV Link Search Index', 'SverchCustomTreeType')
    try:
        tree.sv_process = False
        tree.sv_animate = False
        tree.sv_show = False
        yield tree
    finally:
        # Property callbacks can add an update-model cache even when processing
        # is disabled. Remove that cache too, before releasing RNA references.
        if tree.tree_id in UpdateTree._tree_catch:
            UpdateTree.reset_tree(tree)
        # new() can emit a TreeEvent before sv_process can be disabled. Discard
        # only this probe's queued task while its RNA pointer is still valid.
        for task in tuple(tasks._todo):
            if task.tree == tree:
                tasks._todo.discard(task)
        bpy.data.node_groups.remove(tree)
        # Curve Mapper/Color Ramp can create a shared shader helper during init.
        # free() removes their helper nodes, but leaves the group/fake-user flag.
        # All this happens synchronously, so extra new groups belong to probes.
        for group in list(bpy.data.node_groups):
            if group.as_pointer() not in groups_before:
                if hasattr(group, 'tree_id') and group.tree_id in UpdateTree._tree_catch:
                    UpdateTree.reset_tree(group)
                bpy.data.node_groups.remove(group)
        if helper is not None:
            helper.use_fake_user = helper_fake_user


def _node_variants(node_type):
    with _index_tree() as tree, tree.init_tree():
        try:
            return tuple(operation_variants(tree.nodes.new(node_type)))
        finally:
            # SV_LINK_SEARCH_VARIANT_RESOURCE_CLEANUP_V4_3
            tree.nodes.clear()


def collect_node_type(node_type, variants=None):
    """Copy plain descriptions; callers can restrict this to one operation."""
    result = []
    with _index_tree() as tree, tree.init_tree():
        if variants is None:
            probe = tree.nodes.new(node_type)
            variants = tuple(operation_variants(probe))
            tree.nodes.clear()
        for settings, operation in variants:
            try:
                node = tree.nodes.new(node_type)
                configure_node(node, settings)
                from sverchok.utils.sv_link_search_extensions import remember_ports
                remember_ports(node, settings)
                for sockets in (node.inputs, node.outputs):
                    for index, socket in enumerate(sockets):
                        if socket_available(socket):
                            result.append(SearchEntry(
                                node_type, node.bl_label, operation, settings,
                                describe_socket(socket, index)))
            except Exception:
                log.warning('Link search could not index %s %s',
                            node_type, settings, exc_info=True)
            finally:
                tree.nodes.clear()
    return result


def _catalogue_allowed():
    """Disabled automatic search does no background work; explicit uses remain."""
    if not _enabled:
        return False
    if _catalogue_forced or link_drag_search_enabled(bpy.context):
        return True
    # Opening a manual search schedules its first tick before the popup is live.
    # By the time that tick runs, only a live manual popup may keep it working.
    popup = sys.modules.get('sverchok.ui.sv_link_search_popup')
    for key in getattr(popup, '_live', ()):
        session = _sessions.get(key)
        if session and not session.get('automatic', True):
            return True
    return False


def _catalogue_tick():
    global _ready, _active_node_type, _catalogue_revision, _catalogue_forced
    if not _catalogue_allowed():
        return None
    if _signature is None:
        ensure_catalogue(background=True)
    # Blender data stays on the main thread. A node's init is indivisible;
    # yield between variants instead of keeping an idle polling timer alive.
    deadline = perf_counter() + 0.008
    while _pending or _active_variants:
        if not _active_variants:
            _active_node_type = _pending.pop(0)
            try:
                _active_variants.extend(_node_variants(_active_node_type))
            except Exception:
                log.warning('Link search skipped %s', _active_node_type, exc_info=True)
        if _active_variants:
            variant = _active_variants.popleft()
            try:
                _entries.extend(collect_node_type(_active_node_type, (variant,)))
            except Exception:
                log.warning('Link search skipped %s %s',
                            _active_node_type, variant, exc_info=True)
        if not _active_variants:
            _active_node_type = None
        if perf_counter() >= deadline:
            break
    _ready = not (_pending or _active_variants)
    _catalogue_revision += 1
    if _ready:
        _catalogue_forced = False
    return 0.01 if not _ready else None


def ensure_catalogue(force=False, *, background=False):
    global _signature, _ready, _generation, _active_node_type, _catalogue_revision
    global _catalogue_forced
    if background and not _catalogue_allowed():
        return _ready
    if force:
        _catalogue_forced = True
    signature = available_node_types()
    if force or signature != _signature:
        from sverchok.utils.sv_link_search_extensions import clear_metadata
        clear_metadata()
        _generation += 1
        _signature = signature
        _ready = False
        _entries.clear()
        _pending[:] = signature
        _active_variants.clear()
        _active_node_type = None
        _catalogue_revision += 1
        # Keep enum strings alive until popups close; generations reject stale results.
    if not _pending and not _active_variants:
        _ready = True
        _catalogue_forced = False
    elif _enabled and not bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.register(_catalogue_tick, first_interval=0.05)
    return _ready


@persistent
def _file_loaded(_unused):
    global _signature, _ready, _catalogue_forced
    _signature = None
    _ready = False
    _catalogue_forced = False
    if bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.unregister(_catalogue_tick)
    if (_enabled and not bpy.app.background
            and link_drag_search_enabled(bpy.context)):
        bpy.app.timers.register(_catalogue_tick, first_interval=1.0)


def _editor_tree(context):
    space = context.space_data
    if not space or space.type != 'NODE_EDITOR':
        return None
    tree = space.edit_tree
    if tree and tree.bl_idname in {'SverchCustomTreeType', 'SvGroupTree'} and not tree.library:
        return tree
    return None


def _socket_key(socket):
    return (socket.node.name, socket.is_output, socket.identifier)


def _near_socket_column(context, x, y):
    """Reject ordinary clicks without walking every node/socket through Python.

    Bulk RNA reads use temporary buffers, not a spatial cache or graph watcher.
    The conservative hit bounds match the former per-node check exactly.
    """
    nodes = _editor_tree(context).nodes
    count = len(nodes)
    if not count:
        return False
    scale = context.preferences.system.ui_scale
    vx, vy = context.region.view2d.region_to_view(x, y)
    margin = 20 * scale
    positions = array('f', [0.0]) * (count * 2)
    dimensions = array('f', [0.0]) * (count * 2)
    widths = array('f', [0.0]) * count
    nodes.foreach_get('location_absolute', positions)
    nodes.foreach_get('dimensions', dimensions)
    nodes.foreach_get('width', widths)
    for index in range(count):
        offset = index * 2
        top = positions[offset + 1] * scale
        if not top - max(dimensions[offset + 1], 20 * scale) - margin <= vy <= top + margin:
            continue
        left = positions[offset] * scale
        if not (abs(vx - left) <= margin
                or abs(vx - (left + widths[index] * scale)) <= margin
                or abs(vx - (left + dimensions[offset])) <= margin):
            continue
        node = nodes[index]
        if node.inputs or node.outputs:
            return True
    return False


def _pick_socket(context, x, y):
    """Use Blender's native socket hit test and preserve existing selections."""
    tree = _editor_tree(context)
    if tree is None:
        return None
    active = tree.nodes.active
    if active is not None and any(socket.select for socket in active.outputs):
        return None
    if not _near_socket_column(context, x, y):
        return None
    # Socket.select is read-only. The native probe can clear another selected
    # output; in that case defer to Blender and leave manual search available.
    if _has_selected_outputs(tree):
        return None
    nodes = list(tree.nodes)
    selected = bytearray(len(nodes))
    tree.nodes.foreach_get('select', selected)
    # Selecting never changes socket interfaces. Keep direct RNA references
    # rather than building node-name/identifier keys twice for every socket.
    before = [(socket, socket.select) for node in nodes
              for sockets in (node.inputs, node.outputs) for socket in sockets]
    try:
        bpy.ops.node.select('EXEC_DEFAULT', location=(int(x), int(y)),
                            socket_select=True, toggle=True)
        changed = [socket for socket, was_selected in before
                   if socket.select != was_selected]
        added = [socket for socket in changed if socket.select]
        picked = added[0] if len(added) == 1 else (
            changed[0] if not added and len(changed) == 1 else None)
        if picked:
            bpy.ops.node.select('EXEC_DEFAULT', location=(int(x), int(y)),
                                socket_select=True, toggle=True)
        return picked
    finally:
        # Selection can reorder nodes. Restore by identity, not collection index,
        # and avoid setting unchanged flags on thousands of unrelated nodes.
        for node, was_selected in zip(nodes, selected):
            if node.select != was_selected:
                node.select = bool(was_selected)
        tree.nodes.active = active


def _source_kwargs(socket):
    sockets = socket.node.outputs if socket.is_output else socket.node.inputs
    return dict(source_node=socket.node.name, source_identifier=socket.identifier,
                source_index=next(i for i, item in enumerate(sockets) if item == socket),
                source_output=socket.is_output)


def _resolve_source(operator, tree):
    node = tree.nodes.get(operator.source_node)
    if node is None:
        return None
    sockets = node.outputs if operator.source_output else node.inputs
    for socket in sockets:
        if socket.identifier == operator.source_identifier:
            return socket
    # Do not use a different socket if the original dynamic socket disappeared.
    return None


def _source_properties():
    return dict(
        source_node=StringProperty(options={'SKIP_SAVE'}),
        source_identifier=StringProperty(options={'SKIP_SAVE'}),
        source_index=IntProperty(default=-1, options={'SKIP_SAVE'}),
        source_output=BoolProperty(options={'SKIP_SAVE'}),
        automatic=BoolProperty(default=False, options={'SKIP_SAVE'}),
        single_link=BoolProperty(default=False, options={'SKIP_SAVE'}),
    )


def _enum_items(self, context):
    session = _sessions.get(self.session)
    return session['items'] if session else [('NONE', 'No compatible sockets', '', 0)]


class SvSocketLinkSearch(bpy.types.Operator):
    """Search compatible node operations and connect the chosen socket"""
    bl_idname = 'node.sv_socket_link_search'
    bl_label = 'Sverchok: Search and Connect'
    bl_options = {'UNDO'}
    bl_property = 'choice'
    __annotations__ = _source_properties()

    session: StringProperty(options={'SKIP_SAVE'})
    choice: EnumProperty(items=_enum_items, options={'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        return _editor_tree(context) is not None

    def invoke(self, context, event):
        from sverchok.ui.sv_link_search_popup import invoke_search
        return invoke_search(self, context, event)


    def execute(self, context):
        if self.automatic and not link_drag_search_enabled(context):
            return {'CANCELLED'}
        tree = _editor_tree(context)
        session = _sessions.get(self.session)
        if (tree is None or not session or session['generation'] != _generation
                or tree.as_pointer() != session['tree_pointer']):
            self.report({'WARNING'}, 'The tree or catalogue changed; repeat the search')
            return {'CANCELLED'}
        source = _resolve_source(self, tree)
        if source is None or (not source.is_output and source.is_linked):
            self.report({'WARNING'}, 'The source socket changed or the input is connected')
            return {'CANCELLED'}
        try:
            index = int(self.choice)
            if index < 0:
                return {'CANCELLED'}
            entry = session['results'][index]
        except (ValueError, IndexError, TypeError):
            return {'CANCELLED'}
        # The dialog is now closing. Retain only its plain descriptions for
        # undo/enum lifetime; no borrowed popup, window or area RNA survives.
        from sverchok.utils.sv_link_search_extensions import ExistingSocketEntry, connect_existing
        if isinstance(entry, ExistingSocketEntry):
            try:
                connect_existing(tree, source, entry, single_link=self.single_link)
            except Exception as error:
                self.report({'ERROR'}, 'Could not connect existing socket: ' + str(error))
                return {'CANCELLED'}
            return {'FINISHED'}
        selected = [(node, node.select) for node in tree.nodes]
        active = tree.nodes.active
        original_nodes = {node.as_pointer() for node in tree.nodes}
        try:
            # SV_LINK_SEARCH_RESOURCE_PREP_V4_3
            prepare_node_resources(entry.node_type)
            with tree.init_tree():
                from sverchok.utils.sv_link_search_extensions import create_context_node
                node = create_context_node(context, tree, entry)
                if node is None:
                    node = tree.nodes.new(entry.node_type)
                configure_node(node, entry.settings)
                target = find_socket(node, entry.socket)
                if target is None:
                    raise RuntimeError('The selected socket is no longer available')
                if not ranked_entries(describe_socket(source, self.source_index), [entry]):
                    raise RuntimeError('The source socket type changed')
                node.location = session['location']
                if not source.is_output:
                    node.location.x -= node.width
                output, input_ = (source, target) if source.is_output else (target, source)
                from sverchok.utils.sv_link_search_extensions import geometry_links
                pairs = [(output, input_)] if self.single_link else geometry_links(source, target)
                for out_socket, in_socket in pairs:
                    tree.links.new(out_socket, in_socket)
            # In particular, let List nodes adopt the type of their new input.
            if callable(getattr(node, 'update', None)):
                node.update()
            if not self.source_output:
                receiving = tree.nodes.get(self.source_node)
                if receiving is not None and callable(getattr(receiving, 'update', None)):
                    receiving.update()
            for other in tree.nodes:
                other.select = other == node
            tree.nodes.active = node
            tree.update()
        except Exception as error:
            # Also remove development frames a node may have created in init().
            with tree.init_tree():
                for added_node in list(tree.nodes):
                    if added_node.as_pointer() not in original_nodes:
                        tree.nodes.remove(added_node)
            for old_node, was_selected in selected:
                old_node.select = was_selected
            tree.nodes.active = active
            tree.update()
            self.report({'ERROR'}, 'Could not connect node: ' + str(error))
            log.exception('Link search creation failed')
            return {'CANCELLED'}
        return {'FINISHED'}


def _link_signature(socket):
    # Only links on the starting socket; no recursive graph walk.
    return frozenset((link.from_socket.as_pointer(), link.to_socket.as_pointer())
                     for link in socket.links)


def _over_empty_space(context, x, y):
    tree = _editor_tree(context)
    ui_scale = context.preferences.system.ui_scale
    vx, vy = context.region.view2d.region_to_view(x, y)
    margin = 20 * ui_scale
    for node in tree.nodes:
        if node.bl_idname == 'NodeFrame':
            continue
        location = node.location_absolute
        left, top = location.x * ui_scale, location.y * ui_scale
        width = max(node.width * ui_scale, node.dimensions.x)
        height = max(20 * ui_scale, node.dimensions.y)
        if (left - margin <= vx <= left + width + margin
                and top - height - margin <= vy <= top + margin):
            return False
    return True


class SvObserveLinkDrag(bpy.types.Operator):
    """Keep Blender's cable drag and search when it is released over empty space"""
    bl_idname = 'node.sv_observe_link_drag'
    bl_label = 'Sverchok Link Drag Search'
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return (context.region is not None and context.region.type == 'WINDOW'
                and link_drag_search_enabled(context)
                and _editor_tree(context) is not None)

    def invoke(self, context, event):
        # Start at PRESS: a nested Python invocation of node.link receives the
        # window's current event state, not the synthetic CLICK_DRAG event. At
        # CLICK_DRAG it would hit-test the moved cursor and cancel immediately.
        x, y = event.mouse_region_x, event.mouse_region_y
        try:
            source = _pick_socket(context, x, y)
        except (AttributeError, RuntimeError):
            log.debug('Native socket hit test unavailable', exc_info=True)
            return {'PASS_THROUGH'}
        if source is None or not socket_available(source):
            return {'PASS_THROUGH'}
        # Moving an existing input link remains entirely Blender's operation.
        if not source.is_output and source.is_linked:
            return {'PASS_THROUGH'}
        self._source = source
        self._links = _link_signature(source)
        self._tree = _editor_tree(context)
        self._area = context.area
        self._region = context.region
        self._window = context.window
        result = bpy.ops.node.link('INVOKE_DEFAULT')
        if 'RUNNING_MODAL' not in result:
            return {'PASS_THROUGH'}
        # Registered after native link so we see and pass through its events.
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (not _enabled or context.area != self._area
                or not link_drag_search_enabled(context)
                or _editor_tree(context) != self._tree
                or event.type in {'ESC', 'RIGHTMOUSE', 'WINDOW_DEACTIVATE'}):
            return {'FINISHED', 'PASS_THROUGH'}
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            x, y = event.mouse_region_x, event.mouse_region_y
            window, area, region = self._window, self._area, self._region
            tree, source, links = self._tree, self._source, self._links

            def after_native_link():
                _deferred.discard(after_native_link)
                if not _enabled:
                    return None
                try:
                    with bpy.context.temp_override(window=window, area=area, region=region):
                        ctx = bpy.context
                        if (link_drag_search_enabled(ctx) and _editor_tree(ctx) == tree
                                and _link_signature(source) == links
                                and _over_empty_space(ctx, x, y)):
                            ctx.space_data.cursor_location_from_region(x, y)
                            bpy.ops.node.sv_socket_link_search(
                                'INVOKE_DEFAULT', automatic=True, **_source_kwargs(source))
                except (ReferenceError, RuntimeError, AttributeError):
                    log.debug('Link search context expired', exc_info=True)
                return None

            _deferred.add(after_native_link)
            bpy.app.timers.register(after_native_link, first_interval=0.01)
            return {'FINISHED', 'PASS_THROUGH'}
        return {'PASS_THROUGH'}


class SvRebuildLinkSearch(bpy.types.Operator):
    """Rebuild node/socket descriptions, including newly installed node types"""
    bl_idname = 'node.sv_rebuild_link_search'
    bl_label = 'Sverchok: Rebuild Socket Search Catalogue'

    def execute(self, context):
        ensure_catalogue(force=True)
        self.report({'INFO'}, 'Rebuilding socket search catalogue in the background')
        return {'FINISHED'}


def _socket_menu(self, context):
    socket = getattr(context, 'socket', None)
    if _editor_tree(context) and socket and (socket.is_output or not socket.is_linked):
        self.layout.separator()
        operator = self.layout.operator(SvSocketLinkSearch.bl_idname, text='Search and Connect...')
        for key, value in _source_kwargs(socket).items():
            setattr(operator, key, value)


classes = (SvSocketLinkSearch, SvObserveLinkDrag, SvRebuildLinkSearch)


def register():
    global _enabled, _signature, _catalogue_forced
    for cls in classes:
        bpy.utils.register_class(cls)
    _enabled = True
    _signature = None
    _catalogue_forced = False
    keyconfig = bpy.context.window_manager.keyconfigs.addon
    if keyconfig:
        keymap = keyconfig.keymaps.new(name='Node Editor', space_type='NODE_EDITOR')
        item = keymap.keymap_items.new(
            SvObserveLinkDrag.bl_idname, 'LEFTMOUSE', 'PRESS', head=True)
        _keymaps.append((keymap, item))
    menu = getattr(bpy.types, 'SV_MT_SocketOptionsMenu', None)
    if menu:
        menu.append(_socket_menu)
    bpy.app.handlers.load_post.append(_file_loaded)
    if not bpy.app.background and link_drag_search_enabled(bpy.context):
        bpy.app.timers.register(_catalogue_tick, first_interval=1.0)


def unregister():
    global _enabled, _signature, _ready, _active_node_type, _catalogue_forced
    _enabled = False
    _catalogue_forced = False
    if bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.unregister(_catalogue_tick)
    for callback in tuple(_deferred):
        if bpy.app.timers.is_registered(callback):
            bpy.app.timers.unregister(callback)
    _deferred.clear()
    if _file_loaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_file_loaded)
    menu = getattr(bpy.types, 'SV_MT_SocketOptionsMenu', None)
    if menu:
        menu.remove(_socket_menu)
    for keymap, item in _keymaps:
        keymap.keymap_items.remove(item)
    _keymaps.clear()
    _entries.clear()
    _pending.clear()
    _active_variants.clear()
    _active_node_type = None
    _sessions.clear()
    _signature = None
    _ready = False
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

# ----------------------------------------------------------------------------
# Curve Mapper and helper resources
# ----------------------------------------------------------------------------

from importlib import import_module
from uuid import uuid4


_PROVIDERS = {
    'SvCurveMapperNode': 'sverchok.nodes.number.curve_mapper',
    'SvColorRampNode': 'sverchok.nodes.color.color_ramp',
}


def prepare_node_resources(node_type):
    """Bootstrap a missing shared helper, without touching existing mappings.

    The resulting state matches creating and deleting an ordinary node: the
    shared shader tree and its information frame remain, but the temporary
    curve/ramp does not. Return whether a helper was created.
    """
    provider = _PROVIDERS.get(node_type)
    if provider is None:
        return False

    import bpy

    module = import_module(provider)
    group_name = module.node_group_name
    group = bpy.data.node_groups.get(group_name)
    if group is not None:
        if group.bl_idname != 'ShaderNodeTree':
            raise RuntimeError("The helper {!r} is not a shader node tree".format(group_name))
        return False

    probe_name = '.SV Link Search Init ' + uuid4().hex
    try:
        # This is the same factory called by the node's sv_init(), including
        # Blender-version-specific curve evaluation initialization.
        module.get_evaluator(group_name, probe_name)
        group = bpy.data.node_groups.get(group_name)
        if group is None or group.bl_idname != 'ShaderNodeTree':
            raise RuntimeError('The node did not initialize its shader helper')
        probe = group.nodes.get(probe_name)
        if probe is None:
            raise RuntimeError('The helper factory did not create its temporary node')
        group.nodes.remove(probe)
    except Exception:
        # Only roll back the group this call created, and only if it contains
        # no other node resources. Existing user curves are never removed.
        group = bpy.data.node_groups.get(group_name)
        if (group is not None and group.bl_idname == 'ShaderNodeTree'
                and all(node.bl_idname == 'NodeFrame' or node.name == probe_name
                        for node in group.nodes)):
            bpy.data.node_groups.remove(group)
        raise
    return True
