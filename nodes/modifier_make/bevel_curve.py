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
import bmesh
from bpy.props import IntProperty, EnumProperty, BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, Matrix_generate, Vector_generate, Vector_degenerate, ensure_nesting_level
from sverchok.utils.geom import autorotate_householder, autorotate_track, autorotate_diff, diameter
from sverchok.utils.geom import LinearSpline, CubicSpline
from sverchok.utils.logging import info
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.nodes.modifier_change.polygons_to_edges import pols_edges

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

    bevel_mode = EnumProperty(name='Curve mode',
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

    taper_metrics = [("SAME", "Same as curve", "Use the same metric as for curve (Imprecise!)", 0),
                     ("AXIS", "Orientation axis", "Use metric along orientation axis", 1)]

    taper_metric = EnumProperty(name='Taper metric',
        description = "Metric used for taper object interpolation",
        default = "SAME", items=taper_metrics,
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

    separate_scale = BoolProperty(name = "Separate Scale",
        description = "Allow different scales along X and Y for taper object",
        default = False,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Curve")
        self.inputs.new('VerticesSocket', 'BevelVerts')
        self.inputs.new('StringsSocket', 'BevelEdges')
        self.inputs.new('StringsSocket', 'BevelFaces')
        self.inputs.new('VerticesSocket', 'TaperVerts')
        self.inputs.new('StringsSocket', 'Steps').prop_name = "steps"

        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('StringsSocket', 'Edges')
        self.outputs.new('StringsSocket', 'Faces')

    def draw_buttons(self, context, layout):
        layout.prop(self, "orient_axis", expand=True)
        layout.prop(self, "algorithm")
        if self.algorithm == 'track':
            layout.prop(self, "up_axis")
        layout.prop(self, "bevel_mode")
        layout.prop(self, "taper_mode")
        row = layout.row(align=True)
        row.prop(self, "is_cyclic", toggle=True)
        row.prop(self, "separate_scale", toggle=True)

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
        layout.prop(self, 'taper_metric')
        layout.prop(self, 'tangent_precision')

    @property
    def orient_axis_idx(self):
        return 'XYZ'.index(self.orient_axis)

    def build_spline(self, path, mode, is_cyclic, metric=None):
        if metric is None:
            metric = self.metric
        if mode == 'LIN':
            spline = LinearSpline(path, metric = metric, is_cyclic = is_cyclic)
        else:  # SPL
            spline = CubicSpline(path, metric = metric, is_cyclic = is_cyclic)
        return spline

    def make_taper_spline(self, vertices):
        if self.taper_metric == 'SAME':
            metric = self.metric
        else:
            metric = self.orient_axis

        if len(vertices) == 0:
            # if no taper object provided: use constant scale of 1.0
            def make_unit(z):
                u = Vector((0,0,0))
                u[self.orient_axis_idx] = z
                u[(self.orient_axis_idx+1) % 3] = 1
                return u
            vertices = [make_unit(0), make_unit(1)]
            return LinearSpline(vertices, metric = metric, is_cyclic = False)

        return self.build_spline(vertices, self.taper_mode, is_cyclic=False, metric=metric)

    def get_matrix(self, tangent, scale_x, scale_y):
        x = Vector((1.0, 0.0, 0.0))
        y = Vector((0.0, 1.0, 0.0))
        z = Vector((0.0, 0.0, 1.0))

        if self.orient_axis_idx == 0:
            ax1, ax2, ax3 = x, y, z
        elif self.orient_axis_idx == 1:
            ax1, ax2, ax3 = y, x, z
        else:
            ax1, ax2, ax3 = z, x, y

        scale_matrix = Matrix.Scale(1, 4, ax1) * Matrix.Scale(scale_x, 4, ax2) * Matrix.Scale(scale_y, 4, ax3)

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
        if self.separate_scale:
            return abs(projection[(self.orient_axis_idx + 1) % 3]), abs(projection[(self.orient_axis_idx - 1) % 3])
        else:
            projection[self.orient_axis_idx] = 0
            return projection.length, projection.length
    
    def make_bevel(self, curve, bevel_verts, bevel_edges, bevel_faces, taper, steps):
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

        if bevel_faces:
            bevel_faces = ensure_nesting_level(bevel_faces, 2)
        if not bevel_edges and bevel_faces:
            bevel_edges = pols_edges([bevel_faces], True)[0]

        mesh = bmesh.new()
        prev_level_vertices = None
        first_level_vertices = None
        for spline_vertex, spline_tangent, taper_value in zip(spline_vertices, spline_tangents, taper_values):
            # Scaling and rotation matrix
            scale_x, scale_y = taper_value
            matrix = self.get_matrix(spline_tangent, scale_x, scale_y)
            level_vertices = []
            for bevel_vertex in bevel_verts:
                new_vertex = matrix * Vector(bevel_vertex) + spline_vertex
                level_vertices.append(mesh.verts.new(new_vertex))
            if prev_level_vertices is not None:
                for i,j in bevel_edges:
                    v1 = prev_level_vertices[i]
                    v2 = level_vertices[i]
                    v3 = level_vertices[j]
                    v4 = prev_level_vertices[j]
                    mesh.faces.new([v4, v3, v2, v1])

            if first_level_vertices is None:
                first_level_vertices = level_vertices
            prev_level_vertices = level_vertices

        if not self.is_cyclic:
            if self.cap_start:
                if not bevel_faces:
                    mesh.faces.new(list(reversed(first_level_vertices)))
                else:
                    for face in bevel_faces:
                        cap = [first_level_vertices[i] for i in reversed(face)]
                        mesh.faces.new(cap)
            if self.cap_end and prev_level_vertices is not None:
                if not bevel_faces:
                    mesh.faces.new(prev_level_vertices)
                else:
                    for face in bevel_faces:
                        cap = [prev_level_vertices[i] for i in face]
                        mesh.faces.new(cap)
        else:
            for i,j in bevel_edges:
                v1 = first_level_vertices[i]
                v2 = prev_level_vertices[i]
                v3 = prev_level_vertices[j]
                v4 = first_level_vertices[j]
                mesh.faces.new([v1, v2, v3, v4])

        mesh.verts.index_update()
        mesh.verts.ensure_lookup_table()
        mesh.faces.index_update()
        mesh.edges.index_update()

        return mesh

    def process(self):
        if not any(o.is_linked for o in self.outputs):
            return

        curves_s = self.inputs['Curve'].sv_get(default=[[]])
        bevel_verts_s = self.inputs['BevelVerts'].sv_get(default=[[]])
        bevel_edges_s = self.inputs['BevelEdges'].sv_get(default=[[]])
        bevel_faces_s = self.inputs['BevelFaces'].sv_get(default=[[]])
        taper_verts_s = self.inputs['TaperVerts'].sv_get(default=[[]])
        steps_s = self.inputs['Steps'].sv_get()[0]

        inputs = match_long_repeat([curves_s, bevel_verts_s, bevel_edges_s, bevel_faces_s, taper_verts_s, steps_s])

        out_vertices = []
        out_edges = []
        out_faces = []
        for curve, bevel_verts, bevel_edges, bevel_faces, taper_verts, steps in zip(*inputs):
            taper = self.make_taper_spline(taper_verts)
            mesh = self.make_bevel(curve, bevel_verts, bevel_edges, bevel_faces, taper, steps)
            new_verts, new_edges, new_faces = pydata_from_bmesh(mesh)
            out_vertices.append(new_verts)
            out_edges.append(new_edges)
            out_faces.append(new_faces)
            mesh.free()

        self.outputs['Vertices'].sv_set(out_vertices)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['Faces'].sv_set(out_faces)

def register():
    bpy.utils.register_class(SvBevelCurveNode)

def unregister():
    bpy.utils.unregister_class(SvBevelCurveNode)

