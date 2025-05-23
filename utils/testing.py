from pathlib import Path
from typing import Iterator

import bpy
from bpy.types import NodeTree
import os
from os.path import dirname, basename, join
import unittest
import unittest.mock
import json
from io import StringIO
import logging
from contextlib import contextmanager
import ast

import sverchok
from sverchok import old_nodes
from sverchok.data_structure import get_data_nesting_level
from sverchok.core.socket_data import get_output_socket_data
from sverchok.core.sv_custom_exceptions import SvNoDataError
from sverchok.utils.sv_json_import import JSONImporter


sv_logger = logging.getLogger('sverchok.testing')


@contextmanager
def only_test_logs():
    def filter_test_logs(record: logging.LogRecord):
        """Turnoff all other than test logs"""
        return record.name.startswith('sverchok.testing')

    root_loger = logging.getLogger('sverchok')
    for handler in root_loger.handlers:
        handler.addFilter(filter_test_logs)
    try:
        yield
    finally:
        for handler in root_loger.handlers:
            handler.removeFilter(filter_test_logs)


try:
    import coverage
    coverage_available = True
except ImportError:
    # sv_logger.info("Coverage module is not installed")
    coverage_available = False

##########################################
# Utility methods
##########################################

@contextmanager
def coverage_report():
    if not coverage_available:
        yield None
    else:
        try:
            cov = coverage.Coverage()
            cov.start()
            yield cov
        finally:
            cov.stop()
            cov.save()
            cov.html_report()

def generate_node_definition(node):
    """
    Generate code that programmatically creates specified node.
    This works only for simple cases.
    """

    result = """
tree = get_or_create_node_tree()
node = create_node("{}", tree.name)
""".format(node.bl_idname)
    
    for k, v in node.items():
        result += "node.{} = {}\n".format(k, v)

    return result

def get_node_editor_context():
    """
    Prepare context override for bpy operators that need context.
    """
    win      = bpy.context.window
    scr      = win.screen
    areas  = [area for area in scr.areas if area.type == 'NODE_EDITOR']
    region   = [region for region in areas[0].regions if region.type == 'WINDOW']

    context = {'window':win,
                'screen':scr,
                'area'  :areas[0],
                'region':region,
                'scene' :bpy.context.scene,
                'space': areas[0].spaces[0]
                }
    return context

def create_node_tree(name=None, must_not_exist=True):
    """
    Create new Sverchok node tree in the scene.
    If must_not_exist == True (default), then it is checked that
    the tree with such name did not exist before. If it exists,
    an exception is raised.
    If must_not_exist == False, then new tree will be created anyway,
    but it can be created with another name (standard Blender's renaming).
    """
    if name is None:
        name = "TestingTree"
    if must_not_exist:
        if name in bpy.data.node_groups:
            raise Exception("Will not create tree `{}': it already exists".format(name))
    sv_logger.debug("Creating tree: %s", name)
    tree = bpy.data.node_groups.new(name=name, type="SverchCustomTreeType")
    tree.sv_process = False  # turn off auto processing tree by default
    return tree

def get_or_create_node_tree(name=None):
    """
    Create new Sverchok node tree or reuse existing one.
    """
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        sv_logger.debug("Using existing tree: %s", name)
        return bpy.data.node_groups[name]
    else:
        return create_node_tree(name)

def get_node_tree(name=None):
    """
    Return existing node tree, or raise an exception if there is no such.
    """
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        sv_logger.debug("Using existing tree: %s", name)
        return bpy.data.node_groups[name]
    else:
        raise Exception("There is no node tree named `{}'".format(name))

def remove_node_tree(name=None):
    """
    Remove existing Sverchok node tree.
    """
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        win      = bpy.context.window
        scr      = win.screen
        areas  = [area for area in scr.areas if area.type == 'NODE_EDITOR']
        if len(areas):
            space = areas[0].spaces[0]
            space.node_tree = None
        sv_logger.debug("Removing tree: %s", name)
        tree = bpy.data.node_groups[name]
        bpy.data.node_groups.remove(tree)


