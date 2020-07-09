
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix
from mathutils import kdtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.curve import SvCurve
from sverchok.utils.geom import PlaneEquation
from sverchok.utils.math import xyz_axes
from sverchok.utils.manifolds import intersect_curve_plane
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExSlerpCurveFrameNode', "Interpolate Curve Frame", 'scipy')
else:

    def nearest_solution(point, solutions):
        if len(solutions) == 0:
            return None, None
        if len(solutions) <= 1:
            return solutions[0]
        kdt = kdtree.KDTree(len(solutions))
        for i, solution in enumerate(solutions):
            v = solution[1]
            kdt.insert(v, i)
        kdt.balance()
        _, i, _ = kdt.find(point)
        return solutions[i]

    def matrix_to_curve(curve, matrix, z_axis, init_samples=10, tolerance=1e-3, maxiter=50):
        plane = PlaneEquation.from_matrix(matrix, normal_axis=z_axis)
        # Or take nearest point?
        solutions = intersect_curve_plane(curve, plane,
                    init_samples=init_samples,
                    tolerance=tolerance,
                    maxiter=maxiter)
        t, point = nearest_solution(matrix.translation, solutions)
        if t is None:
            raise Exception(f"Can't project the matrix {matrix} to the {curve}!")
        #matrix.translation = Vector(point)
        return t, matrix.to_quaternion()

    def interpolate(tknots, ts, points, quats):
        base_indexes = tknots.searchsorted(ts, side='left')-1
        t1s, t2s = tknots[base_indexes], tknots[base_indexes+1]
        dts = (ts - t1s) / (t2s - t1s)
        #dts = np.clip(dts, 0.0, 1.0) # Just in case...
        matrix_out = []
        # TODO: ideally this shoulld be vectorized with numpy;
        # but that would require implementation of quaternion
        # interpolation in numpy.
        for dt, base_index, point in zip(dts, base_indexes, points):
            q1, q2 = quats[base_index], quats[base_index+1]
            # spherical linear interpolation.
            # TODO: implement `squad`.
            if dt < 0:
                q = q1
            elif dt > 1.0:
                q = q2
            else:
                q = q1.slerp(q2, dt)
            matrix = q.to_matrix().to_4x4()
            matrix.translation = Vector(point)
            matrix_out.append(matrix)
        return matrix_out

    def interpolate_frames(curve, frames, z_axis, ts, init_samples=10, tolerance=1e-3, maxiter=50):
        quats = []
        tknots = []
        for frame in frames:
            tk, quat = matrix_to_curve(curve, frame, z_axis, init_samples, tolerance, maxiter)
            quats.append(quat)
            tknots.append(tk)

        quats.insert(0, quats[0])
        quats.append(quats[-1])

        tknots.insert(0, -np.inf)
        tknots.append(np.inf)
        tknots = np.array(tknots)

        ts = np.array(ts)
        points = curve.evaluate_array(ts)
        return interpolate(tknots, ts, points, quats)

    class SvExSlerpCurveFrameNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Interpolate Curve Frame
        Tooltip: Interpolate curve frames
        """
        bl_idname = 'SvExSlerpCurveFrameNode'
        bl_label = 'Interpolate Curve Frame'
        bl_icon = 'OUTLINER_OB_EMPTY'

        samples : IntProperty(
            name = "Curve Resolution",
            description = "A number of segments to subdivide the curve in; defines the maximum number of intersection points that is possible to find.",
            default = 5,
            min = 1,
            update = updateNode)

        accuracy : IntProperty(
            name = "Accuracy",
            description = "Accuracy level - number of exact digits after decimal points.",
            default = 4,
            min = 1,
            update = updateNode)

        t_value : FloatProperty(
            name = "T",
            default = 0.5,
            update = updateNode)

        join : BoolProperty(
            name = "Join",
            description = "Output single flat list of matrices for all input curves",
            default = True,
            update = updateNode)

        z_axis : EnumProperty(
            name = "Orientation",
            description = "Which axis of the provided frames points along the curve",
            items = xyz_axes,
            default = 'Z',
            update = updateNode)

        def draw_buttons(self, context, layout):
            layout.prop(self, 'z_axis', expand=True)
            layout.prop(self, 'samples')
            layout.prop(self, 'join', toggle=True)
            
        def draw_buttons_ext(self, context, layout):
            layout.prop(self, 'accuracy')
            
        def sv_init(self, context):
            self.inputs.new('SvCurveSocket', "Curve")
            self.inputs.new('SvMatrixSocket', "Frames")
            self.inputs.new('SvStringsSocket', "T").prop_name = 't_value'
            self.outputs.new('SvMatrixSocket', "Frame")

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            curves_s = self.inputs['Curve'].sv_get()
            curves_s = ensure_nesting_level(curves_s, 2, data_types=(SvCurve,))
            frames_s = self.inputs['Frames'].sv_get()
            # list of frames per curve
            frames_s = ensure_nesting_level(frames_s, 3, data_types=(Matrix,))
            ts_s = self.inputs['T'].sv_get()
            # list of T values per curve
            ts_s = ensure_nesting_level(ts_s, 3)

            tolerance = 10**(-self.accuracy)

            frames_out = []
            for curves, frames_i, ts_i in zip_long_repeat(curves_s, frames_s, ts_s):
                for curve, frames, ts in zip_long_repeat(curves, frames_i, ts_i):
                    new_frames = interpolate_frames(curve, frames, self.z_axis, ts,
                                    init_samples = self.samples+1,
                                    tolerance = tolerance)
                    if self.join:
                        frames_out.extend(new_frames)
                    else:
                        frames_out.append(new_frames)

            self.outputs['Frame'].sv_set(frames_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExSlerpCurveFrameNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExSlerpCurveFrameNode)

