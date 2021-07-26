"""
This module does:
1. Get json from the sverchok/json_examples folder if there is json with the same name
   in sverchok/tests/expected_tree_data folder
2. Import json into a new tree
3. Execute the tree
4. Extract values from most right nodes in the tree
5. Compare them with values from the expected_tree_data folder and raise an error if necessary
6. Save coverage information into expected_tree_data/last_coverage.json
"""
from collections import defaultdict, namedtuple, Generator
from functools import reduce
from pathlib import Path
from statistics import mean
import json
from zipfile import ZipFile

from bpy.types import Node

import sverchok
from sverchok.core.main_tree_handler import tree_updater
from sverchok.utils.testing import SverchokTestCase
from sverchok.utils.sv_json_import import JSONImporter
from sverchok.utils.sv_data_to_json import save_to_json
from sverchok.utils.modules_inspection import iter_classes_from_module
from sverchok import nodes
from sverchok.utils.handle_blender_data import BlNode
from sverchok.ui.sv_examples_menu import example_categories_names
from sverchok.tests.json_import_tests import UNITTEST_SKIPLIST
from sverchok.dependencies import scipy

DataPaths = namedtuple('DataPaths', ['example_path', 'data_path'])
DEPENDENCIES = {'Concave_sverchok.json': scipy}


class ExamplesImportTest(SverchokTestCase):

    def setUp(self):
        self.coverage = Coverage()

    def test_persistence_node_out_data(self):
        for paths in self.get_paths():
            with self.temporary_node_tree("ImportedTree") as new_tree, self.subTest(tree=paths.example_path.name):
                if paths.example_path.name in DEPENDENCIES and DEPENDENCIES[paths.example_path.name] is None:
                    self.skipTest(f"{paths.example_path.name} is skipped - some library is not available")
                importer = JSONImporter.init_from_path(str(paths.example_path))
                importer.import_into_tree(new_tree, print_log=False)
                if importer.has_fails and paths.example_path.name not in UNITTEST_SKIPLIST:
                    raise(ImportError(importer.fail_massage))

                execute_tree(new_tree)
                struct = save_to_json(new_tree)
                with ZipFile(paths.data_path) as zip_file:
                    with zip_file.open(paths.example_path.name.rsplit('.', 1)[0] + '.json') as file:
                        standard = json.load(file)
                self.compare_data(standard, struct, f'\n{paths.example_path.name}')
                self.coverage.update(new_tree)

    def tearDown(self):
        self.coverage.save()

    def compare_data(self, expected, res, msg=''):
        """It assumes that data in sequences has persistent type"""
        if isinstance(expected, dict):
            for key, d1 in expected.items():
                d2 = res[key]
                self.compare_data(d1, d2, msg + ' -> ' + key if msg else key)
        elif isinstance(expected, (list, tuple)):
            if expected and isinstance(expected[0], (list, tuple, dict)):
                for i, d1 in enumerate(expected):
                    self.compare_data(d1, res[i], msg)
            elif expected and isinstance(expected[0], float):
                for i, d1 in enumerate(expected):
                    self.assertAlmostEqual(d1, res[i], 5, f'{msg}\nExpected: {expected}\nResult: {res}')
            elif expected and isinstance(expected[0], (int, str)):
                for i, d1 in enumerate(expected):
                    self.assertEqual(d1, res[i], f'{msg}\nExpected: {expected}\nResult: {res}')
            elif expected:
                raise TypeError(f'Data has unsupported type: {type(expected[0])}')
            else:
                self.assertListEqual(expected, res)
        elif isinstance(expected, (int, str)):
            self.assertEqual(expected, res, f'{msg}Expected: {expected}Result: {res}')
        elif isinstance(expected, float):
            self.assertAlmostEqual(res, res, 5, f'{msg}Expected: {expected}Result: {res}')
        else:
            raise TypeError(f'Data has unsupported type: {type(expected)}|{msg}')

    def get_paths(self) -> Generator[DataPaths]:
        expected_data_path = Path(sverchok.__file__).parent / 'tests/expected_tree_data'
        expected_names = {p.name.rsplit('.', 1)[0] for p in expected_data_path.iterdir()}
        unused_names = expected_names.copy()
        for examples_path, category_name in example_categories_names():
            for json_path in (examples_path / category_name).iterdir():
                file_name = json_path.name.rsplit('.', 1)[0]
                if file_name in expected_names:
                    if file_name in unused_names:
                        unused_names.remove(file_name)
                    yield DataPaths(json_path, expected_data_path / (file_name + '.zip'))
        self.assertSetEqual(unused_names, set(),
                            "There are unused expected tree data files - should be removed or used")


class Coverage:
    def __init__(self):
        self._struct = {
            'coverage': '0.00%',
            'nodes_tested': 0,
            'nodes': dict(),
        }
        node_classes = iter_classes_from_module(nodes, (Node,))
        self._node_idnames = [c.bl_idname for c in node_classes]

    def update(self, tree):
        for bl_node in tree.nodes:
            node_struct = self._update_node_stats(bl_node, self._struct['nodes'].get(bl_node.bl_idname))
            self._struct['nodes'][bl_node.bl_idname] = node_struct
        self._struct['nodes'] = dict(sorted(self._struct['nodes'].items()))
        nodes_coverage = len(self._struct['nodes']) / len(self._node_idnames)
        average_node_coverage = mean(float(n['coverage'].rstrip('%')) / 100 for n in self._struct['nodes'].values())
        self._struct['coverage'] = f"{round(nodes_coverage * average_node_coverage * 100, 2)}%"
        self._struct['nodes_tested'] = len(self._struct['nodes'])

    def save(self):
        with open(Path(sverchok.__file__).parent / 'tests/last_coverage.json', 'w') as file:
            json.dump(self._struct, file, indent=2)

    @staticmethod
    def _update_node_stats(bl_node, struct=None) -> dict:
        default_struct = {
            'coverage': f'0.00%',
            'modes': defaultdict(int)
        }
        struct = struct if struct is not None else default_struct
        node = BlNode(bl_node)
        mode = '|'.join(f'{p.name}:{p.value}' for p in node.properties if p.type in {'ENUM', 'BOOLEAN'})
        if mode:  # empty string in case the node does not have properties
            struct['modes'][mode] += 1

        prop_num = (2 if p.type == 'BOOLEAN' else len(p.enum_items) or 1 if p.type == 'ENUM' else 1
                    for p in node.properties)
        possible_comb = reduce(lambda x, y: x * y, prop_num, 1)
        struct['coverage'] = f'{round((len(struct["modes"]) or 1) / possible_comb * 100, 2)}%'
        return struct


def execute_tree(tree):
    """This is a little beat hacky but for test purposes it's not so bad"""
    executor = tree_updater(tree)
    try:
        while True:
            next(executor)
    except StopIteration:
        pass
