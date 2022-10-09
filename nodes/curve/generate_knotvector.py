# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.math import supported_metrics, xyz_metrics
from sverchok.utils.curve import knotvector as sv_knotvector
from sverchok.utils.geom import Spline

class SvGenerateKnotvectorNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Generate Knotvector
    Tooltip: Calculate knot values for a spline or NURBS curve
    """
    bl_idname = 'SvGenerateKnotvectorNode'
    bl_label = 'Generate Knots'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_APPROXIMATE_CURVE'

    degree : IntProperty(
            name = "Degree",
            description = "Curve degree",
            min = 1,
            default = 3,
            update = updateNode)

    num_cpts : IntProperty(
            name = "Control Points",
            description = "Number of control points",
            min = 2,
            default = 4,
            update = updateNode)

    metric: EnumProperty(
            name='Metric',
            description = "Knot mode",
            default="DISTANCE", items=supported_metrics + xyz_metrics,
            update=updateNode)

    clamped : BoolProperty(
            name = "Clamped",
            description = "Generate clamped knotvector",
            default = True,
            update=updateNode)

    modes = [
            ('UNIFORM', "Uniform", "Generate uniform knotvector based on number of control points and degree", 0),
            ('POINTS', "From Points", "Generate knotvector from point positions, based on some metric", 1)
        ]

    def update_sockets(self, context):
        self.inputs['Vertices'].hide_safe = self.mode != 'POINTS'
        self.inputs['ControlPointsCount'].hide_safe = (self.mode != 'UNIFORM') and not self.rescale
        updateNode(self, context)

    mode : EnumProperty(
            name = "Mode",
            description = "How to generate knotvector",
            items = modes, default = 'UNIFORM',
            update = update_sockets)

    rescale : BoolProperty(
            name = "Set control points number",
            description = "Rescale generated knotvector to fit the specified control points count",
            default = False,
            update = update_sockets)

    numpy_out : BoolProperty(
            name = "NumPy output",
            default = False,
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', text='')
        if self.mode == 'POINTS':
            layout.prop(self, 'metric')
            layout.prop(self, 'rescale')
        else:
            layout.prop(self, 'clamped')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'numpy_out')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Degree").prop_name = 'degree'
        self.inputs.new('SvStringsSocket', "ControlPointsCount").prop_name = 'num_cpts'
        self.outputs.new('SvStringsSocket', "Knotvector")
        self.outputs.new('SvStringsSocket', "Knots")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default = [[[[0]]]])
        degree_s = self.inputs['Degree'].sv_get()
        num_cpts_s = self.inputs['ControlPointsCount'].sv_get()

        vertices_s = ensure_nesting_level(vertices_s, 4)
        degree_s = ensure_nesting_level(degree_s, 2)
        num_cpts_s = ensure_nesting_level(num_cpts_s, 2)

        knotvector_out = []
        knots_out = []
        for params in zip_long_repeat(vertices_s, degree_s, num_cpts_s):
            new_knotvectors = []
            new_knots = []
            for vertices, degree, num_cpts in zip_long_repeat(*params):
                if self.mode == 'UNIFORM':
                    knotvector = sv_knotvector.generate(degree, num_cpts, clamped = self.clamped)
                    knots = np.unique(knotvector)
                else:
                    if not self.rescale:
                        num_cpts = None
                    knots = Spline.create_knots(np.asarray(vertices), metric = self.metric)
                    knotvector = sv_knotvector.from_tknots(degree, knots, num_cpts)
                if not self.numpy_out:
                    knots = knots.tolist()
                    knotvector = knotvector.tolist()
                new_knotvectors.append(knotvector)
                new_knots.append(knots)
            knotvector_out.append(new_knotvectors)
            knots_out.append(new_knots)

        self.outputs['Knotvector'].sv_set(knotvector_out)
        self.outputs['Knots'].sv_set(knots_out)

def register():
    bpy.utils.register_class(SvGenerateKnotvectorNode)

def unregister():
    bpy.utils.unregister_class(SvGenerateKnotvectorNode)

