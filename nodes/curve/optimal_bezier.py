# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.curve.optimal_bezier import optimal_bezier_spline


METRICS = [
    ('POINTS', "Points (uniform)", "All segments receive equal time. Fast; works well when node spacing is roughly even."),
    ('DISTANCE', "Distance (chord-length)", "Segment times proportional to distances between consecutive nodes. Better for uneven spacing."),
    ('OPTIMAL', "Optimal (energy-minimized)", "Hill-descent minimization of bending energy ∫|B''(t)|². Typically 5-15% lower energy than chord-length."),
]


class SvOptimalBezierSplineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Optimal Bezier Spline
    Tooltip: Build a C2-continuous cubic Bezier spline through interpolation nodes
    """
    bl_idname = 'SvOptimalBezierSplineNode'
    bl_label = 'Optimal Bezier Spline'
    bl_icon = 'CURVE_NCURVE'
    sv_icon = 'SV_BEZIER_CURVE'

    metric: EnumProperty(
        name='Metric',
        description="Parameterization strategy",
        items=METRICS,
        default='OPTIMAL',
        update=updateNode,
    )

    cyclic: BoolProperty(
        name="Cyclic",
        description="If checked, the spline wraps the last segment back to the first node (closed spline)",
        default=False,
        update=updateNode,
    )

    epsilon: FloatProperty(
        name="Epsilon",
        description="Convergence tolerance for hill-descent optimization",
        min=1e-15,
        max=1.0,
        default=1e-8,
        precision=15,
        update=updateNode,
    )

    max_iterations: IntProperty(
        name="Max Iterations",
        description="Maximum hill-descent iterations",
        min=1,
        max=100000,
        default=1000,
        update=updateNode,
    )

    delta: FloatProperty(
        name="Delta",
        description="Initial step parameter for hill-descent",
        min=0.0001,
        max=1.0,
        default=0.01,
        precision=4,
        update=updateNode,
    )

    acceleration: FloatProperty(
        name="Acceleration",
        description="Step-size acceleration factor for hill-descent",
        min=1.01,
        max=10.0,
        default=1.2,
        precision=3,
        update=updateNode,
    )

    show_advanced: BoolProperty(
        name="Advanced",
        description="Show advanced optimization parameters",
        default=False,
        update=updateNode,
    )

    def update_sockets(self, context):
        self.inputs['Epsilon'].hide_safe = not self.show_advanced or self.metric != 'OPTIMAL'
        self.inputs['Max Iterations'].hide_safe = not self.show_advanced or self.metric != 'OPTIMAL'
        self.inputs['Delta'].hide_safe = not self.show_advanced or self.metric != 'OPTIMAL'
        self.inputs['Acceleration'].hide_safe = not self.show_advanced or self.metric != 'OPTIMAL'
        updateNode(self, context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'metric', text='')
        layout.prop(self, 'cyclic', toggle=True)
        row = layout.row(align=True)
        row.prop(self, 'show_advanced', icon='TRIA_DOWN' if self.show_advanced else 'TRIA_RIGHT', text='Optimization')
        if self.show_advanced and self.metric == 'OPTIMAL':
            box = layout.box()
            box.prop(self, 'epsilon', text='Epsilon')
            box.prop(self, 'max_iterations', text='Max Iter')
            box.prop(self, 'delta', text='Delta')
            box.prop(self, 'acceleration', text='Accel')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
        self.inputs.new('SvStringsSocket', "Max Iterations").prop_name = 'max_iterations'
        self.inputs.new('SvStringsSocket', "Delta").prop_name = 'delta'
        self.inputs.new('SvStringsSocket', "Acceleration").prop_name = 'acceleration'

        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "ControlPoints")
        self.outputs.new('SvStringsSocket', "Segments")
        self.update_sockets(context)

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        epsilon_s = self.inputs['Epsilon'].sv_get()
        max_iter_s = self.inputs['Max Iterations'].sv_get()
        delta_s = self.inputs['Delta'].sv_get()
        accel_s = self.inputs['Acceleration'].sv_get()

        in_level = get_data_nesting_level(vertices_s)
        if in_level < 2 or in_level > 4:
            raise TypeError(f"Required nesting level is 2 to 4, provided data nesting level is {in_level}")
        nested_out = in_level > 3

        vertices_s = ensure_nesting_level(vertices_s, 4)
        epsilon_s = ensure_nesting_level(epsilon_s, 3)
        max_iter_s = ensure_nesting_level(max_iter_s, 3)
        delta_s = ensure_nesting_level(delta_s, 3)
        accel_s = ensure_nesting_level(accel_s, 3)

        curves_out = []
        control_points_out = []
        segments_out = []

        for params in zip_long_repeat(vertices_s, epsilon_s, max_iter_s, delta_s, accel_s):
            new_curves = []
            new_control_points = []
            new_segments = []

            for vertices, eps, max_iter, delta, accel in zip_long_repeat(*params):
                if len(vertices) < 2:
                    continue

                # Extract scalar values from nested lists
                if isinstance(eps, (list, tuple)):
                    eps = eps[0] if eps else 1e-8
                if isinstance(max_iter, (list, tuple)):
                    max_iter = max_iter[0] if max_iter else 1000
                if isinstance(delta, (list, tuple)):
                    delta = delta[0] if delta else 0.01
                if isinstance(accel, (list, tuple)):
                    accel = accel[0] if accel else 1.2

                curve = optimal_bezier_spline(
                    points=vertices,
                    cyclic=self.cyclic,
                    metric=self.metric,
                    concat=True,
                    epsilon=eps,
                    max_iterations=max_iter,
                    delta=delta,
                    acceleration=accel,
                )

                new_curves.append(curve)
                new_control_points.append(curve.get_control_points().tolist())

                # Count segments: for open spline = n-1, for closed = n
                segment_count = len(vertices) if self.cyclic else len(vertices) - 1
                new_segments.append(segment_count)

            if nested_out:
                curves_out.append(new_curves)
                control_points_out.append(new_control_points)
                segments_out.append(new_segments)
            else:
                curves_out.extend(new_curves)
                control_points_out.extend(new_control_points)
                segments_out.extend(new_segments)

        self.outputs['Curve'].sv_set(curves_out)
        self.outputs['ControlPoints'].sv_set(control_points_out)
        self.outputs['Segments'].sv_set(segments_out)


def register():
    bpy.utils.register_class(SvOptimalBezierSplineNode)


def unregister():
    bpy.utils.unregister_class(SvOptimalBezierSplineNode)


if __name__ == '__main__':
    register()
