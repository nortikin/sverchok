# SPDX-License-Identifier: GPL-3.0-or-later
"""Native event tests; run with --enable-event-simulate under a real/Xvfb display."""
import json
import os
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_search_tests  # Enables this repository before importing its UI.

import bpy
from sverchok.ui import sv_link_search as base, sv_link_search_popup as popup

CASES = ('cold', 'filtered-row', 'typo', 'replace-bundle', 'group', 'configured', 'nested', 'escape')
completed = []
stage = 0
case_index = 0
area = tree = root_tree = session = source = None
tree_name = None
baseline = None
mouse = None
expected = None


def snapshot(tree):
    return (len(tree.nodes), frozenset((l.from_node.name, l.from_socket.name,
                                       l.to_node.name, l.to_socket.name) for l in tree.links))


def finish(ok, error=''):
    path = Path(os.environ.get('LINK_SEARCH_GUI_RESULT', 'link-search-gui.json'))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(ok=ok, completed=completed, error=error), indent=2))
    print('LINK_SEARCH_GUI_RESULT', ok, completed, error, flush=True)
    bpy.ops.wm.quit_blender()


def tick():
    global stage, case_index, area, tree, root_tree, session, source
    global tree_name, baseline, mouse, expected
    try:
        if stage == 0:
            if bpy.app.timers.is_registered(base._catalogue_tick):
                bpy.app.timers.unregister(base._catalogue_tick)
            area = bpy.context.screen.areas[0]
            area.type = 'NODE_EDITOR'
            area.ui_type = 'SverchCustomTreeType'
            _check_native_socket_hit(area)
            entries = []
            for node_type in base.available_node_types():
                entries.extend(base.collect_node_type(node_type, base._node_variants(node_type)))
            base._signature = base.available_node_types()
            base._entries[:] = entries
            base._pending.clear()
            base._active_variants.clear()
            base._ready = True
            stage = 1
            return 0.5
        region = next(r for r in area.regions if r.type == 'WINDOW')
        case = CASES[case_index]
        if stage == 1:
            area.spaces.active.path.clear()
            root_tree = bpy.data.node_groups.new('GUI ' + case, 'SverchCustomTreeType')
            root_tree.sv_process = False
            area.spaces.active.node_tree = root_tree
            tree = root_tree
            if case in {'cold', 'filtered-row'}:
                source = tree.nodes.new('SvScalarMathNodeMK4').outputs[0]
            elif case == 'configured':
                template = tree.nodes.new('ListJoinNode')
                template.name = 'Configured join'
                template.outputs[0].replace_socket('SvSurfaceSocket')
                source = tree.nodes.new('SvFlipSurfaceNode').inputs[0]
            elif case in {'group', 'nested'}:
                group = bpy.data.node_groups.new('Test geometry group', 'SvGroupTree')
                group.interface.new_socket('Vertices', in_out='INPUT', socket_type='SvVerticesSocket')
                group.interface.new_socket('Edges', in_out='INPUT', socket_type='SvStringsSocket')
                group.interface.new_socket('Vertices', in_out='OUTPUT', socket_type='SvVerticesSocket')
                if case == 'nested':
                    owner = root_tree.nodes.new('SvGroupTreeNode')
                    owner.group_tree = group
                    group.group_node_name = owner.name
                    area.spaces.active.path.append(group, node=owner)
                    tree = group
                    with group.init_tree():
                        source = group.nodes.new('NodeGroupInput').outputs['Vertices']
                else:
                    source = tree.nodes.new('SvBoxNodeMk2').outputs['Vers']
            else:
                box = tree.nodes.new('SvBoxNodeMk2')
                box.name = 'New mesh'
                source = box.outputs['Vers']
                if case == 'replace-bundle':
                    old = tree.nodes.new('SvBoxNodeMk2')
                    old.name = 'Old mesh'
                    target = tree.nodes.new('SvBevelNodeMK2')
                    target.name = 'Destination'
                    for output, name in [('Vers', 'vertices'), ('Edgs', 'edges'), ('Pols', 'polygons')]:
                        tree.links.new(old.outputs[output], target.inputs[name])
            if case == 'cold':
                base._entries.clear()
                base._pending[:] = base.available_node_types()
                base._ready = False
            tree_name = tree.name
            baseline = snapshot(tree)
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.ed.undo_push(message='Link Search fixture ' + case)
                bpy.ops.node.sv_socket_link_search('INVOKE_DEFAULT', **base._source_kwargs(source))
            session = base._sessions[next(iter(popup._live))]
            if case == 'cold':
                assert not base._ready
                assert session['popup'] is not None
                assert isinstance(session['query'], popup.Query)
            stage = 2
            return 0.6
        if stage == 2:
            query = {'cold': 'Scalar Math Absolute', 'filtered-row': 'scalar math', 'typo': 'bebel',
                'replace-bundle': '<Destination replace vep', 'group': 'Test geometry group',
                'configured': 'Configured join', 'nested': 'Vector Math Length', 'escape': 'bevel'}[case]
            session['query'].insert(query)
            popup._filter(session)
            popup._redraw(session)
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            stage = 3
            return 0.6
        if stage == 3:
            assert session['visible'], case
            slot = 1 if case == 'filtered-row' else 0
            expected = session['results'][session['visible'][slot]]
            print('GUI_SELECTION', case, expected.label, session['visible'][slot], flush=True)
            if case == 'typo':
                assert expected.node_type == 'SvBevelNodeMK2'
                assert any('bevel' in text.casefold() for text in session['entry_hints'])
            if case == 'nested':
                assert expected.operation == 'Length', expected.label
            if case == 'replace-bundle':
                assert expected.replace_all
            if case == 'escape':
                bpy.context.window.event_simulate(type='ESC', value='PRESS')
                bpy.context.window.event_simulate(type='ESC', value='RELEASE')
                stage = 6
                return 0.6
            pop = session['popup']
            assert pop.width <= bpy.context.window.width, ('Popup is wider than the window', pop.width)
            mouse = (pop.x + 120, pop.y + pop.height - 79 - 20 * slot)
            bpy.context.window.event_simulate(type='MOUSEMOVE', value='NOTHING', x=mouse[0], y=mouse[1])
            stage = 4
            return 0.4
        if stage == 4:
            bpy.context.window.event_simulate(type='LEFTMOUSE', value='PRESS', x=mouse[0], y=mouse[1])
            stage = 5
            return 0.2
        if stage == 5:
            bpy.context.window.event_simulate(type='LEFTMOUSE', value='RELEASE', x=mouse[0], y=mouse[1])
            stage = 6
            return 0.7
        if stage == 6:
            if case == 'escape':
                assert snapshot(tree) == baseline
            else:
                if case == 'replace-bundle':
                    assert len(tree.links) == 3
                    assert all(l.from_node.name == 'New mesh' for l in tree.links)
                else:
                    node = tree.nodes.active
                    assert node.bl_idname == expected.node_type, (case, node.bl_idname, expected.label)
                    assert len(tree.nodes) == baseline[0] + 1
                    assert tree.links
                    for key, value in expected.settings:
                        assert getattr(node, key) == value, (key, getattr(node, key), value)
                with bpy.context.temp_override(area=area, region=region):
                    bpy.ops.ed.undo()
                tree = bpy.data.node_groups.get(tree_name)
                assert tree is not None and snapshot(tree) == baseline, case
            completed.append(case)
            case_index += 1
            if case_index == len(CASES):
                finish(True)
                return None
            stage = 1
            return 0.5
    except Exception:
        error = traceback.format_exc()
        print(error, flush=True)
        report = bpy.data.texts.get('SV Link Search Report')
        if report:
            print(report.as_string(), flush=True)
        finish(False, error)
        return None



