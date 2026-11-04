# SPDX-License-Identifier: GPL-3.0-or-later
"""One socket-search interaction, including while the catalogue is loading."""

from dataclasses import dataclass, field
import re
import uuid

import bpy
from bpy.app.handlers import persistent
from bpy.props import BoolProperty, IntProperty, StringProperty

from sverchok.utils.sv_link_search import describe_socket, ranked_entries, connection_score
from sverchok.utils.sv_link_search import query_score


_enabled = False
_live = set()
_windows = {}
_listeners = set()
_ROWS = 10


def _base():
    from sverchok.ui import sv_link_search
    return sv_link_search


@dataclass
class Query:
    """Single-line editing without making Enter/Esc exit text editing first."""
    text: str = ''
    caret: int = 0
    anchor: int = 0
    undo: list = field(default_factory=list)
    redo: list = field(default_factory=list)

    def snapshot(self):
        return self.text, self.caret, self.anchor

    def restore(self, state):
        self.text, self.caret, self.anchor = state

    def insert(self, value):
        value = value.replace('\r', ' ').replace('\n', ' ')
        left, right = sorted((self.caret, self.anchor))
        next_text = self.text[:left] + value + self.text[right:]
        if next_text != self.text:
            self.undo.append(self.snapshot())
            del self.undo[:-100]
            self.redo.clear()
        self.text = next_text
        self.caret = self.anchor = left + len(value)

    def move(self, direction, shift=False, word=False):
        if not shift and self.caret != self.anchor:
            self.caret = min(self.caret, self.anchor) if direction < 0 else max(self.caret, self.anchor)
        elif word:
            if direction < 0:
                match = re.search(r'\S+\s*$', self.text[:self.caret])
                self.caret = match.start() if match else 0
            else:
                match = re.match(r'\s*\S+\s*', self.text[self.caret:])
                self.caret += match.end() if match else len(self.text) - self.caret
        else:
            self.caret = max(0, min(len(self.text), self.caret + direction))
        if not shift:
            self.anchor = self.caret

    def delete(self, direction, word=False):
        if self.caret == self.anchor:
            self.move(direction, shift=True, word=word)
        self.insert('')

    def history(self, redo=False):
        source, target = (self.redo, self.undo) if redo else (self.undo, self.redo)
        if source:
            target.append(self.snapshot())
            self.restore(source.pop())

    def display(self):
        start = max(0, self.caret - 55)
        end = min(len(self.text), start + 75)
        return (('…' if start else '') + self.text[start:self.caret] + '|'
                + self.text[self.caret:end] + ('…' if end < len(self.text) else ''))


def _choice_index(session, index, row=-1, keyboard=False):
    """Resolve a physical menu row against the last drawn result list.

    Blender can retain a row button's old operator properties on menu refresh.
    Its physical row stays stable even when filtering changes the entry index.
    Keyboard navigation owns an explicit active entry; mouse clicks own a row.
    """
    if keyboard:
        index = session['active']
    elif row >= 0:
        drawn = session.get('drawn_indices', ())
        index = drawn[row] if row < len(drawn) else -1
    return index if index in session['visible'] else -1


def _matches(query, text):
    return query_score(query, text) is not None


def _search_mode(text):
    stripped = text.lstrip()
    return ('tree', stripped[1:].lstrip()) if stripped.startswith('<') else ('new', text)


def _toggle_mode(query):
    caret, anchor = query.caret, query.anchor
    position = len(query.text) - len(query.text.lstrip())
    removing = query.text[position:].startswith('<')
    if removing:
        text = query.text[:position] + query.text[position + 1:]
    else:
        text = query.text[:position] + '<' + query.text[position:]
    query.caret, query.anchor = len(query.text), 0
    query.insert(text)
    def adjust(index):
        if removing:
            return index - 1 if index > position else index
        return index + 1 if index >= position else index
    query.caret = max(0, min(len(text), adjust(caret)))
    query.anchor = max(0, min(len(text), adjust(anchor)))