def remove_all_trees():
    """Remove all trees"""
    while True:
        try:
            bpy.data.node_groups.remove(bpy.data.node_groups[0])
        except IndexError:
            break


def link_node_tree(reference_blend_path, tree_name=None):
    """
    Link node tree from specified .blend file.
    """
    if tree_name is None:
        tree_name = "TestingTree"
    if tree_name in bpy.data.node_groups:
        raise Exception("Tree named `{}' already exists in current scene".format(tree_name))
    with bpy.data.libraries.load(reference_blend_path, link=True) as (data_src, data_dst):
        sv_logger.debug(f"---- Linked node tree: {basename(reference_blend_path)}")
        data_dst.node_groups = [tree_name]
    # right here the update method of the imported tree will be called
    # sverchok does not have a way of preventing this update
    # make sure that all old nodes was registered


def link_text_block(reference_blend_path, block_name):
    """
    Link text block from specified .blend file.
    """

    with bpy.data.libraries.load(reference_blend_path, link=True) as (data_src, data_dst):
        sv_logger.debug(f"---- Linked text block: {basename(reference_blend_path)}")
        data_dst.texts = [block_name]

def create_node(node_type, tree_name=None):
    """
    Create Sverchok node by it's bl_idname.
    """
    if tree_name is None:
        tree_name = "TestingTree"
    sv_logger.debug("Creating node of type %s", node_type)
    return bpy.data.node_groups[tree_name].nodes.new(type=node_type)

def get_node(node_name, tree_name=None):
    """
    Return existing node.
    """
    if tree_name is None:
        tree_name = "TestingTree"
    if tree_name not in bpy.data.node_groups:
        raise Exception("There is no node tree named `{}'".format(tree_name))
    return bpy.data.node_groups[tree_name].nodes[node_name]

def get_tests_path():
    """
    Return path to all test cases (tests/ directory).
    """
    sv_init = sverchok.__file__
    tests_dir = join(dirname(sv_init), "tests")
    return tests_dir

def run_all_tests(pattern=None, log_file = 'sverchok_tests.log', log_level = None, verbosity=2, failfast=False):
    """
    Run all existing test cases.
    Test cases are looked up under tests/ directory.
    """
    
    if pattern is None:
        pattern = "*_tests.py"

    if log_level is not None:
        sv_logger.setLevel(log_level)

    tests_path = get_tests_path()
    log_handler = logging.FileHandler(join(tests_path, log_file), mode='w')
    logging.getLogger().addHandler(log_handler)
    try:
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir = tests_path, pattern = pattern)
        buffer = StringIO()
        runner = unittest.TextTestRunner(stream = buffer, verbosity=verbosity, failfast=failfast)
        old_nodes.register_all()
        with coverage_report(), only_test_logs():
            sv_logger.warning("Run all tests with log level=[%s]",
                              logging.getLevelName(sv_logger.getEffectiveLevel()))
            result = runner.run(suite)
            sv_logger.info("Test cases result:\n%s", buffer.getvalue())
            return result
    finally:
        logging.getLogger().removeHandler(log_handler)


def run_test_from_file(file_name):
    """
    Run test from file given by name. File should be places in tests folder
    :param file_name: string like avl_tree_tests.py
    :return: result
    """
    tests_path = get_tests_path()
    log_handler = logging.FileHandler(join(tests_path, "sverchok_tests.log"), mode='w')
    logging.getLogger().addHandler(log_handler)
    buffer = None
    try:
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=tests_path, pattern=file_name)
        buffer = StringIO()
        runner = unittest.TextTestRunner(stream=buffer, verbosity=2)
        old_nodes.register_all()
        result = runner.run(suite)
        sv_logger.info("Test cases result:\n%s", buffer.getvalue())
        return result
    finally:
        logging.getLogger().removeHandler(log_handler)
        return buffer.getvalue().split('\n')[-2] if buffer else "Global error"


""" using:
from sverchok.utils.testing import run_test_from_file
run_test_from_file("avl_tree_tests.py")
"""


##############################################
# Base test case classes
##############################################