def _check_native_socket_hit(area):
    """Exercise the actual socket picker before testing search-menu creation."""
    from sverchok.core.update_system import UpdateTree
    from sverchok.core.tasks import tasks

    region = next(r for r in area.regions if r.type == 'WINDOW')
    space = area.spaces.active
    old_tree, old_pin = space.node_tree, space.pin
    tree = bpy.data.node_groups.new('.Link Search Native Hit Test', 'SverchCustomTreeType')
    tree.sv_process = False
    try:
        with tree.init_tree():
            source = tree.nodes.new('SvScalarMathNodeMK4')
            other = tree.nodes.new('SvScalarMathNodeMK4')
            source.location = (0, 0)
            other.location = (1000, 0)
        space.pin = True
        space.node_tree = tree
        source.select, other.select = True, False
        tree.nodes.active = source
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.node.view_selected()
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        source.select, other.select = False, True
        tree.nodes.active = other

        def snapshot():
            return ({n.as_pointer(): n.select for n in tree.nodes}, tree.nodes.active,
                    tuple((s.as_pointer(), s.select) for n in (source, other)
                          for sockets in (n.inputs, n.outputs) for s in sockets))

        def restore_nodes(saved):
            flags, active = saved[:2]
            for node in tree.nodes:
                node.select = flags[node.as_pointer()]
            tree.nodes.active = active

        def find_socket(output):
            # Native selection discovers the coordinate; no socket-row offsets
            # or private Blender memory are used by the picker or the test.
            saved = snapshot()
            scale = bpy.context.preferences.system.ui_scale
            left, top = source.location_absolute
            left, top = left * scale, top * scale
            width, height = source.dimensions
            columns = (left + width, left + source.width * scale) if output else (left,)
            try:
                with bpy.context.temp_override(area=area, region=region):
                    for column in columns:
                        for offset in range(0, int(max(height, 20 * scale)) + 30, 2):
                            x, y = region.view2d.view_to_region(column, top - offset, clip=False)
                            if not (0 <= x < region.width and 0 <= y < region.height):
                                continue
                            bpy.ops.node.select('EXEC_DEFAULT', location=(x, y),
                                                socket_select=True, toggle=True)
                            picked = [s for sockets in (source.inputs, source.outputs)
                                      for s in sockets if s.select]
                            if picked:
                                bpy.ops.node.select('EXEC_DEFAULT', location=(x, y),
                                                    socket_select=True, toggle=True)
                                if len(picked) == 1 and picked[0].is_output == output:
                                    return (x, y), picked[0]
                raise AssertionError('Could not locate the native socket for the hit test')
            finally:
                restore_nodes(saved)
                assert snapshot() == saved, 'Native coordinate discovery changed selection'

        def verify(output):
            point, socket = find_socket(output)
            saved = snapshot()
            with bpy.context.temp_override(area=area, region=region):
                assert base._pick_socket(bpy.context, *point) == socket
            assert snapshot() == saved, 'Link Search changed node or socket selection'
            return point, socket

        output_point, output = verify(True)
        verify(False)
        saved = snapshot()
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.node.select('EXEC_DEFAULT', location=output_point,
                                socket_select=True, toggle=True)
        # Keep the selection state produced by Blender. Deselecting its owner
        # can clear a selected socket; only change the active-node pointer.
        tree.nodes.active = other
        selected = snapshot()
        try:
            assert output.select
            with bpy.context.temp_override(area=area, region=region):
                assert base._pick_socket(bpy.context, *output_point) is None
            assert snapshot() == selected, 'A preselected output was changed'
        finally:
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.node.select('EXEC_DEFAULT', location=output_point,
                                    socket_select=True, toggle=True)
            restore_nodes(saved)
        assert snapshot() == saved
        source.hide = True
        with bpy.context.temp_override(area=area, region=region):
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        verify(True)
        print('LINK_SEARCH_NATIVE_HIT_OK: input, output, collapsed node, selection preservation', flush=True)
    finally:
        space.node_tree = old_tree
        space.pin = old_pin
        with tree.init_tree():
            tree.nodes.clear()
        for task in tuple(tasks._todo):
            if task.tree == tree:
                tasks._todo.discard(task)
        if tree.tree_id in UpdateTree._tree_catch:
            UpdateTree.reset_tree(tree)
        bpy.data.node_groups.remove(tree)


bpy.app.timers.register(tick, first_interval=2.0)