def _entry_triggers(entry):
    if getattr(entry, 'triggers', ''):
        return ' '.join(entry.triggers.split())
    cls = bpy.types.Node.bl_rna_get_subclass_py(entry.node_type)
    description = cls.bl_rna.description if cls else ''
    return _trigger_text(description)


from functools import lru_cache as _lru_cache


@_lru_cache(maxsize=1024)
def _trigger_text(description):
    from sverchok.utils.docstring import SvDocstring
    return ' '.join((SvDocstring(description).get_shorthand() or '').split())


def _append_entry(session, entry, mode):
    index = len(session['results'])
    triggers = _entry_triggers(entry)
    session['results'].append(entry)
    session['items'].append((str(index), entry.label, entry.node_type, index))
    settings = ' '.join(str(value) for key, value in getattr(entry, 'settings', ()))
    bundle = getattr(entry, 'bundle_name', '').replace('+', '')
    session['search_text'].append((entry.label + ' ' + entry.node_type + ' '
        + entry.node_label + ' ' + settings + ' ' + triggers + ' ' + bundle).casefold())
    session['entry_hints'].append(triggers)
    session['entry_modes'].append(mode)


def _append_contextual(session):
    from sverchok.utils.sv_link_search_extensions import group_entries, configured_entries
    editor = session.get('editor_context')
    if editor is None:
        return
    try:
        window, area, region = editor
        with bpy.context.temp_override(window=window, area=area, region=region):
            base = _base()
            tree = base._editor_tree(bpy.context)
            if tree is None or tree.as_pointer() != session['tree_pointer']:
                return
            if not session.get('groups_loaded'):
                for entry in ranked_entries(session['source_info'], group_entries(tree)):
                    _append_entry(session, entry, 'new')
                session['groups_loaded'] = True
            if base._ready and not session.get('templates_loaded'):
                for entry in ranked_entries(session['source_info'], configured_entries(tree)):
                    _append_entry(session, entry, 'new')
                session['templates_loaded'] = True
    except (TypeError, ReferenceError):
        return


def _load_existing(session):
    from types import SimpleNamespace
    from sverchok.utils.sv_link_search_extensions import existing_entries
    session['existing_loaded'] = True
    editor = session.get('editor_context')
    if editor is None:
        return
    try:
        window, area, region = editor
        with bpy.context.temp_override(window=window, area=area, region=region):
            base = _base()
            tree = base._editor_tree(bpy.context)
            if tree is None or tree.as_pointer() != session['tree_pointer']:
                return
            source = base._resolve_source(SimpleNamespace(**session['source_kwargs']), tree)
            if source is not None:
                for entry in existing_entries(tree, source):
                    _append_entry(session, entry, 'tree')
    except (ReferenceError, TypeError):
        return


def _entry_label(session, index):
    from sverchok.utils.sv_link_search_extensions import bundle_label
    entry = session['results'][index]
    badge = bundle_label(session['source_info'], session['source_ports'], entry)
    return entry.label + ('  ·  ' + badge if badge and not getattr(entry, 'replace_all', False) else '')


def _filter(session):
    mode, query = _search_mode(session['query'].text)
    if mode == 'tree' and not session.get('existing_loaded'):
        _load_existing(session)
    matches = []
    for index, text in enumerate(session['search_text']):
        if session['entry_modes'][index] != mode:
            continue
        entry = session['results'][index]
        primary = query_score(query, entry.label)
        score = primary if primary is not None else query_score(query, text)
        if score is not None:
            if primary is None:
                score += 8
            compatible = connection_score(session['source_info'], entry.socket)
            if compatible is not None:
                matches.append((score, compatible, getattr(entry, 'replace_all', False),
                                getattr(entry, 'replace', False), index))
    session['visible'] = [item[-1] for item in sorted(matches)]
    filter_key = (mode, query.casefold())
    if session.get('filter_key') != filter_key:
        session['active'] = session['visible'][0] if session['visible'] else -1
        session['offset'] = 0
        session['filter_key'] = filter_key
        session['selection_locked'] = False
    elif not session.get('selection_locked') and session.get('keyboard', True):
        session['active'] = session['visible'][0] if session['visible'] else -1
    visible = session['visible']
    if session['active'] not in visible:
        session['active'] = visible[0] if visible else -1
    if visible:
        position = visible.index(session['active'])
        offset = min(session['offset'], max(0, len(visible) - _ROWS))
        session['offset'] = min(position, max(offset, position - _ROWS + 1))
    else:
        session['offset'] = 0


