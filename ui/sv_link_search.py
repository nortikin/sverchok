# SPDX-License-Identifier: GPL-3.0-or-later
"""Experimental link-drag search for Sverchok's custom node editor.

The native link operator retains ownership of drawing, panning and connections.
A small observer opens our popup only after a drag finishes over empty space.
"""

import logging
import uuid

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty

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
_waiting = set()
_deferred = set()


def available_node_types():
    """Use the same menu registry as Sverchok's existing node search."""
    ids = set()
    menu = get_add_node_menu()
    if menu is None:
        return ()
    for category in menu.walk_categories():
        for item in category:
            name = getattr(item, 'bl_idname', '')
            if not name or name in {'NodeFrame', 'NodeReroute'}:
                continue
            cls = bpy.types.Node.bl_rna_get_subclass_py(name)
            if cls and not getattr(cls, 'missing_dependency', False):
                ids.add(name)
    # First build useful operations, then the remaining menu in stable order.
    priority = {'SvScalarMathNodeMK4', 'SvVectorMathNodeMK3', 'SvLogicNodeMK2',
                'SvColorMixNode', 'SvComponentAnalyzerNode'}
    return tuple(sorted(ids, key=lambda name: (name not in priority, name)))


def collect_node_type(node_type):
    """Create transient nodes, copy descriptions, remove ALL scratch data.

    A scratch tree lives within one call only; it cannot be saved between timer
    ticks. No user tree, socket data or node process() method is used.
    """
    from sverchok.core.update_system import UpdateTree
    from sverchok.core.tasks import tasks

    groups_before = {group.as_pointer() for group in bpy.data.node_groups}
    helper = bpy.data.node_groups.get('sverchok_helper_group')
    helper_fake_user = helper.use_fake_user if helper else None
    tree = bpy.data.node_groups.new('.SV Link Search Index', 'SverchCustomTreeType')
    result = []
    try:
        tree.sv_process = False
        tree.sv_animate = False
        tree.sv_show = False
        with tree.init_tree():
            probe = tree.nodes.new(node_type)
            variants = tuple(operation_variants(probe))
            tree.nodes.clear()
            for settings, operation in variants:
                try:
                    node = tree.nodes.new(node_type)
                    configure_node(node, settings)
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
    return result


def _catalogue_tick():
    global _ready
    if not _enabled:
        return None
    if _signature is None:
        ensure_catalogue()
    if not _pending:
        _ready = True
        return None
    node_type = _pending.pop(0)
    try:
        _entries.extend(collect_node_type(node_type))
    except Exception:
        log.warning('Link search skipped %s', node_type, exc_info=True)
    _ready = not _pending
    return 0.01 if _pending else None


def ensure_catalogue(force=False):
    global _signature, _ready, _generation
    signature = available_node_types()
    if force or signature != _signature:
        _generation += 1
        _signature = signature
        _ready = False
        _entries.clear()
        _pending[:] = signature
        _sessions.clear()
    if _pending and not bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.register(_catalogue_tick, first_interval=0.05)
    if not _pending:
        _ready = True
    return _ready


@persistent
def _file_loaded(_unused):
    global _signature
    # Keep only plain descriptions across undo; opening another file invalidates
    # them because nodes may depend on that file's data.
    _signature = None
    if _enabled and not bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.register(_catalogue_tick, first_interval=1.0)


def _editor_tree(context):
    space = context.space_data
    if not space or space.type != 'NODE_EDITOR':
        return None
    tree = space.edit_tree
    if tree and tree.bl_idname == 'SverchCustomTreeType' and not tree.library:
        return tree
    return None


def _socket_key(socket):
    return (socket.node.name, socket.is_output, socket.identifier)


def _near_socket_column(context, x, y):
    # Most clicks concern node controls or empty space. Do not snapshot every
    # socket for those clicks; the native hit test below is needed only near an
    # input/output column. Include both expanded and collapsed node widths.
    scale = context.preferences.system.ui_scale
    vx, vy = context.region.view2d.region_to_view(x, y)
    margin = 20 * scale
    for node in _editor_tree(context).nodes:
        if not node.inputs and not node.outputs:
            continue
        left = node.location_absolute.x * scale
        top = node.location_absolute.y * scale
        if top - max(node.dimensions.y, 20 * scale) - margin <= vy <= top + margin:
            if any(abs(vx - column) <= margin for column in (
                    left, left + node.width * scale, left + node.dimensions.x)):
                return True
    return False


