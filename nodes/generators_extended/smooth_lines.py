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

    if len(weights) == 3:
        w1, w2, w3 = weights
    else:
        w2 = weights[0]

    # if params.clamping == 'HARD' and params.mode == 'ABSOLUTE':
    # locate points  // # (1 - w) * p1 + w * p2
    p1 = Vector(a).lerp(Vector(b), w2)[:] # locate_point(a, b, w2)
    p2 = Vector(c).lerp(Vector(b), w2)[:] # locate_point(b, c, 1-w2)

    return [v[:] for v in bezlerp(p1, b, b, p2, divs)]


def func_xpline_2d(vlist, wlist, params):

    # nonsense input, garbage in / out
    if len(vlist) < 3:
        return vlist

    if params.loop:
        vlist.append(vlist[0])
        wlist.append(wlist[0])

    final_points = []
    add_points = final_points.append
    for i in range(len(vlist)-2):
        weights = wlist if len(wlist) == 1 else wlist[i:i+3]
        add_points(spline_points(vlist[i:i+3], weights, index=i, params=params))

    if params.loop:
        for section in final_points:
            section.pop()
    else:
        for index in range(len(final_points)-1):
            final_points[index].pop()

    return final_points


class SvSmoothLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: smooth lines fil 
    Tooltip: accepts seq of verts and weights, returns smoothed lines
    
    This node should accept verts and weights and return the smoothed line representation.
    """

    bl_idname = 'SvSmoothLines'
    bl_label = 'Smooth Lines'
    bl_icon = 'GREASEPENCIL'

    smooth_mode_options = [(k, k, '', i) for i, k in enumerate(["absolute", "relative"])]
    smooth_selected_mode = EnumProperty(
        items=smooth_mode_options, description="offers....",
        default="absolute", update=updateNode)

    type_mode_options = [(k, k, '', i) for i, k in enumerate(["cyclic", "open"])]
    type_selected_mode = EnumProperty(
        items=type_mode_options, description="offers....",
        default="cyclic", update=updateNode)

    n_verts = IntProperty(default=5, name="n_verts", min=0, update=updateNode) 
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
        if not attr_socket or not attr_socket.is_linked:
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
            ...

        V_list = self.inputs['vectors'].sv_get()
        W_list = self.inputs['weights'].sv_get()
        verts_out = []

        if W_list and V_list:
            # ensure all vectors from V_list are matched by a weight.
            W_list = self.extend_if_needed(V_list, W_list)

        if not W_list:
            W_list = self.repeater_generator(self.weights)


        for vlist, wlist in zip(V_list, W_list):
            params = lambda: None
            params.num_points = self.n_verts # or from attributes
            params.loop = False if not self.type_selected_mode == 'cyclic' else True
            params.remove_doubles = False
            params.weight = self.weights
            verts_out.append(func_xpline_2d(vlist, wlist, params))

        edges_out = []

        self.outputs['verts'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)

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