class SverchokTestCase(unittest.TestCase):
    """
    Base class for Sverchok test cases.
    """

    def setUp(self):
        sv_logger.debug("Starting test: %s", self.id())

    @contextmanager
    def temporary_node_tree(self, new_tree_name):
        """
        Context manager for dealing with new temporary node tree.
        The tree is created on entering context and removed when
        exiting context. Example of usage:

        with self.temporary_node_tree("TempTree") as tmp:
            do_something(tree)
        """
        new_tree = create_node_tree(new_tree_name)
        try:
            yield new_tree
        finally:
            remove_node_tree(new_tree_name)

    @contextmanager
    def tree_from_file(self, file_name: str, tree_name: str) -> Iterator[NodeTree]:
        path = join(get_tests_path(), "references", file_name)
        link_node_tree(path, tree_name)
        try:
            yield get_node_tree(tree_name)
        finally:
            remove_node_tree(tree_name)

    def getLogger(self):
        return logging.getLogger(self.__class__.__name__)

    def debug(self, *args):
        self.getLogger().debug(*args)

    def info(self, *args):
        self.getLogger().info(*args)

    def serialize_json(self, data):
        """
        Serialize JSON object in standard format.
        """
        return json.dumps(data, sort_keys=True, indent=2)

    def store_reference_json(self, file_name, json_data):
        """
        Store JSON data for further reference.
        """
        with open(self.get_reference_file_path(file_name), 'wb') as f:
            data = json.dumps(json_data).encode('utf8')
            f.write(data)

    def get_reference_file_path(self, file_name):
        return join(get_tests_path(), "references", file_name)

    def load_reference_sverchok_data(self, file_name):
        """
        Load reference data in Sverchok format
        (plain Python syntax of nested lists).
        Returns: Sverchok data (nested lists).
        """
        with open(self.get_reference_file_path(file_name), 'r') as f:
            data = f.read()
            return ast.literal_eval(data)

    def store_reference_sverchok_data(self, file_name, data):
        """
        Store reference data in Sverchok format
        (plain Python syntax of nested lists).
        """
        with open(self.get_reference_file_path(file_name), 'w') as f:
            f.write(repr(data))

    def assert_json_equals(self, actual_json, expected_json):
        """
        Assert that two JSON objects are equal.
        Comparison is done by serializing both objects.
        """
        actual_data = self.serialize_json(actual_json)
        expected_data = self.serialize_json(expected_json)
        self.assertEqual(actual_data, expected_data)

    def assert_json_equals_file(self, actual_json, expected_json_file_name):
        """
        Assert that actual_json equals to JSON stored in expected_json_file_name.
        """
        with open(self.get_reference_file_path(expected_json_file_name), 'rb') as f:
            data = f.read().decode('utf8')
            expected_result = json.loads(data)
            self.assert_json_equals(actual_json, expected_result)

    def assert_node_property_equals(self, tree_name, node_name, property_name, expected_value):
        """
        Assert that named property of the node equals to specified value.
        """
        node = get_node(node_name, tree_name)
        actual_value = getattr(node, property_name)
        self.assertEqual(actual_value, expected_value)

    def assert_node_input_equals(self, tree_name, node_name, input_name, expected_value):
        node = get_node(node_name, tree_name)
        actual_value = node.inputs[input_name].sv_get()
        self.assertEqual(actual_value, expected_value)

    def assert_nodes_linked(self, tree_name, node1_name, node1_output_name, node2_name, node2_input_name):
        """
        Assert that certain output of node1 is linked to certain input of node2.
        """
        node1 = get_node(node1_name, tree_name)
        node2 = get_node(node2_name, tree_name)

        if node1_output_name not in node1.outputs:
            raise AssertionError("Node `{}' does not have output named `{}'".format(node1_name, node1_output_name))
        if node2_input_name not in node2.inputs:
            raise AssertionError("Node `{}' does not have input named `{}'".format(node2_name, node2_input_name))

        if not node1.outputs[node1_output_name].is_linked:
            raise AssertionError("Output `{}' of node `{}' is not linked to anything", node1_output_name, node1_name)
        if not node2.inputs[node2_input_name].is_linked:
            raise AssertionError("Input `{}' of node `{}' is not linked to anything", node2_input_name, node2_name)

        self.assertEqual(node1.outputs[node1_output_name].other, node2.inputs[node2_input_name])

    def assert_nodes_are_equal(self, actual, reference):
        """
        Assert that two nodes have the same settings.
        This works only for simple nodes.
        """
        if actual.bl_idname != reference.bl_idname:
            raise AssertionError("Actual node {} has bl_idname `{}', but reference has `{}'".format(actual, actual.bl_idname, reference.bl_idname))
        for k, v in actual.items():
            if k not in reference:
                raise AssertionError("Property `{}' is present is actual node {}, but is not present in reference".format(k, actual))
            if v != reference[k] and k != 'n_id':
                raise AssertionError("Property `{}' has value `{}' in actual node {}, but in reference it has value `{}'".format(k, v, actual, reference[k]))

        for k in reference.keys():
            if k not in actual:
                raise AssertionError("Property `{}' is present in reference node, but is not present in actual node {}".format(k, actual))

    def assert_node_equals_file(self, actual_node, reference_node_name, reference_file_name, imported_tree_name=None):
        """
        Assert that actual_node equals to node named reference_node_name imported from file reference_file_name.
        This works only for simple nodes.
        """
        if imported_tree_name is None:
            imported_tree_name = "ImportedTree"

        try:
            new_tree = get_or_create_node_tree(imported_tree_name)
            importer = JSONImporter.init_from_path(self.get_reference_file_path(reference_file_name))
            importer.import_into_tree(new_tree, print_log=False)
            self.assert_nodes_are_equal(actual_node, get_node(reference_node_name, imported_tree_name))
        finally:
            remove_node_tree(imported_tree_name)

    def assert_numpy_arrays_equal(self, arr1, arr2, precision=None, fail_fast=True):
        """
        Assert that two numpy arrays are equal.
        Floating-point numbers are compared with specified precision.
        """
        if arr1.shape != arr2.shape:
            raise AssertionError("Shape of 1st array {} != shape of 2nd array {}".format(arr1.shape, arr2.shape))
        shape = list(arr1.shape)
        fails = []

        def compare(prev_indicies):
            step = len(prev_indicies) 
            if step == arr1.ndim:
                ind = tuple(prev_indicies)
                if precision is None:
                    a1 = arr1[ind]
                    a2 = arr2[ind]
                else:
                    a1 = round(arr1[ind], precision)
                    a2 = round(arr2[ind], precision)

                if fail_fast:
                    self.assertEqual(a1, a2, "Array 1 [{}] != Array 2 [{}]".format(ind, ind))
                else:
                    if a1 != a2:
                        fails.append((a1, a2, ind))
            else:
                for idx in range(shape[step]):
                    new_indicies = prev_indicies[:]
                    new_indicies.append(idx)
                    compare(new_indicies)

        compare([])
        if not fail_fast and fails:
            messages = []
            for a1, a2, ind in fails:
                message = f"{a1} != {a2}: Array 1 [{ind}] != Array 2 [{ind}]"
                messages.append(message)
            header = f"{len(fails)} fails of {arr1.size} comparisons:\n"
            message = header + "\n".join(messages)
            self.fail(message)

    def assert_sverchok_data_equal(self, data1, data2, precision=None, message=None):
        """
        Assert that two arrays of Sverchok data (nested tuples or lists)
        are equal.
        Floating-point numbers are compared with specified precision.
        """
        def format_message(text):
            if message is None:
                return text
            else:
                return f"{text}: {message}"

        level1 = get_data_nesting_level(data1)
        level2 = get_data_nesting_level(data2)
        if level1 != level2:
            raise AssertionError(format_message(f"Nesting level of 1st data {level1} != nesting level of 2nd data {level2}"))
        
        def do_assert(d1, d2, idxs):
            if precision is not None:
                d1 = round(d1, precision)
                d2 = round(d2, precision)
            self.assertEqual(d1, d2, format_message(f"Data 1 [{idxs}] != Data 2 [{idxs}]"))

        if level1 == 0:
            do_assert(data1, data2, [])
            return

        def compare(prev_indicies, item1, item2):
            step = len(prev_indicies)
            index = prev_indicies[-1]
            if step == level1:
                if index >= len(item1):
                    raise AssertionError(format_message(f"At {prev_indicies}: index {index} >= length of Item 1: {item1}"))
                if index >= len(item2):
                    raise AssertionError(format_message(f"At {prev_indicies}: index {index} >= length of Item 2: {item2}"))
                do_assert(item1[index], item2[index], prev_indicies)
            else:
                l1 = len(item1)
                l2 = len(item2)
                self.assertEqual(l1, l2, format_message(f"Size of data 1 at level {step} != size of data 2"))
                for next_idx in range(len(item1[index])):
                    new_indicies = prev_indicies[:]
                    new_indicies.append(next_idx)
                    compare(new_indicies, item1[index], item2[index])

        for idx in range(len(data1)):
            compare([idx], data1, data2)

    def assert_sverchok_data_equals_file(self, data, expected_data_file_name, precision=None):
        expected_data = self.load_reference_sverchok_data(expected_data_file_name)
        # sv_logger.info("Data: %s", data)
        # sv_logger.info("Expected data: %s", expected_data)
        self.assert_sverchok_data_equal(data, expected_data, precision=precision)
        #self.assertEqual(data, expected_data)
    
    def assert_dicts_equal(self, first, second, precision=None):
        keys1 = set(first.keys())
        keys2 = set(second.keys())
        if keys1 != keys2:
            raise AssertionError(f"Keys of first dictionary {keys1} do not match to keys of the second dictionary {keys2}")
        for key in first.keys():
            value1 = first[key]
            value2 = second[key]
            self.assert_sverchok_data_equal(value1, value2, precision=precision, message=f"Values for dictionary key {key} do not match")


    @contextmanager
    def assert_prints_stdout(self, regexp):
        """
        Assert that the code prints something matching regexp to stdout.
        Usage:

            with self.assert_prints_stdout("hello"):
                print("hello world")

        """
        with unittest.mock.patch('sys.stdout', new=StringIO()) as fake_stdout:
            yield fake_stdout
            self.assertRegex(fake_stdout.getvalue(), regexp)

    @contextmanager
    def assert_not_prints_stdout(self, regexp):
        """
        Assert that the code does not print anything matching regexp to stdout.
        Usage:

            with self.assert_not_prints_stdout("hello"):
                print("goodbye")

        """
        with unittest.mock.patch('sys.stdout', new=StringIO()) as fake_stdout:
            yield fake_stdout
            self.assertNotRegex(fake_stdout.getvalue(), regexp)

    @contextmanager
    def assert_logs_no_errors(self):
        """
        Assert that the code does not write any ERROR to the log.
        Usage:

            with self.assert_logs_no_errors():
                sv_logger.info("this is just an information, not error")

        """

        has_errors = False

        class Handler(logging.Handler):
            def emit(self, record):
                nonlocal has_errors
                if record.levelno >= logging.ERROR:
                    has_errors = True

        handler = Handler()
        logging.getLogger().addHandler(handler)

        try:
            sv_logger.debug("=== \/ === [%s] Here should be no errors === \/ ===", self.__class__.__name__)
            yield handler
            self.assertFalse(has_errors, "There were some errors logged")
        finally:
            sv_logger.debug("=== /\ === [%s] There should be no errors === /\ ===", self.__class__.__name__)
            logging.getLogger().handlers.remove(handler)

    def subtest_assert_equals(self, value1, value2, message=None):
        """
        The same as assertEqual(), but within subtest.
        Use this to do several assertions per test method,
        for case test execution not to be stopped at
        the first failure.
        """

        with self.subTest():
            self.assertEqual(value1, value2, message)


