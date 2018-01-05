
import bpy

from sverchok.utils.context_managers import sv_preferences

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
    return bpy.data.node_groups.new(name=name, type="SverchCustomTreeType")

def get_or_create_node_tree(name=None):
    if name is None:
        name = "TestingTree"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    else:
        return create_node_tree(name)

def create_node(node_type, tree_name=None):
    if tree_name is None:
        tree_name = "TestingTree"
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

class SvRunTests(bpy.types.Operator):
    """
    Run all tests.
    """

    bl_idname = "node.sv_run_all_tests"
    bl_label = "Run all tests"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        pass
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
        layout.operator("node.sv_run_all_tests")

classes = [SvRunTests, SvTestingPanel]

def register():
    for clazz in classes:
        bpy.utils.register_class(clazz)

def unregister():
    for clazz in reversed(classes):
        bpy.utils.unregister_class(clazz)


