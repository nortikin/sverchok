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
    w1, w2, w3 = weights

    # if params.clamping == 'HARD' and params.mode == 'ABSOLUTE':
    # locate points  // # (1 - w) * p1 + w * p2
    p1 = Vector(a).lerp(Vector(b), w2)[:] # locate_point(a, b, w2)
    p2 = Vector(c).lerp(Vector(b), w2)[:] # locate_point(b, c, 1-w2)

    return bezlerp(p1, b, b, p2, divs)


def func_xpline_2d(V_list, W_list, params):

    # nonsense input, garbage in / out
    if len(V_list) < 3:
        return V_list

    if params.loop:
        V_list.append(V_list[0])
        W_list.append(W_list[0])

    final_points = []
    add_points = final_points.append
    for i, _ in enumerate(len(V_list)-3):
        add_points(spline_points(V_list[i:i+3], W_list[i:i+3], index=i, params=params))

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

    close_mode_options = [(k, k, '', i) for i, k in enumerate(["cyclic", "open"])]
    close_selected_mode = EnumProperty(
        items=close_mode_options, description="offers....",
        default="cyclic", update=updateNode)

    n_verts = IntProperty(default=5, name="n_verts", min=0) 
    weights = FloatProperty(default=0.0, name="weights", min=0.0)

    def sv_init(self, context):
        self.inputs.new("VerticesSocket", "vectors")
        self.inputs.new("StringsSocket", "weights").prop_name = "weights"
        self.inputs.new("StringsSocket", "attributes")
        self.outputs.new("VerticesSocket", "verts")
        self.outputs.new("StringsSocket", "edges")

    # def draw_buttons(self, context, layout):
    #    ...

    def process(self):
        necessary_sockets = [self.inputs["vectors"], self.inputs["weights"]]
        if not all(s.is_linked for s in necessary_sockets):
            return

        if self.inputs["attributes"].is_linked:
            # gather own data, rather than socket data
            ...

        verts_out = []
        for vlist, wlist in zip(V_list, W_list):
            params = lambda: None
            params.num_points = 10
            params.loop = False
            params.remove_doubles = False
            verts_out.append(func_xpline_2d(V_list, W_list, params))

        edges_out = []

        self.outputs['verts'].sv_set(verts_out)
        self.outputs['edges'].sv_set(edges_out)


def register():
    bpy.utils.register_class(SvSmoothLines)


def unregister():
    bpy.utils.unregister_class(SvSmoothLines)