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

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
from mathutils import Vector
import numpy
from math import sin, cos, pi, sqrt

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (match_long_repeat, updateNode, apply_mask)
from sverchok.utils.geom import rotate_vector_around_vector, PlaneEquation, LineEquation, CubicSpline
from sverchok.utils.topo import stable_topo_sort

class SvConicSectionNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Ellipse, Parabola, Hyperbola
    Tooltip: Generate 3D Conic Sections
    """

    bl_idname = 'SvConicSectionNode'
    bl_label = "Conic Section"
    bl_icon = "CONE"

    cone_modes = [
            ("ANGLE", "Angle", "Define the cone by apex, direction and angle", 0),
            ("VECTOR", "Generating Vector", "Define the cone by apex, direction and generating vector", 1)
        ]

    def update_mode(self, context):
        self.inputs['Alpha'].hide_safe = self.cone_mode != 'ANGLE'
        self.inputs['Generatrix'].hide_safe = self.cone_mode != 'VECTOR'
        updateNode(self, context)

    cone_mode: EnumProperty(name = "Define Cone",
                    items = cone_modes,
                    default = "ANGLE",
                    update = update_mode)

    alpha: FloatProperty(name = "Cone Angle",
                description = "Cone Angle (Radians)",
                min = 0, max = pi/2, default = pi/6,
                update = updateNode)

    nlines: IntProperty(name = "Count",
                description = "Number of cone lines / output vertices",
                min = 2, default = 16,
                update = updateNode)

    maxd: FloatProperty(name = "Max. Distance",
                description = "Maximum distance from apex to generated vertex",
                min = 0, default = 100,
                update = updateNode)

    evenly: BoolProperty(name = "Even Distribution",
                description = "Distribute vertices evenly",
                default = False,
                update = updateNode)

    def sv_init(self, context):
        apex = self.inputs.new('SvVerticesSocket', "ConeApex")
        apex.use_prop = True
        apex.prop = (0.0, 0.0, 0.0)

        cone_dir = self.inputs.new('SvVerticesSocket', "ConeDirection")
        cone_dir.use_prop = True
        cone_dir.prop = (0.0, 0.0, 1.0)

        cone_gen = self.inputs.new('SvVerticesSocket', "Generatrix")
        cone_gen.use_prop = True
        cone_gen.prop = (1.0, 0.0, 1.0)

        self.inputs.new('SvStringsSocket', 'Alpha').prop_name = 'alpha'
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'nlines'
        self.inputs.new('SvStringsSocket', "MaxDistance").prop_name = 'maxd'

        plane_v = self.inputs.new('SvVerticesSocket', "PlanePoint")
        plane_v.use_prop = True
        plane_v.prop = (0.0, 0.0, 1.0)

        plane_d = self.inputs.new('SvVerticesSocket', "PlaneDirection")
        plane_d.use_prop = True
        plane_d.prop = (0.0, 0.0, 1.0)

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "BranchMask")
        self.outputs.new('SvStringsSocket', "SideMask")

        self.update_mode(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, "cone_mode")
        layout.prop(self, "evenly")

    def make_section(self, apex, cone_dir, alpha, cone_gen, count, plane_center, plane_dir, maxd):
        apex = Vector(apex)
        cone_dir = Vector(cone_dir)
        plane_dir = Vector(plane_dir)
        cone_dir2 = cone_dir.orthogonal()

        if self.cone_mode == 'ANGLE':
            cone_vector = rotate_vector_around_vector(cone_dir, cone_dir2, alpha)
        else:
            cone_vector = Vector(cone_gen)
        theta = 2*pi/count
        angle = 0

        plane = PlaneEquation.from_normal_and_point(plane_dir, plane_center)
        cone_ort_plane = PlaneEquation.from_normal_and_point(cone_dir, apex)

        if plane.side_of_point(apex) == 0 or (plane_dir.cross(cone_dir)).length < 1e-10:
            def get_side(v):
                return True
        else:
            apex_projection = plane.projection_of_point(apex)
            apex_ort = apex_projection - apex
            cone_sagital_plane = PlaneEquation.from_point_and_two_vectors(apex, apex_ort, cone_dir)
            def get_side(v):
                return cone_sagital_plane.side_of_point(v) > 0

        vertices = []
        branch_mask = []
        side_mask = []
        breaks = []
        i = 0
        while angle < 2*pi:
            cone_line = LineEquation.from_direction_and_point(cone_vector, apex)
            vertex = plane.intersect_with_line(cone_line, min_det = 1e-10)
            if vertex is not None and (vertex - apex).length <= maxd:
                vertices.append(tuple(vertex))
                branch = cone_ort_plane.side_of_point(vertex) > 0
                side = get_side(vertex)
                branch_mask.append(branch)
                side_mask.append(side)
                i += 1
            else:
                breaks.append(i)

            cone_vector = rotate_vector_around_vector(cone_vector, cone_dir, theta)
            angle += theta

        return vertices, branch_mask, side_mask, breaks
    
    def make_edges(self, branch_mask, breaks):
        verts11, verts12 = [], []
        verts21, verts22 = [], []
        edges1 = []
        edges2 = []
        prev_branch = None
        before_break = True
        last_break = None
        for i, branch in enumerate(branch_mask):
            if i not in breaks:
                if i == 0:
                    prev_index = len(branch_mask)-1
                    index = i
                else:
                    prev_index = i-1
                    index = i

                if prev_branch is None:
                    prev_branch = branch_mask[0]

                if prev_branch and branch:
                    edges1.append([prev_index, index])
                    if before_break:
                        if last_break is not None:
                            verts12.append(last_break)
                        verts12.append(index)
                    else:
                        if last_break is not None:
                            verts11.append(last_break)
                        verts11.append(index)
                elif not prev_branch and not branch:
                    edges2.append([prev_index, index])
                    if before_break:
                        if last_break is not None:
                            verts22.append(last_break)
                        verts22.append(index)
                    else:
                        if last_break is not None:
                            verts21.append(last_break)
                        verts21.append(index)
                last_break = None

            else:
                before_break = False
                last_break = i
            prev_branch = branch

        verts1 = verts11 + verts12
        verts2 = verts21 + verts22
        
        return verts1, verts2, edges1, edges2

    def interpolate(self, verts, n, is_cyclic):
        if len(verts) < 3:
            edges = [[i,i+1] for i in range(len(verts)-1)]
            return verts, edges
        spline = CubicSpline(verts, metric='DISTANCE', is_cyclic = is_cyclic)
        ts = numpy.linspace(0, 1, n)
        verts = [tuple(v) for v in spline.eval(ts).tolist()]
        edges = [[i,i+1] for i in range(len(verts)-1)]
        return verts, edges

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        apexes_s = self.inputs['ConeApex'].sv_get()
        conedirs_s = self.inputs['ConeDirection'].sv_get()
        conegens_s = self.inputs['Generatrix'].sv_get()
        alphas_s = self.inputs['Alpha'].sv_get()
        counts_s = self.inputs['Count'].sv_get()
        plane_centers_s = self.inputs['PlanePoint'].sv_get()
        plane_dirs_s = self.inputs['PlaneDirection'].sv_get()
        max_ds_s = self.inputs['MaxDistance'].sv_get()

        out_verts = []
        out_edges = []
        out_branch_masks = []
        out_side_masks = []

        objects = match_long_repeat([apexes_s, conedirs_s, alphas_s, conegens_s, counts_s, plane_centers_s, plane_dirs_s, max_ds_s])
        for apexes, conedirs, alphas, conegens, counts, plane_centers, plane_dirs, max_ds in zip(*objects):
            verts, branch_mask, side_mask, breaks = self.make_section(apexes[0], conedirs[0], alphas[0], conegens[0], counts[0], plane_centers[0], plane_dirs[0], max_ds[0])
            v1idxs, v2idxs, edges1, edges2 = self.make_edges(branch_mask, breaks)

            if self.evenly:
                verts1 = [verts[i] for i in v1idxs]
                verts2 = [verts[i] for i in v2idxs]
                is_cyclic = len(breaks) == 0
                verts1, edges1 = self.interpolate(verts1, counts[0], is_cyclic)
                verts2, edges2 = self.interpolate(verts2, counts[0], is_cyclic)
                verts = verts1 + verts2
                n1 = len(verts1)
                edges2 = [[i+n1, j+n1] for i,j in edges2]

            edges = edges1 + edges2

            out_verts.append(verts)
            out_edges.append(edges)
            out_branch_masks.append(branch_mask)
            out_side_masks.append(side_mask)

        self.outputs['Vertices'].sv_set(out_verts)
        self.outputs['Edges'].sv_set(out_edges)
        self.outputs['BranchMask'].sv_set(out_branch_masks)
        self.outputs['SideMask'].sv_set(out_side_masks)

def register():
    bpy.utils.register_class(SvConicSectionNode)


def unregister():
    bpy.utils.unregister_class(SvConicSectionNode)

