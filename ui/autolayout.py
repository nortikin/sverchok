import collections
import time

import bpy
from bpy.types import Panel, Operator
from bpy.props import FloatProperty, StringProperty, IntProperty, EnumProperty
from mathutils import Vector

from sverchok.utils.sv_easing_functions import easing_dict

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
        links[to_node.name].append((from_node.name, weight))
    from_set = {from_node for from_node, _ in rawlinks}
    to_set = {to_node for _, to_node in rawlinks}
    return links, list(from_set|to_set), to_set - from_set


def collect_links_down(ng, weight_func=lambda n0, n1: 1):
    rawlinks = [(l.from_node.name, l.to_node.name) for l in ng.links]
    links = collections.defaultdict(list)
    for l in ng.links:
        from_node = l.from_node
        to_node = l.to_node
        weight = weight_func(from_node, to_node)
        links[from_node.name].append((to_node.name, weight))
    from_set = {from_node for from_node, _ in rawlinks}
    to_set = {to_node for _, to_node in rawlinks}
    return links, list(from_set|to_set), from_set - to_set

def add_weights(links, nodes, start_nodes):
    print(start_nodes)
    tot_weights = [topo_sort(nodes, links, start) for start in start_nodes]
    out = collections.defaultdict(lambda :0)
    for res in tot_weights:
        #print(res)
        for node, weight in res:
            out[node] = max(weight, out[node])
        #print(sorted(out.items(), key=lambda x:x[1]))
    return out

new_locs = {}
old_locs = {}


def order_nodes_1(ng, delta=300):
    global new_locs
    global old_locs
    old_locs = {n.name:n.location for n in ng.nodes}
    new_locs = {}
    weights = add_weights(*collect_links_up(ng))
    max_x = max(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    y_count = [0 for n in range(len(ng.nodes))]
    for node, weight in weights.items():
        x = max_x - weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        new_locs[node] = Vector((x, y))

def order_nodes_2(ng, delta=300):
    global new_locs
    global old_locs
    old_locs = {n.name:n.location for n in ng.nodes}
    new_locs = {}
    weights = add_weights(*collect_links_down(ng))
    min_x = min(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    y_count = [0 for n in range(len(ng.nodes))]
    for node, weight in weights.items():
        x = min_x + weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        new_locs[node] = Vector((x, y))

def order_nodes_3(ng, delta=300):
    global new_locs
    global old_locs
    old_locs = {n.name:n.location for n in ng.nodes}
    new_locs = {}
    weights_down = add_weights(*collect_links_down(ng))
    weights_up = add_weights(*collect_links_up(ng))
    _, nodes, __ = collect_links_up(ng)
    weights = {}
    max_val = max(weights_down.values())
    min_x = min(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    for node in nodes:
        w_d = weights_down[node]
        w_u = max_val - weights_up[node]
        weight = int(round((w_d + w_u) / 2, 0))
        weights[node] = weight
    y_count = [0 for n in range(max_val + 1)]
    for node, weight in weights.items():
        x = min_x + weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        new_locs[node] = Vector((x, y))

def order_nodes_3(ng, delta=300):
    global new_locs
    global old_locs
    old_locs = {n.name:n.location for n in ng.nodes}
    new_locs = {}
    weights_down = add_weights(*collect_links_down(ng))
    weights_up = add_weights(*collect_links_up(ng))
    _, nodes, __ = collect_links_up(ng)
    weights = {}
    max_val = max(weights_down.values())
    min_x = min(n.location.x for n in ng.nodes)
    max_y = max(n.location.y for n in ng.nodes)
    
    for node in nodes:
        w_d = weights_down[node]
        w_u = max_val - weights_up[node]
        weight = int(round((w_d + w_u) / 2, 0))
        weights[node] = weight
    y_count = [0 for n in range(max_val + 1)]
    def key_value(node):
        return -old_locs[node].y
    for node in sorted(weights.keys(), key=key_value):
        weight = weights[node]
        x = min_x + weight * delta
        y = max_y - y_count[weight] * delta
        y_count[weight] += 1
        new_locs[node] = Vector((x, y))




class SvAutoLayoutPanel(Panel):
    bl_idname = "SvAutoLayoutPanel"
    bl_label = "Autolayout"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sverchok'
    use_pin = True

    @classmethod
    def poll(cls, context):
        return True
        try:
            return context.space_data.tree_type == 'SverchCustomTreeType'
        except:
            return False

    def draw(self, context):
        layout = self.layout
        layout.label("Autolayout options")
        for key in SvAutoLayoutOp.order_funcs.keys():
            layout.operator("wm.sverchok_autolayout", text=key).func_name = key

def update_value(self, context):
    tree = context.space_data.edit_tree
    order_nodes_2(tree, self.x_spread)



easing_items = [(str(k), f.__name__, f.__name__) for k, f in easing_dict.items()]
start_time = 0

class SvAutoLayoutTween(Operator):

    """Operator which runs its self from a timer"""
    bl_idname = "wm.sverchok_autolayout"
    bl_label = "tween auto layout"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR'


    x_spread = FloatProperty(default=300, soft_min=0)
    func_name = StringProperty(default="Topo up")

    order_funcs = {
                   "Topo up":   order_nodes_1,
                   "Topo down": order_nodes_2,
                   "Topo avg":  order_nodes_3,
                   }


    _timer = None
    mode = StringProperty(default='')
    _start_time = None
    duration = IntProperty(default=2, min=1, max=10)
    speed = FloatProperty(default=1 / 13)
    easing_key = EnumProperty(items=easing_items, default="1")

    def get_easing_func(self):
        return easing_dict[int(self.easing_key)]

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "speed")
        layout.prop(self, "duration")
        layout.prop(self, "easing_key")
        layout.prop(self, "x_spread")

    # causes a crash
    #def invoke(self, context, event):
    #    return context.window_manager.invoke_props_dialog(self)

    def modal(self, context, event):
        #print(dir(event))

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if start_time + self.duration < time.perf_counter():
            print("FINISHED, cancelling")
            self.cancel(context)
            return {'FINISHED'}

        if not (event.type == 'TIMER'):
            #print("not time resign")
            return {'PASS_THROUGH'}


        t = (time.perf_counter() - start_time)/self.duration

        #print("t", t)
        easing_func = self.get_easing_func()
        for node in context.space_data.edit_tree.nodes:
            new_loc = new_locs[node.name]
            old_loc = old_locs[node.name]
            current_loc = old_loc.lerp(new_loc, easing_func(t))
            node.location = current_loc

        return {'PASS_THROUGH'}


    def execute(self, context):
        global start_time
        wm = context.window_manager
        self._timer = wm.event_timer_add(self.speed, context.window)
        #print(self._timer)
        start_time = time.perf_counter()
        wm.modal_handler_add(self)

        func = self.order_funcs.get(self.func_name)
        tree = context.space_data.edit_tree

        func(tree, self.x_spread)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)


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

    order_funcs = {
                   "Topo up":   order_nodes_1,
                   "Topo down": order_nodes_2,
                   "Topo avg":  order_nodes_3,
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





classes = [
    SvAutoLayoutOp,
    SvAutoLayoutPanel,
    SvAutoLayoutTween
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
