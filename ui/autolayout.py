import collections

import bpy
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty


class SvAutoLayoutPanel(Panel):
    bl_idname = "SvAutoLayoutPanel"
    bl_label = "Autolayout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.tree_type == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        layout = self.layout
        layout.label("Autolayout options")
        for key in SvAutoLayoutOp.order_funcs.keys():
            layout.operator("node.sverchok_autolayout", text=key).func_name = key

def update_value(self, context):
    tree = context.space_data.edit_tree
    order_nodes_2(tree, self.x_spread)

class SvAutoLayoutOp(Operator):
    """Sort layout"""
    bl_idname = "node.sverchok_autolayout"
    bl_label = "Sort layout"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        try:
            return context.space_data.tree_type == 'SverchCustomTreeType'
        except:
            return False

    x_spread = FloatProperty(default=300, soft_min=0, update=update_value)
    func_name = StringProperty(default="Topo up")

    order_funcs = {"Topo up": order_nodes_1,
                   "Topo down": order_nodes_2,
                }

    def execute(self, context):
        func = self.order_funcs.get(self.func_name)
        tree = context.space_data.edit_tree
        if func:
            func(tree, self.x_spread)
            return {'FINISHED'}
        else:
            print("no func {}".format(self.func_name))
            return {'CANCELLED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



def topo_sort(nodes, links, start):
    """
    nodes = [], list of nodes
    links = {node: [node0, node1, ..., nodeN]}
    """
    node_count = len(nodes)
    weights = collections.defaultdict(lambda : -1)
    def visit(node, weight):
        weights[node] = max(weight, weights[node])
        for from_node, link_weight in links[node]:
            visit(from_node, weight + link_weight)
    visit(start, 0)
    return sorted(weights.items(), key= lambda x:x[1])

def collect_links_up(ng, weight_func=lambda n0, n1: 1):
    rawlinks = [(l.from_node.name, l.to_node.name) for l in ng.links]
    links = collections.defaultdict(list)
    for l in ng.links:
        from_node = l.from_node
        to_node = l.to_node
        weight = weight_func(from_node, to_node)
        links[to_node].append((from_node, weight))
    from_set = {from_node for from_node, _ in rawlinks}
    to_set = {to_node for _, to_node in rawlinks}
    return links, from_set, to_set


def collect_links_down(ng, weight_func=lambda n0, n1: 1):
    rawlinks = [(l.to_node.name, l.from_node.name) for l in ng.links]
    links = collections.defaultdict(list)
    for l in ng.links:
        from_node = l.to_node
        to_node = l.from_node
        weight = weight_func(from_node, to_node)
        links[to_node.name].append((from_node.name, weight))
    from_set = {from_node for from_node, _ in rawlinks}
    to_set = {to_node for _, to_node in rawlinks}
    return links, from_set, to_set

def add_weights(links, from_set, to_set):
    f, t = from_set, to_set
    nodes = list(f | t)
    tot_weights = [topo_sort(nodes, links, start) for start in (t - f)]
    out = collections.defaultdict(lambda :0)
    for res in tot_weights:
        #print(res)
        for node, weight in res:
            out[node] = max(weight, out[node])
        #print(sorted(out.items(), key=lambda x:x[1]))
    return out

def order_nodes_1(ng, delta=300):
    weights = add_weights(*collect_links_up(ng))
    max_x = max(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    y_count = [0 for n in range(len(ng.nodes))]
    for node, weight in weights.items():
        x = max_x - weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        ng.nodes[node].location = (x, y)

def order_nodes_2(ng, delta=300):
    weights = add_weights(*collect_links_down(ng))
    min_x = min(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    y_count = [0 for n in range(len(ng.nodes))]
    for node, weight in weights.items():
        x = min_x + weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        ng.nodes[node].location = (x, y)

classes = [
    SvAutoLayoutOp,
    SvAutoLayoutPanel
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