def _append_results(session):
    base = _base()
    if session['generation'] != base._generation:
        return
    before = len(session['results'])
    _append_contextual(session)
    start = session['scanned']
    if start == len(base._entries):
        if len(session['results']) != before:
            _filter(session)
        return
    entries = ranked_entries(session['source_info'], base._entries[start:])
    session['scanned'] = len(base._entries)
    for entry in entries:
        _append_entry(session, entry, 'new')
    _filter(session)


def _valid_context(session, context):
    base = _base()
    tree = base._editor_tree(context)
    return (_enabled and base._enabled and session['generation'] == base._generation
            and tree is not None and tree.as_pointer() == session['tree_pointer']
            and (not session['automatic'] or base.link_drag_search_enabled(context)))


def _popup_exists(session):
    popup = session.get('popup')
    if popup is None:
        return False
    try:
        # This validates the borrowed temporary region before any dereference,
        # following Blender's bundled bl_extension_notify._region_exists.
        with bpy.context.temp_override(window=session['window'], area=session['area'],
                                       region=popup):
            return True
    except (TypeError, ReferenceError):
        return False


def _release(key):
    _live.discard(key)
    session = _base()._sessions.get(key)
    if session:
        # Popup RNA is short-lived. Keep the source editor until choice execution.
        for name in ('popup', 'window', 'area', 'region'):
            session.pop(name, None)
    for window, value in tuple(_windows.items()):
        if value == key:
            del _windows[window]


def _redraw(session):
    popup = session.get('popup')
    if popup:
        popup.tag_refresh_ui()
        popup.tag_redraw()


def _refresh():
    if not _enabled:
        return None
    base = _base()
    for key in tuple(_live):
        session = base._sessions.get(key)
        if not session or not _popup_exists(session):
            _release(key)
            continue
        try:
            with bpy.context.temp_override(window=session['window'], area=session['area'],
                                           region=session['region']):
                valid = _valid_context(session, bpy.context)
                if valid:
                    _append_results(session)
                stamp = (len(base._entries), len(base._pending),
                         len(getattr(base, '_active_variants', ())), base._ready, valid)
                if session.get('stamp') != stamp:
                    _redraw(session)
                    session['stamp'] = stamp
        except (TypeError, ReferenceError):
            _release(key)
    return 0.05 if _live else None


def _move_selection(session, delta):
    visible = session['visible']
    if visible:
        current = visible.index(session['active']) if session['active'] in visible else 0
        session['active'] = visible[max(0, min(len(visible) - 1, current + delta))]
        session['keyboard'] = True
        session['selection_locked'] = True
        _filter(session)


