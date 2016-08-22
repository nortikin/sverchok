import collections

import bpy
from bpy.types import Panel, Operator
from bpy.props import FloatProperty


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
        op = layout.operator("node.sverchok_autolayout")
        layout.prop(op, "x_spread")

def update_value(self, context):
    tree = context.space_data.edit_tree
    order_nodes(tree, self.x_spread)

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

    def execute(self, context):
        print(dir(context))
        tree = context.space_data.edit_tree
        order_nodes(tree, self.x_spread)
        return {'FINISHED'}

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
        for from_node in links[node]:
            visit(from_node, weight + 1)
    visit(start, 0)
    return sorted(weights.items(), key= lambda x:x[1])

def collect_links(ng):
    rawlinks = [(l.from_node.name, l.to_node.name) for l in ng.links]
    links = collections.defaultdict(list)
    for from_node, to_node in rawlinks:
        links[to_node].append(from_node)
    from_set = {from_node for from_node, _ in rawlinks}
    to_set = {to_node for _, to_node in rawlinks}
    return links, from_set, to_set

def generate_weights(ng):
    links, f, t = collect_links(ng)
    nodes = list(f | t)
    tot_weights = [topo_sort(nodes, links, start) for start in (t - f)]
    out = collections.defaultdict(lambda :0)
    for res in tot_weights:
        print(res)
        for node, weight in res:
            out[node] = max(weight, out[node])
        print(sorted(out.items(), key=lambda x:x[1]))
    return out

def order_nodes(ng, delta=300):
    weights = generate_weights(ng)
    max_x = max(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    y_count = [0 for n in range(len(ng.nodes))]
    for node, weight in weights.items():
        x = max_x - weight * delta
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
