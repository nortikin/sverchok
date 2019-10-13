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

from math import sin, tan

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_4
from sverchok.nodes.generator.basic_3pt_arc import generate_3PT_mode_1 as three_point_arc
from sverchok.utils.sv_itertools import extend_if_needed


def find_projected_arc_center(p1, p2, b, radius=0.5):
    """
                            .
                        .  B.
                    .       .
               c.           .a
            .               .
        .                 C . = 90
    .....A........b..........

    c = circle enter distance
    b = tangent distance
    """    

    a = Vector(p1)
    b = Vector(b)
    c = Vector(p2)

    a = (a-b).normalized() + b
    c = (c-b).normalized() + b

    focal = (a + c) / 2.0
    focal_length = (b-focal).length

    try:
        angleA = (a-b).angle(c-b) / 2.0
    except ValueError as e:
        print('smoothlines encountered non zero length vectors')
        #  Vector.angle(other): zero length vectors have no valid angle
        return None

    # slightly undefined input handled ugly-er
    try:
        sideA = radius
        sideB = sideA / tan(angleA)
        sideC = sideA / sin(angleA)
    except Exception as e:
        print(e)
        print("no idea why this input happens.. show me a shorter version of your input mesh")
        return None

    try:
        ratio = (sideC - radius) / focal_length
    except Exception as e:
        print(e)
        print("smoothlines encountered two colinear lines, no arc to generate")
        # this will be interpretted as a no-op
        # potentially here you could return something like  [lerp(A,B, "radius"), B, lerp(C, B, "radius")]
        return None

    mid = b.lerp(focal, ratio)[:]
    
    ab_rate = sideB / (a-b).length
    cb_rate = sideB / (c-b).length
    p1 = b.lerp(a, ab_rate)[:]
    p2 = b.lerp(c, cb_rate)[:]

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

    if params.mode == 'absolute':
        len_ab = (Vector(a)-Vector(b)).length
        len_cb = (Vector(c)-Vector(b)).length
        weight_to_use_1 = w2 / len_ab
        weight_to_use_2 = w2 / len_cb
        p1 = Vector(b).lerp(Vector(a), weight_to_use_1)[:]
        p2 = Vector(b).lerp(Vector(c), weight_to_use_2)[:]
    elif params.mode == 'relative':
        p1 = Vector(a).lerp(Vector(b), weight_to_use_1)[:]
        p2 = Vector(c).lerp(Vector(b), weight_to_use_2)[:]
    elif params.mode == 'arc':
        pts = find_projected_arc_center(c, a, b, radius=w2)
        if not pts:
            return [b]
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
    bl_icon = 'NORMALIZE_FCURVES'

    smooth_selected_mode: EnumProperty(
        items=enum_item_4(["absolute", "relative", "arc"]), default="absolute",
        description="gives various representations of the smooth corner", update=updateNode)

    type_selected_mode: EnumProperty(
        items=enum_item_4(["cyclic", "open"]), default="open", update=updateNode)

    n_verts: IntProperty(default=5, name="n_verts", min=2, update=updateNode) 
    weights: FloatProperty(default=0.0, name="weights", min=0.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvVerticesSocket", "vectors")
        self.inputs.new("SvStringsSocket", "weights").prop_name = "weights"
        self.inputs.new("SvStringsSocket", "attributes")
        self.outputs.new("SvVerticesSocket", "verts")
        self.outputs.new("SvStringsSocket", "edges")

    def draw_buttons(self, context, layout):

        # with attrs socket connected all params must be passed via this socket, to override node variables
        attr_socket = self.inputs.get('attributes')
        if attr_socket and attr_socket.is_linked:
            return

        col = layout.column()
        row1 = col.row(align=True)
        row1.prop(self, "smooth_selected_mode", text="mode", expand=True)
        row2 = col.row(align=True)
        row2.prop(self, "type_selected_mode", text="type", expand=True)
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
            W_list = extend_if_needed(V_list, W_list, default=0.5)

        params = self.get_params()
        for vlist, wlist in zip(V_list, W_list):
            
            new_verts = func_xpline_2d(vlist, wlist, params)
            verts_out.append(new_verts)
            if edges_socket.is_linked:
                edges_out.append(edge_sequence_from_verts(len(new_verts), params))

        verts_socket.sv_set(verts_out)
        edges_socket.sv_set(edges_out)

    def get_params(self):
        params = lambda: None
        params.num_points = self.n_verts
        params.loop = False if not self.type_selected_mode == 'cyclic' else True
        params.remove_doubles = False
        params.weight = self.weights
        params.mode = self.smooth_selected_mode
        return params


def register():
    bpy.utils.register_class(SvSmoothLines)


def unregister():
    bpy.utils.unregister_class(SvSmoothLines)
