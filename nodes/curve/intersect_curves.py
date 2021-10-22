# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, split_by_count, transpose_list
from sverchok.utils.curve import SvCurve
from sverchok.utils.curve.nurbs import SvNurbsCurve
from sverchok.utils.curve.nurbs_algorithms import intersect_nurbs_curves
from sverchok.utils.curve.freecad import curve_to_freecad
from sverchok.dependencies import FreeCAD, scipy
from sverchok.utils.dummy_nodes import add_dummy

if FreeCAD is None and scipy is None:
    add_dummy('SvIntersectNurbsCurvesNode', "Intersect Curves", 'FreeCAD or scipy')

if FreeCAD is not None:
    from FreeCAD import Base

class SvIntersectNurbsCurvesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Intersect Curves
    Tooltip: Find intersection points of two NURBS curves
    """
    bl_idname = 'SvIntersectNurbsCurvesNode'
    bl_label = 'Intersect NURBS Curves'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_INTERSECT_CURVES'

    def get_implementations(self, context):
        result = []
        if FreeCAD is not None:
            item = ('FREECAD', "FreeCAD", "Implementation from FreeCAD library", 0)
            result.append(item)
        
        if scipy is not None:
            item = ('SCIPY', "SciPy", "Sverchok built-in implementation", 1)
            result.append(item)

        return result

    implementation : EnumProperty(
            name = "Implementation",
            items = get_implementations,
            update = updateNode)

    match_methods = [
            ('LONG', "Longest", "", 0),
            ('CROSS', "Cross", "", 1)
        ]

    matching : EnumProperty(
            name = "Matching",
            items = match_methods,
            update = updateNode)

    single : BoolProperty(
            name = "Find single intersection",
            default = True,
            update = updateNode)

    check_intersection : BoolProperty(
            name = "Curves do intersect",
            description = "If checked, the node will fail when curves do not intersect",
            default = False,
            update = updateNode)

    precision : FloatProperty(
            name = "Precision",
            default = 0.001,
            precision = 6,
            min = 0,
            update = updateNode)

    methods = [
            ('Nelder-Mead', "Nelder-Mead", "", 0),
            ('L-BFGS-B', 'L-BFGS-B', "", 1),
            ('SLSQP', 'SLSQP', "", 2),
            ('Powell', 'Powell', "", 3),
            ('trust-constr', 'Trust-Constr', "", 4)
        ]

    method : EnumProperty(
            name = "Numeric method",
            items = methods,
            default = methods[0][0],
            update = updateNode)

    split : BoolProperty(
            name = "Split by row",
            default = True,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'implementation', text='')
        layout.prop(self, 'matching')
        layout.prop(self, 'single')
        layout.prop(self, 'check_intersection')
        if self.matching == 'CROSS':
            layout.prop(self, 'split')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.implementation == 'SCIPY':
            layout.prop(self, 'precision')
            layout.prop(self, 'method')

    def sv_init(self, context):
        self.inputs.new('SvCurveSocket', "Curve1")
        self.inputs.new('SvCurveSocket', "Curve2")
        self.outputs.new('SvVerticesSocket', "Intersections")
        self.outputs.new('SvStringsSocket', "T1")
        self.outputs.new('SvStringsSocket', "T2")

    def _filter(self, points):
        if not points:
            return [], [], []

        t1, t2, prev = points[0]
        out_t1 = [t1]
        out_t2 = [t2]
        out_points = [prev]
        for t1, t2, p in points[1:]:
            r = (Vector(p) - Vector(prev)).length
            if r > 1e-4:
                out_t1.append(t1)
                out_t2.append(t2)
                out_points.append(p)
            prev = p
        return out_t1, out_t2, out_points

    def process_native(self, curve1, curve2):
        res = intersect_nurbs_curves(curve1, curve2,
                    method = self.method,
                    numeric_precision = self.precision,
                    logger = self.get_logger())
        points = [(r[0], r[1], r[2].tolist()) for r in res]
        return self._filter(points)

    def process_freecad(self, sv_curve1, sv_curve2):
        fc_curve1 = curve_to_freecad(sv_curve1)[0]
        fc_curve2 = curve_to_freecad(sv_curve2)[0]
        points = fc_curve1.curve.intersectCC(fc_curve2.curve)
        points = [(p.X, p.Y, p.Z) for p in points]

        pts = []
        for p in points:
            t1 = fc_curve1.curve.parameter(Base.Vector(*p))
            t2 = fc_curve2.curve.parameter(Base.Vector(*p))
            pts.append((t1, t2, p))
        return self._filter(pts)

    def match(self, curves1, curves2):
        if self.matching == 'LONG':
            return zip_long_repeat(list(enumerate(curves1)), list(enumerate(curves2)))
        else:
            return [(c1, c2) for c2 in enumerate(curves2) for c1 in enumerate(curves1)]

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        curve1_s = self.inputs['Curve1'].sv_get()
        curve2_s = self.inputs['Curve2'].sv_get()

        curve1_s = ensure_nesting_level(curve1_s, 2, data_types=(SvCurve,))
        curve2_s = ensure_nesting_level(curve2_s, 2, data_types=(SvCurve,))

        points_out = []
        t1_out = []
        t2_out = []

        object_idx = 0
        for curve1s, curve2s in zip_long_repeat(curve1_s, curve2_s):
            new_points = []
            new_t1 = []
            new_t2 = []
            for (i, curve1), (j, curve2) in self.match(curve1s, curve2s):
                curve1 = SvNurbsCurve.to_nurbs(curve1)
                if curve1 is None:
                    raise Exception("Curve1 is not a NURBS")
                curve2 = SvNurbsCurve.to_nurbs(curve2)
                if curve2 is None:
                    raise Exception("Curve2 is not a NURBS")

                if self.implementation == 'SCIPY':
                    t1s, t2s, ps = self.process_native(curve1, curve2)
                else:
                    t1s, t2s, ps = self.process_freecad(curve1, curve2)

                if self.check_intersection:
                    if not ps:
                        raise Exception(f"Object #{object_idx}: Curve #{i} does not intersect with curve #{j}!")

                if self.single:
                    if len(ps) >= 1:
                        ps = ps[0]
                        t1s = t1s[0]
                        t2s = t2s[0]

                new_points.append(ps)
                new_t1.append(t1s)
                new_t2.append(t2s)

            if self.split:
                n = len(curve1s)
                new_points = split_by_count(new_points, n)
                new_t1 = split_by_count(new_t1, n)
                new_t1 = transpose_list(new_t1)
                new_t2 = split_by_count(new_t2, n)

            points_out.append(new_points)
            t1_out.append(new_t1)
            t2_out.append(new_t2)
            object_idx += 1

        self.outputs['Intersections'].sv_set(points_out)
        self.outputs['T1'].sv_set(t1_out)
        self.outputs['T2'].sv_set(t2_out)

def register():
    if FreeCAD is not None or scipy is not None:
        bpy.utils.register_class(SvIntersectNurbsCurvesNode)

def unregister():
    if FreeCAD is not None or scipy is not None:
        bpy.utils.unregister_class(SvIntersectNurbsCurvesNode)