class SV_MT_LiveSocketSearch(bpy.types.Menu):
    bl_label = 'Search and Connect'

    def draw(self, context):
        base = _base()
        key = _windows.get(context.window.as_pointer())
        session = base._sessions.get(key)
        layout = self.layout
        layout.ui_units_x = 24
        if not session:
            layout.label(text='Search expired. Drop the link again.', icon='INFO')
            return
        session['popup'] = context.region_popup
        if not _valid_context(session, context):
            layout.label(text='Search changed. Drop the link again.', icon='INFO')
            return
        # The search header is deliberately not a separate text-edit control:
        # Enter chooses a node and Esc closes the menu in a single key press.
        layout.label(text=session['query'].display(), icon='VIEWZOOM')
        layout.operator_context = 'INVOKE_REGION_WIN'
        offset = session['offset']
        indices = session['visible'][offset:offset + _ROWS]
        # SV_LINK_SEARCH_STABLE_ROWS_V4_6: refreshed buttons refer to row slots.
        session['drawn_indices'] = tuple(indices)
        columns = layout.row()
        choices = columns.column()
        choices.ui_units_x = 17
        for slot, index in enumerate(indices):
            choice = choices.row()
            choice.activate_init = session['keyboard'] and index == session['active']
            choice.active_default = session['keyboard'] and index == session['active']
            label = _entry_label(session, index)
            if len(label) > 44:
                label = label[:24] + '…' + label[-19:]
            op = choice.operator('node.sv_live_socket_choose', text=label,
                                 icon='FORWARD' if index == session['active'] else 'BLANK1')
            op.session = key
            op.index = index
            op.row = slot
        for _unused in range(_ROWS - len(indices)):
            choices.label(text=' ')
        # V5: mode and progress share the existing footer.
        mode, _query = _search_mode(session['query'].text)
        loading = mode == 'new' and not base._ready
        count = len(session['visible'])
        if count:
            footer = '{}–{} / {}'.format(offset + 1, offset + len(indices), count)
        else:
            footer = 'No matches yet' if loading else 'No compatible matches'
        footer = ('Tree' if mode == 'tree' else 'New') + '  ·  ' + footer
        if loading:
            footer += '  ·  Indexing nodes…'
        choices.label(text=footer, icon='TIME' if loading else 'NONE')
        # Native menus measure columns in button creation order. Emit each
        # whole column together; interleaved row splits grow the popup width.
        hints = columns.column()
        hints.ui_units_x = 7
        hints.enabled = False
        for index in indices:
            text = session['entry_hints'][index]
            hints.label(text=text if len(text) <= 18 else text[:17] + '…')
        for _unused in range(_ROWS - len(indices) + 1):
            hints.label(text=' ')


class SvLiveSocketChoose(bpy.types.Operator):
    """Connect the result. Shift: selected socket only. Hover for full details."""
    bl_idname = 'node.sv_live_socket_choose'
    bl_label = 'Choose Socket Search Result'
    bl_options = {'INTERNAL', 'UNDO'}

    session: StringProperty(options={'SKIP_SAVE'})
    index: IntProperty(default=-1, options={'SKIP_SAVE'})
    row: IntProperty(default=-1, min=-1, max=_ROWS - 1, options={'SKIP_SAVE'})
    single_link: BoolProperty(default=False, options={'SKIP_SAVE'})

    @classmethod
    def description(cls, context, properties):
        session = _base()._sessions.get(properties.session)
        if session:
            index = _choice_index(session, properties.index, properties.row)
            if index >= 0:
                return (_entry_label(session, index) + '\n' + session['entry_hints'][index]
                        + '\nShift: connect only the selected socket')
        return 'Connect the selected socket'

    def invoke(self, context, event):
        self.single_link = event.shift
        session = _base()._sessions.get(self.session)
        if session:
            self.index = _choice_index(
                session, self.index, self.row,
                keyboard=session['keyboard'] and event.type in {'RET', 'NUMPAD_ENTER'})
            # Keep the resolved entry for execute/redo; never resolve it twice.
            self.row = -1
        return self.execute(context)

    def execute(self, context):
        base = _base()
        session = base._sessions.get(self.session)
        if session is not None:
            self.single_link = self.single_link or session.get('single_link', False)
        if not session:
            self.report({'WARNING'}, 'Search session is missing. Drop the link again.')
            return {'CANCELLED'}
        # Also support native paths that execute a menu button without invoke.
        if self.row >= 0:
            self.index = _choice_index(session, self.index, self.row,
                                       keyboard=session['keyboard'])
            self.row = -1
        if self.index not in session['visible']:
            self.report({'WARNING'}, 'Search result changed. Select the result again.')
            return {'CANCELLED'}
        # SV_LINK_SEARCH_EDITOR_CONTEXT_V4_5: the callback's context belongs to
        # the menu; validation and creation must use the original node editor.
        editor = session.get('editor_context')
        if editor is None:
            self.report({'WARNING'}, 'Original node editor is unavailable. Drop the link again.')
            return {'CANCELLED'}
        try:
            window, area, region = editor
            with context.temp_override(window=window, area=area, region=region):
                tree = base._editor_tree(context)
                if not _valid_context(session, context):
                    self.report({'WARNING'}, 'Original tree or catalogue changed; repeat the search')
                    return {'CANCELLED'}
                result = bpy.ops.node.sv_socket_link_search(
                    'EXEC_DEFAULT', session=self.session, choice=str(self.index),
                    automatic=session['automatic'], single_link=self.single_link,
                    **session['source_kwargs'])
        except Exception as error:
            base.log.exception('Link Search menu choice failed')
            self.report({'ERROR'}, str(error)[:300])
            return {'CANCELLED'}
        finally:
            _release(self.session)
            session.pop('editor_context', None)
        if 'CANCELLED' in result:
            self.report({'WARNING'}, 'Node was not created; see the console for details')
        return result