class EmptyTreeTestCase(SverchokTestCase):
    """
    Base class for test cases, that work on empty node tree.
    At setup, it creates new node tree (it becomes available as self.tree).
    At teardown, it removes created node tree.
    """

    def setUp(self):
        super().setUp()
        self.tree = get_or_create_node_tree()

    def tearDown(self):
        remove_node_tree()
        super().tearDown()

class ReferenceTreeTestCase(SverchokTestCase):
    """
    Base class for test cases, that require existing node tree
    for their work.
    At setup, this class links a node tree from specified .blend
    file into current scene. Name of .blend (or better .blend.gz)
    file must be specified in `reference_file_name` property
    of inherited class. Name of linked tree can be specified
    in `reference_tree_name' property, by default it is "TestingTree".
    The linked node tree is available as `self.tree'.
    At teardown, this class removes that tree from scene.
    """

    reference_file_name = None
    reference_tree_name = None

    def get_reference_file_path(self, file_name=None):
        if file_name is None:
            file_name = self.reference_file_name
        return join(get_tests_path(), "references", file_name)

    def link_node_tree(self, tree_name=None):
        if tree_name is None:
            tree_name = self.reference_tree_name
        path = self.get_reference_file_path()
        link_node_tree(path, tree_name)
        return get_node_tree(tree_name)

    def link_text_block(self, block_name):
        link_text_block(self.get_reference_file_path(), block_name)

    def setUp(self):
        super().setUp()
        if self.reference_file_name is None:
            raise Exception("ReferenceTreeTestCase subclass must have `reference_file_name' set")
        if self.reference_tree_name is None:
            self.reference_tree_name = "TestingTree"

        with self.assert_logs_no_errors():
            self.tree = self.link_node_tree()

    def tearDown(self):
        remove_all_trees()  # node trees can include references to many other trees
        super().tearDown()

