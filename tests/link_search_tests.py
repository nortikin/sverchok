# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
import uuid

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

    def execute_entry(self, source, entry):
        self.ui._sessions[self.session] = dict(
            results=[entry], generation=self.ui._generation,
            tree_pointer=self.tree.as_pointer(), location=(300, 0),
            items=[('0', entry.label, '', 0)])
        with bpy.context.temp_override(area=self.area, region=self.region):
            return bpy.ops.node.sv_socket_link_search(
                'EXEC_DEFAULT', session=self.session, choice='0',
                **self.ui._source_kwargs(source))

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


if __name__ == '__main__':
    unittest.main()
