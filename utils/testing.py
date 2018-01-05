
import bpy
from os.path import dirname, basename, join
import unittest
import json
from io import StringIO

import sverchok
from sverchok.utils.logging import debug, info
from sverchok.utils.context_managers import sv_preferences

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

def create_node_tree(name=None):
    """
    Create new Sverchok node tree in the scene.
    """
    if name is None:
        name = "TestingTree"
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
    return bpy.data.node_groups[tree_name].nodes[node_name]

def nodes_are_equal(actual, reference):
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
            raise AssertionError("Property `{}' has value `{}' in actual node {}, but in reference it has value `{}'".format(k, actual, reference[k]))

    for k in reference.keys():
        if k not in actual:
            raise AssertionError("Property `{}' is present in reference node, but is not present in actual node {}".format(k, actual))

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

    loader = unittest.TestLoader()
    start_dir = get_tests_path()
    suite = loader.discover(start_dir = start_dir, pattern = "*_tests.py")
    buffer = StringIO()
    runner = unittest.TextTestRunner(stream = buffer, verbosity=2)
    result = runner.run(suite)
    info("Test cases result:\n%s", buffer.getvalue())
    return result

class SverchokTestCase(unittest.TestCase):
    """
    Base class for Sverchok test cases.
    """

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

    def assert_json_equals(self, actual_json, expected_json):
        """
        Assert that two JSON objects are equal.
        Comparasion is done by serializing both objects.
        """
        actual_data = self.serialize_json(actual_json)
        expected_data = self.serialize_json(expected_json)
        self.assertEquals(actual_data, expected_data)

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

    def link_node_tree(self):
        path = self.get_reference_file_path()
        link_node_tree(path)
        return get_or_create_node_tree()

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