def _pick_socket(context, x, y):
    """Use Blender's hit test, never guessed socket row positions or ctypes.

    Socket.select is read-only RNA. Toggle selection changes exactly the
    indicated socket. Toggling again restores it; node selection is restored
    separately. Blender may clear a previous selected output on the same node.
    """
    tree = _editor_tree(context)
    if tree is None or not _near_socket_column(context, x, y):
        return None
    nodes = [(node, node.select) for node in tree.nodes]
    active = tree.nodes.active
    before = {_socket_key(socket): socket.select
              for node, _ in nodes for socket in (*node.inputs, *node.outputs)}
    try:
        bpy.ops.node.select('EXEC_DEFAULT', location=(int(x), int(y)),
                            socket_select=True, toggle=True)
        changed = [socket for node, _ in nodes
                   for socket in (*node.inputs, *node.outputs)
                   if socket.select != before[_socket_key(socket)]]
        added = [socket for socket in changed if socket.select]
        picked = added[0] if len(added) == 1 else (
            changed[0] if not added and len(changed) == 1 else None)
        if picked:
            bpy.ops.node.select('EXEC_DEFAULT', location=(int(x), int(y)),
                                socket_select=True, toggle=True)
        return picked
    finally:
        for node, selected in nodes:
            node.select = selected
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
        tree = _editor_tree(context)
        socket = _resolve_source(self, tree)
        if socket is None:
            socket = getattr(context, 'socket', None)
            if socket is None or socket.id_data != tree:
                self.report({'WARNING'}, 'Start by dragging a socket onto empty space')
                return {'CANCELLED'}
            for key, value in _source_kwargs(socket).items():
                setattr(self, key, value)
        if not ensure_catalogue():
            bpy.ops.node.sv_wait_link_search('INVOKE_DEFAULT', **_source_kwargs(socket))
            return {'CANCELLED'}
        results = ranked_entries(describe_socket(socket, self.source_index), _entries)
        if not results:
            self.report({'INFO'}, 'No compatible sockets in the current catalogue')
            return {'CANCELLED'}
        self.session = uuid.uuid4().hex
        # Keep strings and entries alive for the lifetime of the RNA enum popup.
        while len(_sessions) > 7:
            _sessions.pop(next(iter(_sessions)))
        _sessions[self.session] = dict(
            results=results, generation=_generation, tree_pointer=tree.as_pointer(),
            location=tuple(context.space_data.cursor_location),
            items=[(str(i), entry.label, entry.node_type, i)
                   for i, entry in enumerate(results)])
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    def execute(self, context):
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
            entry = session['results'][int(self.choice)]
        except (ValueError, IndexError):
            return {'CANCELLED'}
        selected = [(node, node.select) for node in tree.nodes]
        active = tree.nodes.active
        original_nodes = {node.as_pointer() for node in tree.nodes}
        try:
            with tree.init_tree():
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
                tree.links.new(output, input_)
            # In particular, let List nodes adopt the type of their new input.
            node.update()
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


class SvWaitLinkSearch(bpy.types.Operator):
    """Wait for the automatic socket catalogue (Esc cancels this search)"""
    bl_idname = 'node.sv_wait_link_search'
    bl_label = 'Preparing Sverchok Socket Search'
    bl_options = {'INTERNAL'}
    __annotations__ = _source_properties()

    def invoke(self, context, event):
        self._area = context.area
        self._tree = _editor_tree(context)
        self._location = tuple(context.space_data.cursor_location)
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        _waiting.add(self)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _finish(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        context.workspace.status_text_set(None)
        _waiting.discard(self)

    def cancel(self, context):
        self._finish(context)

    def modal(self, context, event):
        if (not _enabled or context.area != self._area
                or _editor_tree(context) != self._tree
                or event.type in {'ESC', 'RIGHTMOUSE', 'WINDOW_DEACTIVATE'}):
            self._finish(context)
            return {'CANCELLED'}
        if event.type == 'TIMER' and event.timer == self._timer:
            if _ready:
                self._finish(context)
                context.space_data.cursor_location = self._location
                source = _resolve_source(self, self._tree)
                if source:
                    bpy.ops.node.sv_socket_link_search('INVOKE_DEFAULT', **_source_kwargs(source))
                return {'FINISHED'}
            context.workspace.status_text_set(
                'Indexing Sverchok sockets: {} node types remaining. Esc cancels search.'.format(
                    len(_pending)))
        return {'RUNNING_MODAL'}


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
                        if (_editor_tree(ctx) == tree and _link_signature(source) == links
                                and _over_empty_space(ctx, x, y)):
                            ctx.space_data.cursor_location_from_region(x, y)
                            bpy.ops.node.sv_socket_link_search(
                                'INVOKE_DEFAULT', **_source_kwargs(source))
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


classes = (SvSocketLinkSearch, SvWaitLinkSearch, SvObserveLinkDrag, SvRebuildLinkSearch)


def register():
    global _enabled, _signature
    for cls in classes:
        bpy.utils.register_class(cls)
    _enabled = True
    _signature = None
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
    if not bpy.app.background:
        bpy.app.timers.register(_catalogue_tick, first_interval=1.0)


def unregister():
    global _enabled, _signature, _ready
    _enabled = False
    if bpy.app.timers.is_registered(_catalogue_tick):
        bpy.app.timers.unregister(_catalogue_tick)
    for callback in tuple(_deferred):
        if bpy.app.timers.is_registered(callback):
            bpy.app.timers.unregister(callback)
    _deferred.clear()
    for waiter in tuple(_waiting):
        try:
            waiter._finish(bpy.context)
        except (ReferenceError, RuntimeError):
            pass
    _waiting.clear()
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
    _sessions.clear()
    _signature = None
    _ready = False
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
