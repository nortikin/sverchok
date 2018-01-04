
import bpy

def generate_node_definition(node):
    result = """
get_or_create_node_tree()
node = create_node("{}")
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