class SvLiveSocketKeys(bpy.types.Operator):
    """Keep typing and selection active while socket results arrive"""
    bl_idname = 'node.sv_live_socket_keys'
    bl_label = 'Socket Search Input'
    bl_options = {'INTERNAL'}

    session: StringProperty(options={'SKIP_SAVE'})

    def invoke(self, context, event):
        self._done = False
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        _listeners.add(self)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        self._done = True
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None
        _listeners.discard(self)

    def modal(self, context, event):
        base = _base()
        session = base._sessions.get(self.session)
        if self._done or self.session not in _live or not session or not _popup_exists(session):
            self.cancel(context)
            return {'FINISHED', 'PASS_THROUGH'}
        if not _valid_context(session, context):
            self.cancel(context)
            return {'FINISHED', 'PASS_THROUGH'}
        if event.type in {'ESC', 'RIGHTMOUSE', 'WINDOW_DEACTIVATE'}:
            self.cancel(context)
            return {'FINISHED', 'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            if (event.mouse_x, event.mouse_y) != (event.mouse_prev_x, event.mouse_prev_y):
                was_keyboard = session['keyboard']
                session['keyboard'] = False
                if was_keyboard:
                    _redraw(session)
            return {'PASS_THROUGH'}
        if event.type in {'LEFTMOUSE', 'RET', 'NUMPAD_ENTER'}:
            session['single_link'] = bool(event.shift)
        if event.value != 'PRESS':
            return {'PASS_THROUGH'}
        if event.type in {'RET', 'NUMPAD_ENTER'}:
            # Let Blender execute a menu row and close its popup normally.
            return {'PASS_THROUGH'}
        if event.type in {'UP_ARROW', 'DOWN_ARROW', 'PAGE_UP', 'PAGE_DOWN',
                          'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            step = {'UP_ARROW': -1, 'DOWN_ARROW': 1, 'PAGE_UP': -_ROWS,
                    'PAGE_DOWN': _ROWS, 'WHEELUPMOUSE': -3, 'WHEELDOWNMOUSE': 3}[event.type]
            _move_selection(session, step)
            _redraw(session)
            return {'RUNNING_MODAL'}
        query = session['query']
        control = event.ctrl or event.oskey
        if event.type == 'TAB' and not control:
            _toggle_mode(query)
        elif control and event.type == 'A':
            query.anchor, query.caret = 0, len(query.text)
        elif control and event.type in {'C', 'X'}:
            left, right = sorted((query.caret, query.anchor))
            if left != right:
                context.window_manager.clipboard = query.text[left:right]
                if event.type == 'X':
                    query.insert('')
        elif control and event.type == 'V':
            query.insert(context.window_manager.clipboard)
        elif control and event.type in {'Z', 'Y'}:
            query.history(redo=event.shift or event.type == 'Y')
        elif event.type in {'LEFT_ARROW', 'RIGHT_ARROW'}:
            query.move(-1 if event.type == 'LEFT_ARROW' else 1, event.shift, control)
        elif event.type in {'HOME', 'END'}:
            query.caret = 0 if event.type == 'HOME' else len(query.text)
            if not event.shift:
                query.anchor = query.caret
        elif event.type in {'BACK_SPACE', 'DEL'}:
            query.delete(-1 if event.type == 'BACK_SPACE' else 1, control)
        elif event.unicode and not control and not event.alt:
            query.insert(event.unicode)
        elif event.type == 'SPACE' and not control and not event.alt:
            query.insert(' ')
        else:
            return {'PASS_THROUGH'}
        session['keyboard'] = True
        _filter(session)
        _redraw(session)
        return {'RUNNING_MODAL'}


def invoke_search(operator, context, event):
    base = _base()
    automatic = getattr(operator, 'automatic', False)
    if automatic and not base.link_drag_search_enabled(context):
        return {'CANCELLED'}
    tree = base._editor_tree(context)
    socket = base._resolve_source(operator, tree)
    if socket is None:
        socket = getattr(context, 'socket', None)
        if socket is None or socket.id_data != tree:
            operator.report({'WARNING'}, 'Start by dragging a socket onto empty space')
            return {'CANCELLED'}
        for name, value in base._source_kwargs(socket).items():
            setattr(operator, name, value)
    # SV_LINK_SEARCH_MANUAL_LOCATION_V4_4: context-menu searches have no drop observer.
    if not automatic:
        region = next((item for item in context.area.regions if item.type == 'WINDOW'), None)
        if region is not None:
            with context.temp_override(region=region):
                context.space_data.cursor_location_from_region(
                    event.mouse_x - region.x, event.mouse_y - region.y)
    base.ensure_catalogue()
    # Catalogue startup is scheduled, never completed synchronously here.
    key = uuid.uuid4().hex
    while len(base._sessions) > 7:
        oldest = next(iter(base._sessions))
        _release(oldest)
        base._sessions.pop(oldest)
    session = dict(results=[], items=[], generation=base._generation,
                   tree_pointer=tree.as_pointer(), location=tuple(context.space_data.cursor_location),
                   source_info=describe_socket(socket, operator.source_index),
                   source_kwargs=base._source_kwargs(socket), automatic=automatic,
                   scanned=0, search_text=[], entry_modes=[], entry_hints=[], existing_loaded=False,
                   visible=[], query=Query(), active=-1,
                   offset=0, keyboard=True, window=context.window, area=context.area,
                   region=context.region,
                   editor_context=(context.window, context.area, context.region))
    from sverchok.utils.sv_link_search_extensions import bundle_ports
    session['source_ports'] = bundle_ports(socket.node, socket.is_output, anchor=socket)
    base._sessions[key] = session
    _append_results(session)
    _windows[context.window.as_pointer()] = key
    _live.add(key)
    bpy.ops.wm.call_menu('INVOKE_DEFAULT', name='SV_MT_LiveSocketSearch')
    bpy.ops.node.sv_live_socket_keys('INVOKE_DEFAULT', session=key)
    if not bpy.app.timers.is_registered(_refresh):
        bpy.app.timers.register(_refresh, first_interval=0.05)
    # The menu owns only a session key, not this temporary operator. Cancelling
    # the launcher avoids adding an undo step for merely opening a search.
    return {'CANCELLED'}


@persistent
def _file_loaded(_unused):
    for key in tuple(_live):
        _release(key)
    _windows.clear()
    # Editor references retained for a closing menu must not survive file loads.
    for session in _base()._sessions.values():
        session.pop('editor_context', None)


classes = (SV_MT_LiveSocketSearch, SvLiveSocketChoose, SvLiveSocketKeys)


def register():
    global _enabled
    for cls in classes:
        bpy.utils.register_class(cls)
    _enabled = True
    bpy.app.handlers.load_post.append(_file_loaded)


def unregister():
    global _enabled
    _enabled = False
    if bpy.app.timers.is_registered(_refresh):
        bpy.app.timers.unregister(_refresh)
    for listener in tuple(_listeners):
        listener.cancel(bpy.context)
    _file_loaded(None)
    if _file_loaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_file_loaded)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
