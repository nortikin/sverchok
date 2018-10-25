# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import mathutils
from mathutils.geometry import interpolate_bezier as bezlerp
from mathutils import Vector
from bpy.props import FloatProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.nodes.generator.basic_3pt_arc import generate_3PT_mode_1 as three_point_arc

def find_projected_arc_center(p1, p2, b, radius=0.5):
    focal = (Vector(p1) + Vector(p2)) / 2
    len_b_to_focal = (Vector(b) - focal).length

    # could be optimized for true 45 degree angle segments, but later maybe?
    ratio = len_b_to_focal / radius
    mid = Vector(b).lerp(focal, ratio)[:]
    return p1, mid, p2

def spline_points(points, weights, index, params):
    """ 
        b  .
       .        .
      .              .
     .                    c
    a

    """
    cyclic = params.loop
    divs = params.num_points
    a, b, c = points

    if len(weights) == 2:
        w1, w2 = weights
    else:
        w2 = weights[0]

    # return early if no weight, then user wants no smooth/fillet
    if -0.0001 < w2 < 0.0001:
        return [b]

    weight_to_use_1 = 1 - w2
    weight_to_use_2 = 1 - w2

    # if params.clamping == 'HARD' 
    if params.mode in {'absolute', 'arc'}:
        len_ab = (Vector(a)-Vector(b)).length
        len_cb = (Vector(c)-Vector(b)).length
        weight_to_use_1 = w2 / len_ab
        weight_to_use_2 = w2 / len_cb
        p1 = Vector(b).lerp(Vector(a), weight_to_use_1)[:]
        p2 = Vector(b).lerp(Vector(c), weight_to_use_2)[:]
    elif params.mode == 'relative':
        p1 = Vector(a).lerp(Vector(b), weight_to_use_1)[:]
        p2 = Vector(c).lerp(Vector(b), weight_to_use_2)[:]
    
    if params.mode == 'arc':
        pts = find_projected_arc_center(p1, p2, b, radius=w2)
        return three_point_arc(pts=pts, num_verts=divs, make_edges=False)[0]

    return [v[:] for v in bezlerp(p1, b, b, p2, divs)]


def func_xpline_2d(vlist, wlist, params):

    # nonsense input, garbage in / out
    if len(vlist) < 3:
        return vlist

    final_points = []
    add_points = final_points.extend

    if params.loop:
        vlist.extend(vlist[:2])
        wlist.extend(wlist[:2])
    else:
        add_points([vlist[0]])

    for i in range(len(vlist)-2):
        weights = wlist if len(wlist) == 1 else wlist[i:i+2]
        add_points(spline_points(vlist[i:i+3], weights, index=i, params=params))

    if not params.loop:
        add_points([vlist[-1]])

    return final_points

def edge_sequence_from_verts(num_indices, params):
    new_edges = [[i, i+1] for i in range(num_indices-1)]
    if params.loop:
        new_edges.append([num_indices-1, 0])
    return new_edges


class SvSmoothLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: smooth lines fil 
    Tooltip: accepts seq of verts and weights, returns smoothed lines
    
    This node should accept verts and weights and return the smoothed line representation.
    """

    bl_idname = 'SvSmoothLines'
    bl_label = 'Smooth Lines'
    bl_icon = 'GREASEPENCIL'

    smooth_mode_options = [(k, k, '', i) for i, k in enumerate(["absolute", "relative", "arc"])]
    smooth_selected_mode = EnumProperty(
        items=smooth_mode_options, description="offers....",
        default="absolute", update=updateNode)

    type_mode_options = [(k, k, '', i) for i, k in enumerate(["cyclic", "open"])]
    type_selected_mode = EnumProperty(
        items=type_mode_options, description="offers....",
        default="open", update=updateNode)

    n_verts = IntProperty(default=5, name="n_verts", min=2, update=updateNode) 
    weights = FloatProperty(default=0.0, name="weights", min=0.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("VerticesSocket", "vectors")
        self.inputs.new("StringsSocket", "weights").prop_name = "weights"
        self.inputs.new("StringsSocket", "attributes")
        self.outputs.new("VerticesSocket", "verts")
        self.outputs.new("StringsSocket", "edges")

    def draw_buttons(self, context, layout):

        # with attrs socket connected all params must be passed via this socket, to override node variables
        attr_socket = self.inputs.get('attributes')
        if attr_socket and attr_socket.is_linked:
            return

        col = layout.column()
        col.prop(self, "smooth_selected_mode", text="mode")
        col.prop(self, "type_selected_mode", text="type")
        col.prop(self, "n_verts", text='num verts')


    def process(self):
        necessary_sockets = [self.inputs["vectors"],]
        if not all(s.is_linked for s in necessary_sockets):
            return

        if self.inputs["attributes"].is_linked:
            # gather own data, rather than socket data
            # NOT IMPLEMENTED YET
            ...

        edges_socket = self.outputs['edges']
        verts_socket = self.outputs['verts']

        V_list = self.inputs['vectors'].sv_get()
        W_list = self.inputs['weights'].sv_get()
        verts_out = []
        edges_out = []

        if W_list and V_list:
            # ensure all vectors from V_list are matched by a weight.
            W_list = self.extend_if_needed(V_list, W_list)

        if not W_list:
            W_list = self.repeater_generator(self.weights)

        for vlist, wlist in zip(V_list, W_list):
            
            # setup this sequence, 
            params = lambda: None
            params.num_points = self.n_verts
            params.loop = False if not self.type_selected_mode == 'cyclic' else True
            params.remove_doubles = False
            params.weight = self.weights
            params.mode = self.smooth_selected_mode
            # params = self.get_params_from_attribute_socket()

            new_verts = func_xpline_2d(vlist, wlist, params)
            verts_out.append(new_verts)
            if edges_socket.is_linked:
                edges_out.append(edge_sequence_from_verts(len(new_verts), params))

        verts_socket.sv_set(verts_out)
        edges_socket.sv_set(edges_out)

    def repeater_generator(self, weight):
        def yielder():
            while True:
                yield weight
        return yielder

    def extend_if_needed(self, vl, wl):
        # match wl to correspond with vl
        try:
            last_value = wl[-1][-1]
        except:
            last_value = 0.5

        if (len(vl) > len(wl)):
            num_new_empty_lists = len(vl) - len(wl)
            for emlist in range(num_new_empty_lists):
                wl.append([])

        # extend each sublist in wl to match quantity found in sublists of v1
        for i, vlist in enumerate(vl):
            if (len(vlist) > len(wl[i])):
                num_new_repeats = len(vlist) - len(wl[i])
                for n in range(num_new_repeats):
                    wl[i].append(last_value)
        return wl

def register():
    bpy.utils.register_class(SvSmoothLines)


def unregister():
    bpy.utils.unregister_class(SvSmoothLines)