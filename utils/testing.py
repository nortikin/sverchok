
import bpy
from os.path import dirname, basename, join
import unittest
import json

import sverchok
from sverchok.utils.logging import debug
from sverchok.utils.context_managers import sv_preferences

#test_modules = ["box1"]

def generate_node_definition(node):
    result = """
tree = get_or_create_node_tree()
node = create_node("{}", tree.name)
""".format(node.bl_idname)
    
    for k, v in node.items():
        result += "node.{} = {}\n".format(k, v)

    return result

def get_node_editor_context():
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
    if name is None:
        name = "TestingTree"
    debug("Creating tree: %s", name)
    return bpy.data.node_groups.new(name=name, type="SverchCustomTreeType")

def get_or_create_node_tree(name=None):
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        debug("Using existing tree: %s", name)
        return bpy.data.node_groups[name]
    else:
        return create_node_tree(name)

def remove_node_tree(name=None):
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

def create_node(node_type, tree_name=None):
    if tree_name is None:
        tree_name = "TestingTree"
    debug("Creating node of type %s", node_type)
    return bpy.data.node_groups[tree_name].nodes.new(type=node_type)

def get_node(node_name, tree_name=None):
    if tree_name is None:
        tree_name = "TestingTree"
    return bpy.data.node_groups[tree_name].nodes[node_name]

def nodes_are_equal(actual, reference):
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

def run_all_tests():
    loader = unittest.TestLoader()
    sv_init = sverchok.__file__
    start_dir = join(dirname(sv_init), "tests")
    suite = loader.discover(start_dir = start_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

class SimpleExportTest(unittest.TestCase):
    def setUp(self):
        self.tree = get_or_create_node_tree()

    def tearDown(self):
        remove_node_tree()

    def serialize_json(self, data):
        return json.dumps(data, sort_keys=True, indent=2)

    def assert_json_equals(self, actual_json, expected_json):
        actual_data = self.serialize_json(actual_json)
        expected_data = self.serialize_json(expected_json)
        self.assertEquals(actual_data, expected_data)

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
            raise Exception("Some tests failed")
        sys.exit(0)
    except Exception as e:
        print(e)
        sys.exit(1)