class NodeProcessTestCase(EmptyTreeTestCase):
    """
    Base class for test cases that test process() function
    of one single node.
    At setup, this class creates an empty node tree and one
    node in it. bl_idname of tested node must be specified in
    `node_bl_idname' property of child test case class.
    Optionally, some simple nodes can be created (by default
    a Note node) and connected to some outputs of tested node.
    This is useful for nodes that return from process() if they
    see that nothing is linked to outputs.

    In actual test_xxx() method, the test case should call
    self.node.process(), and after that examine output of the
    node by either self.get_output_data() or self.assert_output_data_equals().

    At teardown, the whole tested node tree is deleted.
    """

    node_bl_idname = None
    connect_output_sockets = None
    output_node_bl_idname = "NoteNode"

    def get_output_data(self, output_name):
        """
        Return data that tested node has written to named output socket.
        Returns None if it hasn't written any data.
        """
        try:
            return get_output_socket_data(self.node, output_name)
        except SvNoDataError:
            return None
    
    def assert_output_data_equals(self, output_name, expected_data, message=None):
        """
        Assert that tested node has written expected_data to
        output socket output_name.
        """
        data = self.get_output_data(output_name)
        self.assertEqual(data, expected_data, message)

    def assert_output_data_equals_file(self, output_name, expected_data_file_name, message=None):
        """
        Assert that tested node has written expected data to
        output socket output_name.
        Expected data is stored in reference file expected_data_file_name.
        """
        data = self.get_output_data(output_name)
        expected_data = self.load_reference_sverchok_data(expected_data_file_name)
        self.assert_sverchok_data_equal(data, expected_data, message=message)

    def setUp(self):
        super().setUp()

        if self.node_bl_idname is None:
            raise Exception("NodeProcessTestCase subclass must have `node_bl_idname' set")

        self.node = create_node(self.node_bl_idname)

        if self.connect_output_sockets and self.output_node_bl_idname:
            for output_name in self.connect_output_sockets:
                out_node = create_node(self.output_node_bl_idname)
                self.tree.links.new(self.node.outputs[output_name], out_node.inputs[0])

