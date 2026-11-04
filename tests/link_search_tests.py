# SPDX-License-Identifier: GPL-3.0-or-later
"""Link Search regressions. Run with Blender --python tests/link_search_tests.py."""
import importlib
import importlib.abc
import importlib.util
from pathlib import Path
import sys
import unittest

def enable_addon():
    root = Path(__file__).resolve().parents[1]
    if 'sverchok' not in sys.modules:
        class RepositoryFinder(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname == 'sverchok':
                    return importlib.util.spec_from_file_location(fullname, root / '__init__.py',
                        submodule_search_locations=[str(root)])
        sys.meta_path.insert(0, RepositoryFinder())
    import addon_utils
    addon_utils.enable('sverchok', default_set=True)
    return root

# Direct execution and the GUI test's local import both need the repository
# registered first. Normal sverchok.tests discovery already has an enabled addon.
if __name__ in {'__main__', 'link_search_tests'}:
    enable_addon()

# ----------------------------------------------------------------------------
# Socket matching and creation
# ----------------------------------------------------------------------------

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

try:
    import bpy
except ImportError:
    bpy = None

from sverchok.utils.sv_link_search import (
    SearchEntry, SocketInfo, connection_score, ranked_entries, semantic_hint,
)


def socket(name, type_='SvStringsSocket', output=False, **kwargs):
    return SocketInfo(name, type_, output, semantic=semantic_hint(name, type_), **kwargs)


class LinkSearchMatchingTests(unittest.TestCase):
    def test_topology_does_not_suggest_other_topology_or_scalar(self):
        source = socket('Edges', output=True)
        self.assertIsNone(connection_score(source, socket('Polygons')))
        self.assertIsNone(connection_score(source, socket('Radius')))
        self.assertIsNotNone(connection_score(source, socket('Data')))
        self.assertEqual(connection_score(source, socket('Edges')), 0)

    def test_vector_connects_to_generic_data_but_not_mask(self):
        source = socket('Vertices', 'SvVerticesSocket', True)
        self.assertIsNotNone(connection_score(source, socket('data')))
        self.assertIsNone(connection_score(source, socket('mask')))
        self.assertIsNone(connection_score(source, socket('Faces')))

    def test_reverse_search_obeys_directional_generic_conversion(self):
        generic_input = socket('Data')
        vector_output = socket('Vertices', 'SvVerticesSocket', True)
        self.assertIsNotNone(connection_score(generic_input, vector_output))
        generic_output = socket('Data', output=True)
        vector_input = socket('Vertices', 'SvVerticesSocket')
        self.assertIsNone(connection_score(generic_output, vector_input))

    def test_same_direction_never_suggested(self):
        self.assertIsNone(connection_score(socket('Edges'), socket('Edges')))

    def test_faces_alias_and_mask_names(self):
        self.assertEqual(semantic_hint('Polygons', 'SvStringsSocket'), 'faces')
        self.assertEqual(semantic_hint('Face Mask', 'SvStringsSocket'), 'mask')
        self.assertEqual(semantic_hint('mask', 'SvStringsSocket'), 'mask')
        self.assertEqual(semantic_hint('Edge Length', 'SvStringsSocket'), 'number')

    def test_unrecognized_name_keeps_broad_suggestions(self):
        self.assertEqual(semantic_hint('Out', 'SvStringsSocket'), '')
        self.assertIsNotNone(connection_score(socket('Out', output=True), socket('Edges')))

    def test_special_types_are_not_generic_strings(self):
        source = socket('Curve', 'SvCurveSocket', True)
        self.assertIsNone(connection_score(source, socket('Surface', 'SvSurfaceSocket')))
        self.assertIsNotNone(connection_score(source, socket('Data')))

    def test_specific_matching_sockets_rank_before_generic(self):
        def entry(label, sock):
            return SearchEntry(label, label, '', (), sock)
        generic = entry('A List Mask', socket('Data'))
        exact = entry('Z Edges Node', socket('Edges'))
        wrong = entry('Faces Node', socket('Faces'))
        result = ranked_entries(socket('Edges', output=True), [generic, wrong, exact])
        self.assertEqual(result, [exact, generic])

    def test_known_conversion_has_lower_priority_than_exact_type(self):
        source = socket('Vertices', 'SvVerticesSocket', True)
        exact = socket('A', 'SvVerticesSocket')
        matrix = socket('Matrix', 'SvMatrixSocket')
        self.assertLess(connection_score(source, exact), connection_score(source, matrix))

    def test_list_mask_data_output_is_generic(self):
        self.assertEqual(semantic_hint('dataTrue', 'SvStringsSocket'), 'generic')
        self.assertEqual(semantic_hint('dataFalse', 'SvStringsSocket'), 'generic')


@unittest.skipUnless(bpy is not None, 'Requires Blender and enabled Sverchok')
class LinkSearchCreationTests(unittest.TestCase):
    def setUp(self):
        from sverchok.ui import sv_link_search as ui
        self.ui = ui
        self.preferences = bpy.context.preferences.addons['sverchok'].preferences
        self.old_link_drag_search = self.preferences.link_drag_search
        self.tree = bpy.data.node_groups.new('Link Search Test', 'SverchCustomTreeType')
        self.tree.sv_process = False
        self.area = bpy.context.screen.areas[0]
        self.old_type = self.area.type
        self.old_tree_type = self.old_tree = None
        if self.old_type == 'NODE_EDITOR':
            self.old_tree_type = self.area.spaces.active.tree_type
            self.old_tree = self.area.spaces.active.node_tree
        self.area.type = 'NODE_EDITOR'
        self.area.spaces.active.tree_type = 'SverchCustomTreeType'
        self.area.spaces.active.node_tree = self.tree
        self.region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.session = uuid.uuid4().hex

    def tearDown(self):
        from sverchok.core.update_system import UpdateTree
        self.preferences.link_drag_search = self.old_link_drag_search
        self.ui._sessions.pop(self.session, None)
        self.area.spaces.active.node_tree = None
        if self.old_type == 'NODE_EDITOR':
            self.area.spaces.active.tree_type = self.old_tree_type
            self.area.spaces.active.node_tree = self.old_tree
        else:
            self.area.type = self.old_type
        self.tree.nodes.clear()
        if self.tree.tree_id in UpdateTree._tree_catch:
            UpdateTree.reset_tree(self.tree)
        bpy.data.node_groups.remove(self.tree)

    def execute_entry(self, source, entry, automatic=False):
        self.ui._sessions[self.session] = dict(
            results=[entry], generation=self.ui._generation,
            tree_pointer=self.tree.as_pointer(), location=(300, 0),
            items=[('0', entry.label, '', 0)])
        with bpy.context.temp_override(area=self.area, region=self.region):
            return bpy.ops.node.sv_socket_link_search(
                'EXEC_DEFAULT', session=self.session, choice='0',
                automatic=automatic,
                **self.ui._source_kwargs(source))

    def test_preference_changes_poll_without_restart(self):
        with bpy.context.temp_override(area=self.area, region=self.region):
            self.preferences.link_drag_search = False
            self.assertFalse(self.ui.SvObserveLinkDrag.poll(bpy.context))
            self.preferences.link_drag_search = True
            self.assertTrue(self.ui.SvObserveLinkDrag.poll(bpy.context))
        prop = self.preferences.bl_rna.properties['link_drag_search']
        self.assertFalse(prop.is_skip_save)

    def test_disabled_preference_blocks_auto_but_keeps_manual_search(self):
        self.preferences.link_drag_search = False
        source = self.tree.nodes.new('SvScalarMathNodeMK4')
        entry = next(e for e in self.ui.collect_node_type('SvScalarMathNodeMK4')
                     if not e.socket.is_output)
        self.assertEqual(self.execute_entry(source.outputs[0], entry, automatic=True), {'CANCELLED'})
        self.assertEqual(len(self.tree.nodes), 1)
        self.assertEqual(len(self.tree.links), 0)
        self.assertEqual(self.execute_entry(source.outputs[0], entry), {'FINISHED'})
        self.assertEqual(len(self.tree.links), 1)

    def test_selected_output_prevents_native_selection_probe(self):
        # RNA Socket.select is read-only; exact interaction coverage lives in
        # the GUI regression checks. Here verify the guard precedes ALL probes.
        output = SimpleNamespace(select=True)
        fake_tree = SimpleNamespace(nodes=[SimpleNamespace(outputs=[output])])
        with patch.object(self.ui, '_editor_tree', return_value=fake_tree), \
                patch.object(self.ui, '_near_socket_column', side_effect=AssertionError('probe ran')):
            self.assertIsNone(self.ui._pick_socket(bpy.context, 0, 0))
        self.assertTrue(output.select)


    def test_forward_vector_to_list_mask(self):
        source = self.tree.nodes.new('SvVectorMathNodeMK3')
        entry = next(e for e in self.ui.collect_node_type('MaskListNode')
                     if not e.socket.is_output and e.socket.name == 'data')
        self.assertEqual(self.execute_entry(source.outputs[0], entry), {'FINISHED'})
        self.assertEqual(len(self.tree.links), 1)
        target = self.tree.nodes.active
        self.assertEqual(target.bl_idname, 'MaskListNode')
        self.assertEqual(self.tree.links[0].to_socket.name, 'data')
        self.assertEqual(target.outputs['dataTrue'].bl_idname, 'SvVerticesSocket')

    def test_reverse_search_creates_configured_producer(self):
        destination = self.tree.nodes.new('SvScalarMathNodeMK4')
        entry = next(e for e in self.ui.collect_node_type('SvScalarMathNodeMK4')
                     if e.settings == (('current_op', 'SINE'),) and e.socket.is_output)
        self.assertEqual(self.execute_entry(destination.inputs[0], entry), {'FINISHED'})
        self.assertEqual(self.tree.nodes.active.current_op, 'SINE')
        self.assertEqual(len(self.tree.nodes.active.inputs), 1)
        self.assertEqual(self.tree.links[0].to_node, destination)

    def test_failed_creation_rolls_back_and_keeps_selection(self):
        from dataclasses import replace
        source = self.tree.nodes.new('SvScalarMathNodeMK4')
        source.select = True
        self.tree.nodes.active = source
        entry = next(e for e in self.ui.collect_node_type('SvScalarMathNodeMK4')
                     if not e.socket.is_output)
        invalid = replace(entry, socket=replace(entry.socket, name='missing socket'))
        # Blender raises RuntimeError for an operator's ERROR report.
        try:
            self.execute_entry(source.outputs[0], invalid)
        except RuntimeError:
            pass
        self.assertEqual(len(self.tree.nodes), 1)
        self.assertEqual(len(self.tree.links), 0)
        self.assertEqual(self.tree.nodes.active, source)
        self.assertTrue(source.select)

    def test_connected_input_is_preserved(self):
        a = self.tree.nodes.new('SvScalarMathNodeMK4')
        b = self.tree.nodes.new('SvScalarMathNodeMK4')
        self.tree.links.new(a.outputs[0], b.inputs[0])
        entry = next(e for e in self.ui.collect_node_type('SvScalarMathNodeMK4')
                     if e.socket.is_output)
        self.assertEqual(self.execute_entry(b.inputs[0], entry), {'CANCELLED'})
        self.assertEqual(len(self.tree.nodes), 2)
        self.assertEqual(self.tree.links[0].from_node, a)

# ----------------------------------------------------------------------------
# Registered operation profiles
# ----------------------------------------------------------------------------

import unittest

try:
    import bpy
except ImportError:
    bpy = None

from sverchok.utils.sv_link_search import (
    MODE_PROPERTIES, configure_node, describe_socket, operation_variants,
    connection_score, socket_available,
)


ADDED_MODES = {
    'ListFuncNode': 'func_',
    'SvMatrixMathNode': 'operation',
    'SvQuaternionMathNode': 'operation',
    'SvExScalarFieldMathNode': 'operation',
    'SvExVectorFieldMathNode': 'operation',
    'SvStringsToolsNodeMK2': 'current_op',
}


@unittest.skipIf(bpy is None, 'Requires Blender and enabled Sverchok')
class LinkSearchModesTests(unittest.TestCase):
    def setUp(self):
        self.tree = bpy.data.node_groups.new('.SV Link Search Mode Tests', 'SverchCustomTreeType')
        self.tree.sv_process = False
        self.tree.sv_show = False

    def tearDown(self):
        from sverchok.core.update_system import UpdateTree
        from sverchok.core.tasks import tasks
        with self.tree.init_tree():
            self.tree.nodes.clear()
        for task in tuple(tasks._todo):
            if task.tree == self.tree:
                tasks._todo.discard(task)
        if self.tree.tree_id in UpdateTree._tree_catch:
            UpdateTree.reset_tree(self.tree)
        bpy.data.node_groups.remove(self.tree)

    @staticmethod
    def ports(node):
        return tuple((socket.is_output, socket.name, socket.bl_idname)
                     for sockets in (node.inputs, node.outputs) for socket in sockets
                     if socket_available(socket))

    def test_all_operations_come_from_registered_rna(self):
        with self.tree.init_tree():
            for node_type, prop_name in ADDED_MODES.items():
                with self.subTest(node_type=node_type):
                    node = self.tree.nodes.new(node_type)
                    expected = {item.identifier for item in node.bl_rna.properties[prop_name].enum_items if item.identifier}
                    variants = list(operation_variants(node))
                    had_socket_updater = hasattr(node, 'update_sockets')
                    self.assertEqual(MODE_PROPERTIES[node_type], prop_name)
                    self.assertEqual({settings[0][1] for settings, label in variants}, expected)
                    self.assertTrue(all(label for settings, label in variants))
                    for settings, label in variants:
                        with self.subTest(operation=label):
                            configure_node(node, settings)
                            self.assertEqual(getattr(node, prop_name), settings[0][1])
                            self.assertEqual(hasattr(node, 'update_sockets'), had_socket_updater)
                            first = self.ports(node)
                            self.assertTrue(first)
                            configure_node(node, settings)
                            self.assertEqual(self.ports(node), first)
                    self.tree.nodes.remove(node)

    def test_matrix_unary_and_basis_sockets(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('SvMatrixMathNode')
            configure_node(node, (('operation', 'INVERT'),))
            self.assertEqual([s.name for s in node.inputs], ['A'])
            self.assertEqual([s.name for s in node.outputs], ['C'])
            configure_node(node, (('operation', 'BASIS'),))
            self.assertEqual({s.name for s in node.outputs}, {'C', 'X', 'Y', 'Z'})
            configure_node(node, (('operation', 'MULTIPLY'),))
            self.assertEqual([s.name for s in node.inputs], ['A', 'B'])
            self.assertEqual([s.name for s in node.outputs], ['C'])

    def test_list_math_compatibility_cleanup_after_invalid_mode(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('ListFuncNode')
            had_socket_updater = hasattr(node, 'update_sockets')
            with self.assertRaises((TypeError, ValueError, RuntimeError)):
                configure_node(node, (('func_', '__MISSING_OPERATION__'),))
            self.assertEqual(hasattr(node, 'update_sockets'), had_socket_updater)

    def test_quaternion_operation_changes_output_type(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('SvQuaternionMathNode')
            configure_node(node, (('operation', 'DOT'),))
            self.assertEqual([(s.name, s.bl_idname) for s in node.outputs if socket_available(s)],
                             [('Value', 'SvStringsSocket')])
            configure_node(node, (('operation', 'NORMALIZE'),))
            self.assertEqual([s.name for s in node.inputs if socket_available(s)], ['A'])
            self.assertEqual([s.name for s in node.outputs if socket_available(s)], ['Quaternion'])

    def test_scalar_field_unary_hides_second_input(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('SvExScalarFieldMathNode')
            configure_node(node, (('operation', 'SIN'),))
            self.assertEqual([s.name for s in node.inputs if socket_available(s)], ['FieldA'])
            configure_node(node, (('operation', 'ADD'),))
            self.assertEqual([s.name for s in node.inputs if socket_available(s)], ['FieldA', 'FieldB'])

    def test_vector_field_scalar_output_is_not_a_vector_output(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('SvExVectorFieldMathNode')
            configure_node(node, (('operation', 'NORM'),))
            outputs = [s for s in node.outputs if socket_available(s)]
            self.assertEqual(len(outputs), 1)
            self.assertEqual(outputs[0].bl_idname, 'SvScalarFieldSocket')
            norm = describe_socket(outputs[0], list(node.outputs).index(outputs[0]))
            configure_node(node, (('operation', 'ADD'),))
            vector_input = describe_socket(node.inputs[0], 0)
            self.assertIsNone(connection_score(norm, vector_input))

    def test_string_tools_switches_between_text_and_number(self):
        with self.tree.init_tree():
            node = self.tree.nodes.new('SvStringsToolsNodeMK2')
            configure_node(node, (('current_op', 'to_number'),))
            self.assertEqual(node.outputs[0].bl_idname, 'SvStringsSocket')
            self.assertEqual(len(node.inputs), 1)
            configure_node(node, (('current_op', 'upper'),))
            self.assertEqual(node.outputs[0].bl_idname, 'SvTextSocket')
            self.assertEqual(len(node.inputs), 1)
            configure_node(node, (('current_op', 'replace'),))
            self.assertEqual(len(node.inputs), 4)
            self.assertEqual(node.inputs[-1].bl_idname, 'SvStringsSocket')

    def test_catalogue_sockets_match_recreated_operations(self):
        from sverchok.ui import sv_link_search
        from sverchok.utils.sv_link_search import find_socket
        with self.tree.init_tree():
            for node_type in ADDED_MODES:
                entries = sv_link_search.collect_node_type(node_type)
                self.assertTrue(entries, node_type)
                for entry in entries:
                    with self.subTest(node_type=node_type, operation=entry.operation,
                                      socket=entry.socket.name):
                        node = self.tree.nodes.new(node_type)
                        configure_node(node, entry.settings)
                        self.assertIsNotNone(find_socket(node, entry.socket))
                        for prop_name, identifier in entry.settings:
                            self.assertEqual(getattr(node, prop_name), identifier)
                        self.tree.nodes.remove(node)

    def test_operator_creates_every_operation_in_both_directions(self):
        import uuid
        from sverchok.ui import sv_link_search as ui
        area = bpy.context.screen.areas[0]
        old_type = area.type
        old_tree_type = old_tree = None
        if old_type == 'NODE_EDITOR':
            old_tree_type = area.spaces.active.tree_type
            old_tree = area.spaces.active.node_tree
        area.type = 'NODE_EDITOR'
        area.spaces.active.tree_type = 'SverchCustomTreeType'
        area.spaces.active.node_tree = self.tree
        region = next(r for r in area.regions if r.type == 'WINDOW')
        session_key = uuid.uuid4().hex
        try:
            for node_type in ADDED_MODES:
                entries = ui.collect_node_type(node_type)
                selected = {}
                for entry in entries:
                    selected.setdefault((entry.settings, entry.socket.is_output), entry)
                for (settings, reverse), entry in selected.items():
                    with self.subTest(node_type=node_type, operation=entry.operation, reverse=reverse):
                        with self.tree.init_tree():
                            self.tree.nodes.clear()
                            fixture = self.tree.nodes.new('ListJoinNode')
                            sockets = fixture.inputs if reverse else fixture.outputs
                            source = sockets[0].replace_socket(entry.socket.socket_type)
                        ui._sessions[session_key] = dict(
                            results=[entry], items=[('0', entry.label, entry.node_type, 0)],
                            generation=ui._generation, tree_pointer=self.tree.as_pointer(),
                            location=(300, 0))
                        with bpy.context.temp_override(area=area, region=region):
                            result = bpy.ops.node.sv_socket_link_search(
                                'EXEC_DEFAULT', session=session_key, choice='0',
                                **ui._source_kwargs(source))
                        self.assertEqual(result, {'FINISHED'})
                        created = self.tree.nodes.active
                        self.assertEqual(created.bl_idname, node_type)
                        for prop_name, identifier in settings:
                            self.assertEqual(getattr(created, prop_name), identifier)
                        self.assertEqual(len(self.tree.links), 1)
                        link = self.tree.links[0]
                        self.assertEqual(link.from_node if reverse else link.to_node, created)
                        self.assertEqual(link.to_node if reverse else link.from_node, fixture)
        finally:
            ui._sessions.pop(session_key, None)
            area.spaces.active.node_tree = None
            if old_type == 'NODE_EDITOR':
                area.spaces.active.tree_type = old_tree_type
                area.spaces.active.node_tree = old_tree
            else:
                area.type = old_type

# ----------------------------------------------------------------------------
# Query ranking, groups, configured copies and connection rollback
# ----------------------------------------------------------------------------

import unittest

try:
    import bpy
except ImportError:
    bpy = None

from sverchok.utils.sv_link_search import query_score


class QueryRelevanceTests(unittest.TestCase):
    def test_exact_beats_typo_and_alias(self):
        self.assertLess(query_score('bevel', 'Bevel vertices'), query_score('bevel', 'Level'))
        self.assertIsNotNone(query_score('bebel', 'Bevel vertices'))
        self.assertIsNotNone(query_score('inverse', 'Matrix Invert'))
        self.assertIsNotNone(query_score('sqrt', 'Scalar Math Square Root'))
        self.assertIsNone(query_score('unrelated', 'Bevel vertices'))


@unittest.skipIf(bpy is None, 'Requires Blender')
class LinkSearchContextTests(unittest.TestCase):
    def setUp(self):
        self.tree = bpy.data.node_groups.new('.Link Search fixture', 'SverchCustomTreeType')
        self.tree.sv_process = False
        self.area = bpy.context.screen.areas[0]
        self.old_type = self.area.type
        self.old_tree = self.area.spaces.active.node_tree if self.old_type == 'NODE_EDITOR' else None
        self.area.type = 'NODE_EDITOR'
        self.area.spaces.active.tree_type = 'SverchCustomTreeType'
        self.area.spaces.active.node_tree = self.tree
        self.region = next(r for r in self.area.regions if r.type == 'WINDOW')
        self.groups = []

    def tearDown(self):
        from sverchok.core.update_system import UpdateTree
        from sverchok.core.tasks import tasks
        from sverchok.ui import sv_link_search as base
        base._sessions.pop('context-fixture', None)
        self.area.spaces.active.path.clear()
        self.area.spaces.active.node_tree = self.old_tree
        self.area.type = self.old_type
        with self.tree.init_tree():
            self.tree.nodes.clear()
        for tree in [self.tree] + self.groups:
            for task in tuple(tasks._todo):
                if task.tree == tree:
                    tasks._todo.discard(task)
            if tree.tree_id in UpdateTree._tree_catch:
                UpdateTree.reset_tree(tree)
            bpy.data.node_groups.remove(tree)

    def group(self, name='Geometry group'):
        group = bpy.data.node_groups.new(name, 'SvGroupTree')
        self.groups.append(group)
        group.interface.new_socket('Vertices', in_out='INPUT', socket_type='SvVerticesSocket')
        group.interface.new_socket('Edges', in_out='INPUT', socket_type='SvStringsSocket')
        group.interface.new_socket('Vertices', in_out='OUTPUT', socket_type='SvVerticesSocket')
        return group

    def execute(self, source, entry, single=False):
        from sverchok.ui import sv_link_search as base
        base._sessions['context-fixture'] = dict(results=[entry],
            items=[('0', entry.label, entry.node_type, 0)], generation=base._generation,
            tree_pointer=source.id_data.as_pointer(), location=(100, 100))
        with bpy.context.temp_override(area=self.area, region=self.region):
            return bpy.ops.node.sv_socket_link_search('EXEC_DEFAULT', session='context-fixture',
                choice='0', single_link=single, **base._source_kwargs(source))

    def test_full_replace_bundle_and_failure_restore(self):
        from sverchok.utils import sv_link_search_extensions as ext
        old = self.tree.nodes.new('SvBoxNodeMk2')
        new = self.tree.nodes.new('SvBoxNodeMk2')
        target = self.tree.nodes.new('SvBevelNodeMK2')
        for output, name in [('Vers', 'vertices'), ('Edgs', 'edges'), ('Pols', 'polygons')]:
            self.tree.links.new(old.outputs[output], target.inputs[name])
        entries = ext.existing_entries(self.tree, new.outputs['Vers'])
        entry = next(e for e in entries if e.node_name == target.name and e.socket.name == 'vertices' and e.replace_all)
        self.assertIn('Replace V+E+P', entry.label)
        notify = ext._update_connected_tree
        try:
            def fail(*args):
                raise RuntimeError('Intentional bundle failure')
            ext._update_connected_tree = fail
            with self.assertRaises(RuntimeError):
                ext.connect_existing(self.tree, new.outputs['Vers'], entry)
        finally:
            ext._update_connected_tree = notify
        self.assertEqual(len(self.tree.links), 3)
        self.assertTrue(all(link.from_node == old for link in self.tree.links))
        # Rollback recreates links, so request fresh authorization metadata.
        entry = next(e for e in ext.existing_entries(self.tree, new.outputs['Vers'])
                     if e.node_name == target.name and e.socket.name == 'vertices' and e.replace_all)
        self.assertEqual(ext.connect_existing(self.tree, new.outputs['Vers'], entry), 3)
        self.assertTrue(all(link.from_node == new for link in self.tree.links))

    def test_group_creation_and_interface_change(self):
        from sverchok.utils.sv_link_search_extensions import group_entries, create_context_node
        group = self.group()
        source = self.tree.nodes.new('SvBoxNodeMk2')
        entry = next(e for e in group_entries(self.tree) if e.group_name == group.name and not e.socket.is_output and e.socket.name == 'Vertices')
        self.assertEqual(self.execute(source.outputs['Vers'], entry), {'FINISHED'})
        self.assertEqual(self.tree.nodes.active.node_tree, group)
        group.interface.new_socket('Changed', in_out='INPUT', socket_type='SvStringsSocket')
        with bpy.context.temp_override(area=self.area, region=self.region):
            with self.assertRaises(RuntimeError):
                create_context_node(bpy.context, self.tree, entry)

    def test_nested_group_edit_and_recursion_filter(self):
        from sverchok.ui import sv_link_search as base
        from sverchok.utils.sv_link_search_extensions import group_entries, group_allowed
        inner = self.group('Inner')
        outer = self.group('Outer')
        with outer.init_tree():
            nested = outer.nodes.new('SvGroupTreeNode')
            nested.group_tree = inner
        self.assertFalse(group_allowed(outer, inner))
        self.assertFalse(group_allowed(inner, inner))
        owner = self.tree.nodes.new('SvGroupTreeNode')
        owner.group_tree = inner
        self.area.spaces.active.path.append(inner, node=owner)
        inner.group_node_name = owner.name
        with bpy.context.temp_override(area=self.area, region=self.region):
            self.assertEqual(base._editor_tree(bpy.context), inner)
        with inner.init_tree():
            source = inner.nodes.new('NodeGroupInput')
        entry = next(e for e in group_entries(inner) if e.interface_node and not e.socket.is_output)
        # The group has only a Vertices output interface, which is connectable.
        self.assertEqual(self.execute(source.outputs['Vertices'], entry), {'FINISHED'})
        self.assertEqual(len(inner.links), 1)

    def test_configured_interface_copy_without_catalogue_evaluation(self):
        from sverchok.ui import sv_link_search as base
        from sverchok.utils.sv_link_search_extensions import configured_entries
        base.collect_node_type('ListJoinNode')
        template = self.tree.nodes.new('ListJoinNode')
        template.label = 'Configured join'
        template.outputs[0].replace_socket('SvSurfaceSocket')
        target = self.tree.nodes.new('SvFlipSurfaceNode')
        entries = configured_entries(self.tree)
        entry = next(e for e in entries if e.template_name == template.name and e.socket.is_output)
        before = len(self.tree.nodes)
        self.assertEqual(self.execute(target.inputs[0], entry), {'FINISHED'})
        self.assertEqual(len(self.tree.nodes), before + 1)
        self.assertNotEqual(self.tree.nodes.active, template)
        self.assertEqual(target.inputs[0].links[0].from_node, self.tree.nodes.active)

    def test_list_math_callback_works_without_compatibility_patch(self):
        node = self.tree.nodes.new('ListFuncNode')
        node.func_ = 'SUM'
        self.assertEqual(node.func_, 'SUM')
        self.assertIn('Sum', node.label)
        self.assertFalse(hasattr(node, 'update_sockets'))


    def test_script_template_index_does_not_execute_user_code(self):
        from sverchok.ui import sv_link_search as base
        from sverchok.utils.sv_link_search_extensions import configured_entries
        base.collect_node_type('SvScriptNodeLite')
        template = self.tree.nodes.new('SvScriptNodeLite')
        script = bpy.data.texts.new('.Link Search script fixture')
        script.write('"""\nout result s\n"""\nbpy.context.scene["sv_link_search_runs"] = 1 + bpy.context.scene.get("sv_link_search_runs", 0)\nresult = [[1]]\n')
        template.script_name = script.name
        template.script_str = script.as_string()
        try:
            template.update_sockets()
            bpy.context.scene['sv_link_search_runs'] = 0
            entries = configured_entries(self.tree)
            self.assertEqual(bpy.context.scene['sv_link_search_runs'], 0)
            entry = next(e for e in entries if e.template_name == template.name and e.socket.is_output)
            receiver = self.tree.nodes.new('ListJoinNode')
            self.assertEqual(self.execute(receiver.inputs[0], entry), {'FINISHED'})
            self.assertEqual(self.tree.nodes.active.script_name, script.name)
            self.assertGreater(bpy.context.scene['sv_link_search_runs'], 0)
        finally:
            bpy.data.texts.remove(script)
            if 'sv_link_search_runs' in bpy.context.scene:
                del bpy.context.scene['sv_link_search_runs']

    def test_reverse_bundle_replace_and_shift_single(self):
        from sverchok.utils import sv_link_search_extensions as ext
        old = self.tree.nodes.new('SvBoxNodeMk2')
        new = self.tree.nodes.new('SvBoxNodeMk2')
        receiver = self.tree.nodes.new('SvBevelNodeMK2')
        self.tree.links.new(old.outputs['Edgs'], receiver.inputs['edges'])
        entries = ext.existing_entries(self.tree, receiver.inputs['vertices'])
        full = next(e for e in entries if e.node_name == new.name and e.socket.name == 'Vers' and e.replace_all)
        self.assertEqual(ext.connect_existing(self.tree, receiver.inputs['vertices'], full, single_link=True), 1)
        self.assertEqual(receiver.inputs['edges'].links[0].from_node, old)
        self.assertFalse(receiver.inputs['polygons'].is_linked)

    def test_receiver_layout_updated_before_failed_calculation(self):
        from sverchok.utils.sv_link_search import SearchEntry, describe_socket
        from sverchok.ui import sv_link_search as base
        receiver = self.tree.nodes.new('ListJoinNode')
        cls = type(receiver)
        process = cls.process
        updates = []
        update = cls.update
        try:
            def fail(node):
                raise RuntimeError('Intentional producer calculation failure')
            def record(node):
                updates.append(node.as_pointer())
                return update(node)
            cls.process = fail
            cls.update = record
            entry = next(e for e in base.collect_node_type('SvScalarMathNodeMK4') if e.socket.is_output)
            self.assertEqual(self.execute(receiver.inputs[0], entry), {'FINISHED'})
            self.assertIn(receiver.as_pointer(), updates)
            self.assertGreaterEqual(len(receiver.inputs), 2)
        finally:
            cls.process = process
            cls.update = update

    def test_new_exact_result_supersedes_fuzzy_until_navigation(self):
        from sverchok.ui import sv_link_search as base, sv_link_search_popup as popup
        from sverchok.utils.sv_link_search import SearchEntry, describe_socket
        source = self.tree.nodes.new('SvBoxNodeMk2').outputs['Vers']
        info = describe_socket(source, 0)
        fuzzy = SearchEntry('SvBevelNodeMK2', 'Level', '', (), info.__class__(
            'Vertices', 'SvVerticesSocket', False, 'Vertices', 0, 'vertices'))
        exact = SearchEntry('SvBevelNodeMK2', 'Bevel', '', (), fuzzy.socket)
        session = dict(results=[], items=[], search_text=[], entry_modes=[], entry_hints=[],
            visible=[], query=popup.Query(), active=-1, offset=0, keyboard=True,
            source_info=info, source_ports=())
        session['query'].insert('bevel')
        popup._append_entry(session, fuzzy, 'new')
        popup._filter(session)
        popup._append_entry(session, exact, 'new')
        popup._filter(session)
        self.assertEqual(session['active'], 1)
        popup._move_selection(session, 1)
        self.assertEqual(session['active'], 0)
        popup._filter(session)
        self.assertEqual(session['active'], 0)



# Link Search: idle scheduling and click-filter regression tests.
import unittest as _link_search_unittest
class LinkSearchPerformanceTests(_link_search_unittest.TestCase):
    def setUp(self):
        from collections import deque
        from contextlib import ExitStack
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        from sverchok.ui import sv_link_search as ui
        self.ui = ui
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.registered = set()
        self.live = set()
        self.preference = False
        self.timers = SimpleNamespace(
            is_registered=lambda fn: fn in self.registered,
            register=Mock(side_effect=lambda fn, **kw: self.registered.add(fn)),
            unregister=Mock(side_effect=lambda fn: self.registered.remove(fn)))
        self.fake_bpy = SimpleNamespace(
            context=SimpleNamespace(window_manager=SimpleNamespace(
                keyconfigs=SimpleNamespace(addon=None))),
            app=SimpleNamespace(background=False, timers=self.timers,
                handlers=SimpleNamespace(load_post=[])),
            types=SimpleNamespace(),
            utils=SimpleNamespace(register_class=Mock(), unregister_class=Mock()),
            ops=SimpleNamespace(node=SimpleNamespace(select=Mock())))
        self.stack.enter_context(patch.multiple(ui,
            bpy=self.fake_bpy,
            sys=SimpleNamespace(modules={'sverchok.ui.sv_link_search_popup': SimpleNamespace(_live=self.live)}),
            _enabled=True, _signature=('Dummy',), _ready=False, _catalogue_forced=False,
            _entries=[], _pending=['Dummy'], _active_variants=deque(),
            _active_node_type=None, _catalogue_revision=0, _generation=0,
            _sessions={}, _keymaps=[], _deferred=set(),
            link_drag_search_enabled=lambda context: self.preference,
            available_node_types=Mock(return_value=('Dummy',)),
            _node_variants=Mock(return_value=(((), 'Default'),)),
            collect_node_type=Mock(return_value=['metadata'])))
        self.stack.enter_context(patch('sverchok.utils.sv_link_search_extensions.clear_metadata'))

    def test_disabled_startup_has_no_catalogue_timer(self):
        self.ui.register()
        self.assertFalse(self.registered)
        self.ui.available_node_types.assert_not_called()

    def test_enabled_startup_schedules_warmup(self):
        self.preference = True
        self.ui.register()
        self.assertIn(self.ui._catalogue_tick, self.registered)
        self.ui.available_node_types.assert_not_called()

    def test_disabled_callback_does_not_inspect_or_create_nodes(self):
        self.ui._signature = None
        self.assertIsNone(self.ui._catalogue_tick())
        self.ui.available_node_types.assert_not_called()
        self.ui._node_variants.assert_not_called()
        self.ui.collect_node_type.assert_not_called()

    def test_disabled_file_load_cancels_pending_warmup(self):
        self.registered.add(self.ui._catalogue_tick)
        self.ui._catalogue_forced = True
        self.ui._file_loaded(None)
        self.assertFalse(self.registered)
        self.assertFalse(self.ui._catalogue_forced)
        self.assertIsNone(self.ui._signature)

    def test_background_file_load_never_schedules_automatic_warmup(self):
        self.preference = True
        self.fake_bpy.app.background = True
        self.ui._file_loaded(None)
        self.assertFalse(self.registered)

    def test_manual_search_still_indexes_when_automatic_search_is_disabled(self):
        self.live.add('manual')
        self.ui._sessions['manual'] = {'automatic': False}
        self.assertIsNone(self.ui._catalogue_tick())
        self.assertTrue(self.ui._ready)
        self.assertEqual(self.ui._entries, ['metadata'])
        self.ui.collect_node_type.assert_called_once()

    def test_closing_manual_search_pauses_disabled_indexing(self):
        self.ui._sessions['closed'] = {'automatic': False}
        self.assertIsNone(self.ui._catalogue_tick())
        self.assertEqual(self.ui._pending, ['Dummy'])
        self.ui.collect_node_type.assert_not_called()

    def test_disabled_automatic_popup_cannot_keep_indexing_alive(self):
        self.live.add('automatic')
        self.ui._sessions['automatic'] = {'automatic': True}
        self.assertIsNone(self.ui._catalogue_tick())
        self.ui.collect_node_type.assert_not_called()

    def test_explicit_rebuild_finishes_and_releases_override(self):
        self.ui.ensure_catalogue(force=True)
        self.assertTrue(self.ui._catalogue_forced)
        self.assertIn(self.ui._catalogue_tick, self.registered)
        self.assertIsNone(self.ui._catalogue_tick())
        self.assertTrue(self.ui._ready)
        self.assertFalse(self.ui._catalogue_forced)

    def test_reenabling_search_resumes_paused_work_on_demand(self):
        self.preference = True
        self.ui.ensure_catalogue()
        self.assertIn(self.ui._catalogue_tick, self.registered)
        self.assertIsNone(self.ui._catalogue_tick())
        self.assertTrue(self.ui._ready)

    def test_disabled_click_poll_does_not_scan_the_tree(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        with patch.object(self.ui, '_editor_tree', Mock(side_effect=AssertionError('Unexpected tree scan'))):
            context = SimpleNamespace(region=SimpleNamespace(type='WINDOW'))
            self.assertFalse(self.ui.SvObserveLinkDrag.poll(context))

    @staticmethod
    def empty_tree():
        from types import SimpleNamespace
        return SimpleNamespace(nodes=SimpleNamespace(active=None))

    def test_click_away_from_sockets_does_not_scan_socket_selection(self):
        from unittest.mock import Mock, patch
        with patch.object(self.ui, '_editor_tree', return_value=self.empty_tree()), \
                patch.object(self.ui, '_near_socket_column', return_value=False), \
                patch.object(self.ui, '_has_selected_outputs', Mock(side_effect=AssertionError('Unexpected socket scan'))):
            self.assertIsNone(self.ui._pick_socket(object(), 0, 0))
            self.fake_bpy.ops.node.select.assert_not_called()

    def test_selected_outputs_still_block_native_selection_probe(self):
        from unittest.mock import patch
        with patch.object(self.ui, '_editor_tree', return_value=self.empty_tree()), \
                patch.object(self.ui, '_near_socket_column', return_value=True), \
                patch.object(self.ui, '_has_selected_outputs', return_value=True):
            self.assertIsNone(self.ui._pick_socket(object(), 0, 0))
            self.fake_bpy.ops.node.select.assert_not_called()

    def test_active_selected_output_bypasses_even_the_geometry_scan(self):
        from types import SimpleNamespace
        from unittest.mock import Mock, patch
        active = SimpleNamespace(outputs=[SimpleNamespace(select=True)])
        tree = SimpleNamespace(nodes=SimpleNamespace(active=active))
        with patch.object(self.ui, '_editor_tree', return_value=tree), \
                patch.object(self.ui, '_near_socket_column', Mock(side_effect=AssertionError('Unexpected geometry scan'))):
            self.assertIsNone(self.ui._pick_socket(object(), 0, 0))
            self.fake_bpy.ops.node.select.assert_not_called()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError('Link Search tests failed')
