# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, BoolProperty

from sverchok.core.sv_custom_exceptions import SvInvalidInputException
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.curve.hobby import hobby_curve


class SvHobbySplineNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Hobby Spline
    Tooltip: Generate Hobby spline curve through given points with continuous mock curvature
    """
    bl_idname = 'SvHobbySplineNode'
    bl_label = 'Hobby Spline'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_POLYLINE'

    is_cyclic: BoolProperty(
        name="Cyclic",
        description="If checked, the spline will be closed (last point connects to first)",
        default=False,
        update=updateNode
    )

    concat: BoolProperty(
        name="Concatenate",
        description="If checked, output a single concatenated curve; otherwise, output individual Bezier segments",
        default=True,
        update=updateNode
    )

    tension: FloatProperty(
        name="Tension",
        description="Tension parameter. Higher values pull the curve closer to the polyline. "
                    "1.0 gives natural curvature, approaching infinity yields the polyline itself",
        min=0.75,
        max=100.0,
        default=1.0,
        precision=3,
        update=updateNode
    )

    curl_start: FloatProperty(
        name="Curl Start",
        description="Curl at the start endpoint. "
                    "1.0 gives circular-arc-like endpoint, 0.0 gives zero curvature (straight departure)",
        min=0.0,
        max=100.0,
        default=1.0,
        precision=3,
        update=updateNode
    )

    curl_end: FloatProperty(
        name="Curl End",
        description="Curl at the end endpoint. "
                    "1.0 gives circular-arc-like endpoint, 0.0 gives zero curvature (straight arrival)",
        min=0.0,
        max=100.0,
        default=1.0,
        precision=3,
        update=updateNode
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, "is_cyclic", toggle=True)
        layout.prop(self, "concat", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Tension").prop_name = 'tension'
        self.inputs.new('SvStringsSocket', "Curl Start").prop_name = 'curl_start'
        self.inputs.new('SvStringsSocket', "Curl End").prop_name = 'curl_end'
        self.outputs.new('SvCurveSocket', "Curve")

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(default=[[]])
        tension_s = self.inputs['Tension'].sv_get()
        curl_start_s = self.inputs['Curl Start'].sv_get()
        curl_end_s = self.inputs['Curl End'].sv_get()

        in_level = get_data_nesting_level(vertices_s)
        if in_level < 2 or in_level > 4:
            raise TypeError(
                f"Required nesting level is 2 to 4, provided data nesting level is {in_level}"
            )
        nested_out = in_level > 3

        # Normalize nesting levels for consistent iteration
        vertices_s = ensure_nesting_level(vertices_s, 4)
        tension_s = ensure_nesting_level(tension_s, 2)
        curl_start_s = ensure_nesting_level(curl_start_s, 2)
        curl_end_s = ensure_nesting_level(curl_end_s, 2)

        curve_out = []
        for params in zip_long_repeat(vertices_s, tension_s, curl_start_s, curl_end_s):
            new_curves = []
            for vertices, tension, curl_start, curl_end in zip_long_repeat(*params):
                if len(vertices) < 2:
                    raise SvInvalidInputException("At least two points are required")
                if self.is_cyclic and len(vertices) < 3:
                    raise SvInvalidInputException("At least three points are required to make a closed curve")

                curve = hobby_curve(
                    points=vertices,
                    cyclic=self.is_cyclic,
                    tension=tension,
                    curl_start=curl_start,
                    curl_end=curl_end,
                    concat=self.concat
                )
                new_curves.append(curve)

            if nested_out:
                curve_out.append(new_curves)
            else:
                curve_out.extend(new_curves)

        self.outputs['Curve'].sv_set(curve_out)


def register():
    bpy.utils.register_class(SvHobbySplineNode)


def unregister():
    bpy.utils.unregister_class(SvHobbySplineNode)