######################################################
# Test running conditionals
######################################################

def is_pull_request():
    """
    Return True if we are running a build for pull-request check on Travis CI.
    """
    pull_request = os.environ.get("TRAVIS_PULL_REQUEST", None)
    return (pull_request is not None and pull_request != "false")

def is_integration_server():
    """
    Return True if we a running inside an integration server (Travis CI) build.
    """
    ci = os.environ.get("CI", None)
    return (ci == "true")

def get_ci_branch():
    """
    If we are running inside an integration server build, return
    the name of git branch which we are checking.
    Otherwise, return None.
    """
    branch = os.environ.get("TRAVIS_BRANCH", None)
    print("Branch:", branch)
    return branch

def make_skip_decorator(condition, message):
    def decorator(func):
        if condition():
            return unittest.skip(message)(func)
        else:
            return func

    return decorator

# Here go decorators used to mark test to be executed only in certain conditions.
# Example usage:
#       
#       @manual_only
#       def test_something(self):
#           # This test will not be running on Travis CI, only in manual mode.
#

pull_requests_only = make_skip_decorator(is_pull_request, "Applies only to PR builds")
skip_pull_requests = make_skip_decorator(lambda: not is_pull_request(), "Does not apply to PR builds")
manual_only = make_skip_decorator(lambda: not is_integration_server(), "Applies for manual builds only")

def branches_only(*branches):
    """
    This test should be only executed for specified branches:

        @branches_only("master")
        def test_something(self):
            ...

    Please note that this applies only for Travis CI builds,
    in manual mode this test will be ran anyway.
    """
    return make_skip_decorator(lambda: get_ci_branch() not in branches, "Does not apply to this branch")

def batch_only(func):
    """
    Decorator for tests that are to be executed in batch mode only
    (i.e. when tests are run from command line, either locally or in CI
    environment). Usage:

        @batch_only
        def test_something(self):
            ...
    """
    if bpy.app.background:
        return func
    else:
        return unittest.skip("This test is intended for batch mode only")(func)

def interactive_only(func):
    """
    Decorator for tests that are to be executed in interactive mode only
    (i.e. when tests are run from Blender's UI with "Run all tests" button).
    Usage:

        @interactive_only
        def test_something(self):
            ...
    """
    if not bpy.app.background:
        return func
    else:
        return unittest.skip("This test is intended for interactive mode only")(func)

def requires(module):
    return unittest.skipIf(module is None, "This test requires a module which is not currently available")


if __name__ == "__main__":
    import sys
    import argparse
    try:
        #register()
        argv = sys.argv
        if bpy.app.binary_path:
            argv = argv[argv.index("--")+1:]
        else:
            argv = argv[1:]

        parser = argparse.ArgumentParser(prog = "testing.py", description = "Run Sverchok tests")
        parser.add_argument('pattern', metavar='*.PY', nargs='?', default = '*_tests.py', help="Test case files pattern")
        #parser.add_argument('-t', '--test', nargs='+', default = argparse.SUPPRESS)
        parser.add_argument('-o', '--output', metavar='FILE.log', default='sverchok_tests.log', help="Path to output log file")
        parser.add_argument('-f', '--fail-fast', action='store_true', help="Stop after first failing test")
        parser.add_argument('-v', '--verbose', action='count', default=2, help="Set the verbosity level")
        parser.add_argument('-q', '--quiet', dest='verbose', action='store_const', const=0, help="Be quiet")
        parser.add_argument('--debug', dest='log_level', action='store_const', const='DEBUG', help="Enable debug logging")
        parser.add_argument('--info', dest='log_level', action='store_const', const='INFO', help="Log only information messages")

        args = parser.parse_args(argv)
        #print(args)

        if not bpy.app.binary_path:
            bpy.ops.wm.read_userpref()

        log_level = getattr(args, 'log_level', None)
        result = run_all_tests(pattern = args.pattern,
                    log_file = args.output,
                    log_level = log_level,
                    verbosity = args.verbose,
                    failfast = args.fail_fast)
        if not result.wasSuccessful():
            # We have to raise an exception for Blender to exit with specified exit code.
            raise Exception("Some tests failed")
        sys.exit(0)
    except Exception as e:
        sv_logger.exception(e)
        sys.exit(1)

