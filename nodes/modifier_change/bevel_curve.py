# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from math import pi, degrees, floor, ceil, copysign
from mathutils import Vector, Matrix
import numpy as np

import bpy
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, Matrix_generate, Vector_generate, Vector_degenerate
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff, diameter
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.mesh import Mesh

class SvBevelCurveNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Bevel Curve
    Tooltip: Bevel a Curve (a.k.a. Extrude along Path)
    """

    bl_idname = 'SvBevelCurveNode'
    bl_label = 'Bevel a Curve'
    bl_icon = 'MOD_CURVE'

    algorithms = [
            ("householder", "Householder", "Use Householder reflection matrix", 1),
            ("track", "Tracking", "Use quaternion-based tracking", 2),
            ("diff", "Rotation difference", "Use rotational difference calculation", 3)
        ]

    algorithm = EnumProperty(name = "Algorithm",
        description = "Rotation calculation algorithm",
        default = "householder",
        items = algorithms, update=updateNode)

    axes = [
            ("X", "X", "X axis", 1),
            ("Y", "Y", "Y axis", 2),
            ("Z", "Z", "Z axis", 3)
        ]

    orient_axis = EnumProperty(name = "Orientation axis",
        description = "Which axis of donor objects to align with recipient curve",
        default = "Z",
        items = axes, update=updateNode)

    up_axis = EnumProperty(name = "Up axis",
        description = "Which axis of donor objects should look up",
        default = 'X',
        items = axes, update=updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]

    bevel_mode = EnumProperty(name='Bevel mode',
        default="SPL", items=modes,
        update=updateNode)

    taper_mode = EnumProperty(name='Taper mode',
        default="SPL", items=modes,
        update=updateNode)

    metrics =    [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                  ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
                  ('POINTS', 'Points', "Points based", 2),
                  ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    metric = EnumProperty(name='Metric',
        description = "Knot mode",
        default="DISTANCE", items=metrics,
        update=updateNode)

    is_cyclic = BoolProperty(name = "Cyclic",
        description = "Whether the spline is cyclic",
        default = False,
        update=updateNode)

    steps = IntProperty(name = "Steps",
        description = "Number of steps along the curve",
        default = 10, min = 4,
        update = updateNode)

    tangent_precision = FloatProperty(name='Tangent precision',
        description = "Step for tangents calculation. Lesser values correspond to better precision.",
        default = 0.001, min=0.000001, max=0.1, precision=8,
        update=updateNode)

    flip_curve = BoolProperty(name = "Flip Curve",
        description = "Invert curve direction - not from lesser coordinate values to greater, but vice versa",
        default = False,
        update=updateNode)

    flip_taper = BoolProperty(name = "Flip Taper",
        description = "Invert taper direction - not from lesser coordinate values to greater, but vice versa",
        default = False,
        update=updateNode)

    cap_start = BoolProperty(name = "Cap Start",
        description = "Make cap at the beginning of curve",
        default = False,
        update=updateNode)

    cap_end = BoolProperty(name = "Cap End",
        description = "Make cap at the ending of curve",
        default = False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Curve")
        self.inputs.new('VerticesSocket', 'BevelVerts')
        self.inputs.new('StringsSocket', 'BevelEdges')
        self.inputs.new('VerticesSocket', 'TaperVerts')
        self.inputs.new('StringsSocket', 'Steps').prop_name = "steps"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Faces')

    def draw_buttons(self, context, layout):
        layout.prop(self, "algorithm")
        layout.prop(self, "orient_axis", expand=True)
        if self.algorithm == 'track':
            layout.prop(self, "up_axis")
        layout.prop(self, "bevel_mode")
        layout.prop(self, "taper_mode")
        layout.prop(self, "is_cyclic", toggle=True)

        if not self.is_cyclic:
            row = layout.row(align=True)
            row.prop(self, "cap_start", toggle=True)
            row.prop(self, "cap_end", toggle=True)

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        row = layout.row(align=True)
        row.prop(self, "flip_curve", toggle=True)
        row.prop(self, "flip_taper", toggle=True)

        layout.prop(self, 'metric')
        layout.prop(self, 'tangent_precision')

    @property
    def orient_axis_idx(self):
        return 'XYZ'.index(self.orient_axis)

    def build_spline(self, path, mode, is_cyclic):
        if mode == 'LIN':
            spline = LinearSpline(path, metric = self.metric, is_cyclic = is_cyclic)
        else:  # SPL
            spline = CubicSpline(path, metric = self.metric, is_cyclic = is_cyclic)
        return spline

    def make_taper_spline(self, vertices):
        if len(vertices) == 0:
            def make_unit(z):
                u = Vector((0,0,0))
                u[self.orient_axis_idx] = z
                u[(self.orient_axis_idx+1) % 3] = 1
                return u
            vertices = [make_unit(0), make_unit(1)]
            return LinearSpline(vertices, metric = self.metric, is_cyclic = False)

        return self.build_spline(vertices, self.taper_mode, False)

    def get_matrix(self, tangent, scale):
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))

        if self.orient_axis_idx == 0:
            ax1, ax2, ax3 = x, y, z
        elif self.orient_axis_idx == 1:
            ax1, ax2, ax3 = y, x, z
        else:
            ax1, ax2, ax3 = z, x, y

        scale_matrix = Matrix.Scale(1, 4, ax1) * Matrix.Scale(scale, 4, ax2) * Matrix.Scale(scale, 4, ax3)

        if self.algorithm == 'householder':
            rot = autorotate_householder(ax1, tangent).inverted()
        elif self.algorithm == 'track':
            rot = autorotate_track(self.orient_axis, tangent, self.up_axis)
        elif self.algorithm == 'diff':
            rot = autorotate_diff(tangent, ax1)
        else:
            raise Exception("Unsupported algorithm")

        return rot * scale_matrix

    def get_taper_scale(self, vertex):
        projection = Vector(vertex)
        projection[self.orient_axis_idx] = 0
        return projection.length
    
    def make_bevel(self, curve, bevel_verts, bevel_edges, taper, steps):
        spline = self.build_spline(curve, self.bevel_mode, self.is_cyclic)
        t_values = np.linspace(0.0, 1.0, num = steps)
        if self.is_cyclic:
            t_values = t_values[:-1]
        if self.flip_curve:
            t_for_curve = 1.0 - t_values
        else:
            t_for_curve = t_values
        if self.flip_taper:
            t_for_taper = 1.0 - t_values
        else:
            t_for_taper = t_values

        spline_vertices = [Vector(v) for v in spline.eval(t_for_curve).tolist()]
        spline_tangents = [Vector(v) for v in spline.tangent(t_for_curve, h=self.tangent_precision).tolist()]
        taper_values = [self.get_taper_scale(v) for v in taper.eval(t_for_taper).tolist()]

        mesh = Mesh()
        prev_level_vertices = None
        first_level_vertices = None
        for spline_vertex, spline_tangent, taper_value in zip(spline_vertices, spline_tangents, taper_values):
            # Scaling and rotation matrix
            matrix = self.get_matrix(spline_tangent, taper_value)
            level_vertices = []
            for bevel_vertex in bevel_verts:
                new_vertex = matrix * Vector(bevel_vertex) + spline_vertex
                level_vertices.append(mesh.new_vertex(new_vertex))
            if prev_level_vertices is not None:
                for i,j in bevel_edges:
                    v1 = prev_level_vertices[i]
                    v2 = level_vertices[i]
                    v3 = level_vertices[j]
                    v4 = prev_level_vertices[j]
                    mesh.new_face([v4, v3, v2, v1])
            if first_level_vertices is None:
                first_level_vertices = level_vertices
            prev_level_vertices = level_vertices

        if not self.is_cyclic:
            if self.cap_start:
                mesh.new_face(list(reversed(first_level_vertices)))
            if self.cap_end and prev_level_vertices is not None:
                mesh.new_face(prev_level_vertices)
        else:
            for i,j in bevel_edges:
                v1 = first_level_vertices[i]
                v2 = prev_level_vertices[i]
                v3 = prev_level_vertices[j]
                v4 = first_level_vertices[j]
                mesh.new_face([v1, v2, v3, v4])
        return mesh

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get(default=[[]])
        bevel_verts_s = self.inputs['BevelVerts'].sv_get(default=[[]])
        bevel_edges_s = self.inputs['BevelEdges'].sv_get(default=[[]])
        taper_verts_s = self.inputs['TaperVerts'].sv_get(default=[[]])
        steps_s = self.inputs['Steps'].sv_get()[0]

        inputs = match_long_repeat([curves_s, bevel_verts_s, bevel_edges_s, taper_verts_s, steps_s])

        out_vertices = []
        out_edges = []
        out_faces = []
        for curve, bevel_verts, bevel_edges, taper_verts, steps in zip(*inputs):
            taper = self.make_taper_spline(taper_verts)
            mesh = self.make_bevel(curve, bevel_verts, bevel_edges, taper, steps)
            out_vertices.append(mesh.get_sv_vertices())
            out_edges.append(mesh.get_sv_edges())
            out_faces.append(mesh.get_sv_faces())

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)

def register():
    bpy.utils.register_class(SvBevelCurveNode)

def unregister():
    bpy.utils.unregister_class(SvBevelCurveNode)

