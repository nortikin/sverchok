
import bpy
from os.path import dirname, basename, join
import unittest
import json
from io import StringIO
import logging
from contextlib import contextmanager

import sverchok
from sverchok.utils.logging import debug, info
from sverchok.utils.context_managers import sv_preferences
from sverchok.utils.sv_IO_panel_tools import import_tree

##########################################
# Utility methods
##########################################

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
    debug("Creating tree: %s", name)
    return bpy.data.node_groups.new(name=name, type="SverchCustomTreeType")

def get_or_create_node_tree(name=None):
    """
    Create new Sverchok node tree or reuse existing one.
    """
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        debug("Using existing tree: %s", name)
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
        debug("Using existing tree: %s", name)
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
        space = areas[0].spaces[0]
        space.node_tree = None
        debug("Removing tree: %s", name)
        tree = bpy.data.node_groups[name]
        bpy.data.node_groups.remove(tree)

def link_node_tree(reference_blend_path, tree_name=None):
    """
    Link node tree from specified .blend file.
    """
    if tree_name is None:
        tree_name = "TestingTree"
    if tree_name in bpy.data.node_groups:
        raise Exception("Tree named `{}' already exists in current scene".format(tree_name))
    with bpy.data.libraries.load(reference_blend_path, link=True) as (data_src, data_dst):
        data_dst.node_groups = [tree_name]

def link_text_block(reference_blend_path, block_name):
    """
    Link text block from specified .blend file.
    """

    with bpy.data.libraries.load(reference_blend_path, link=True) as (data_src, data_dst):
        data_dst.texts = [block_name]

def create_node(node_type, tree_name=None):
    """
    Create Sverchok node by it's bl_idname.
    """
    if tree_name is None:
        tree_name = "TestingTree"
    debug("Creating node of type %s", node_type)
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

def run_all_tests():
    """
    Run all existing test cases.
    Test cases are looked up under tests/ directory.
    """

    tests_path = get_tests_path()
    log_handler = logging.FileHandler(join(tests_path, "sverchok_tests.log"), mode='w')
    logging.getLogger().addHandler(log_handler)
    try:
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir = tests_path, pattern = "*_tests.py")
        buffer = StringIO()
        runner = unittest.TextTestRunner(stream = buffer, verbosity=2)
        result = runner.run(suite)
        info("Test cases result:\n%s", buffer.getvalue())
        return result
    finally:
        logging.getLogger().removeHandler(log_handler)

##############################################
# Base test case classes
##############################################

class SverchokTestCase(unittest.TestCase):
    """
    Base class for Sverchok test cases.
    """

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

    def assert_json_equals(self, actual_json, expected_json):
        """
        Assert that two JSON objects are equal.
        Comparasion is done by serializing both objects.
        """
        actual_data = self.serialize_json(actual_json)
        expected_data = self.serialize_json(expected_json)
        self.assertEquals(actual_data, expected_data)

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
            if v != reference[k]:
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
            import_tree(new_tree, self.get_reference_file_path(reference_file_name))
            self.assert_nodes_are_equal(actual_node, get_node(reference_node_name, imported_tree_name))
        finally:
            remove_node_tree(imported_tree_name)

class EmptyTreeTestCase(SverchokTestCase):
    """
    Base class for test cases, that work on empty node tree.
    At setup, it creates new node tree (it becomes available as self.tree).
    At teardown, it removes created node tree.
    """

    def setUp(self):
        self.tree = get_or_create_node_tree()

    def tearDown(self):
        remove_node_tree()

class ReferenceTreeTestCase(SverchokTestCase):

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
        if self.reference_file_name is None:
            raise Exception("ReferenceTreeTestCase subclass must have `reference_file_name' set")
        if self.reference_tree_name is None:
            self.reference_tree_name = "TestingTree"
        
        self.tree = self.link_node_tree()

    def tearDown(self):
        remove_node_tree()

######################################################
# UI operator and panel classes
######################################################

class SvRunTests(bpy.types.Operator):
    """
    Run all tests.
    """

    bl_idname = "node.sv_testing_run_all_tests"
    bl_label = "Run all tests"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        run_all_tests()
        return {'FINISHED'}

class SvDumpNodeDef(bpy.types.Operator):
    """
    Print definition of selected node to stdout.
    This works correctly only for simple cases!
    """

    bl_idname = "node.sv_testing_dump_node_def"
    bl_label = "Dump node definition"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        ntree = context.space_data.node_tree
        selection = list(filter(lambda n: n.select, ntree.nodes))
        if len(selection) != 1:
            self.report({'ERROR'}, "Exactly one node must be selected!")
            return {'CANCELLED'}

        node = selection[0]
        print(generate_node_definition(node))
        self.report({'INFO'}, "See console")

        return {'FINISHED'}

class SvTestingPanel(bpy.types.Panel):
    bl_idname = "SvTestingPanel"
    bl_label = "Testing"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            if context.space_data.edit_tree.bl_idname != 'SverchCustomTreeType':
                return False
            with sv_preferences() as prefs:
                return prefs.developer_mode
        except:
            return False

    def draw(self, context):
        layout = self.layout
        layout.operator("node.sv_testing_run_all_tests")
        layout.operator("node.sv_testing_dump_node_def")

classes = [SvRunTests, SvDumpNodeDef, SvTestingPanel]

def register():
    for clazz in classes:
        bpy.utils.register_class(clazz)

def unregister():
    for clazz in reversed(classes):
        bpy.utils.unregister_class(clazz)

if __name__ == "__main__":
    import sys
    try:
        register()
        result = run_all_tests()
        if not result.wasSuccessful():
            # We have to raise an exception for Blender to exit with specified exit code.
            raise Exception("Some tests failed")
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)

