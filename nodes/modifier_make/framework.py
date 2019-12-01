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

from collections import defaultdict

import bpy
import bmesh
from mathutils import Vector
from mathutils.geometry import intersect_point_line
from bpy.props import IntProperty, FloatProperty, EnumProperty, BoolProperty

from sverchok.data_structure import match_long_repeat, cycle_for_length, updateNode
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.logging import info
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh, bmesh_from_pydata, remove_doubles
from sverchok.utils.intersect_edges import intersect_edges_3d

def distance_z(idx, v1, v2):
    return abs(v1[idx] - v2[idx])

def is_in_segment(v1, v2, point, tolerance=1e-6):
    closest, percent = intersect_point_line(point, v1, v2)
    if not (0 <= percent <= 1):
        return False
    distance = (point - closest).length
    if distance > tolerance:
        return False
    return True

def make_verts_axis(v, Z, make_basis, offset, step, count):
    result = []
    v = Vector(v)
    has_offset = abs(offset) > 1e-6
    if make_basis or not has_offset:
        result.append(v)
    if has_offset:
        v = v + offset*Z
        result.append(v)
    for i in range(count):
        v = v + step*Z
        result.append(v)
    if make_basis or not has_offset:
        v = v + (step - offset)*Z
        result.append(v)
    return result

def make_verts_curve(v, curve):
    #info("C: %s", curve)
    v = Vector(v)
    result = []
    prev_pt = None
    for pt in curve:
        pt = Vector(pt)
        if prev_pt is None:
            dv = pt
        else:
            dv = pt - prev_pt
        v = v + dv
        result.append(v)
        prev_pt = pt
    return result

def connect_verts(bm, z_idx, v1, verts2_bm, width):
    if z_idx is not None:
        dz = width / 2.0
    else:
        dz = width
    for v2 in verts2_bm:
        if z_idx is not None:
            distance = distance_z(z_idx, v1.co, v2.co)
        else:
            distance = (v1.co - v2.co).length
        #info("V1: %s, V2: %s, distance: %s", v1.co, v2.co, distance)
        if distance <= dz + 1e-6:
            #info("make edge")
            bm.edges.new((v1, v2))
            bm.edges.ensure_lookup_table()

def process_edge(bm, z_idx, verts1_bm, verts2_bm, step1, step2, mult1, mult2):
    if step1 < step2:
        verts1_bm, verts2_bm = verts2_bm, verts1_bm
        step1, step2 = step2, step1
        mult1, mult2 = mult2, mult1
                
    bm.verts.index_update()
    
    for i, v in enumerate(verts1_bm):
        #info("Connect #%s", i)
        connect_verts(bm, z_idx, v, verts2_bm, mult1 * step1)
    
class SvFrameworkNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Framework / carcass / ferme
    Tooltip: Generate construction framework
    """

    bl_idname = 'SvFrameworkNode'
    bl_label = 'Framework'
    bl_icon = 'OUTLINER_OB_EMPTY'

    offset : FloatProperty(name = "Offset",
            description = "Vertices offset along orientation axis",
            min = 0, max = 1.0, default = 0,
            update = updateNode)

    step : FloatProperty(name = "Step",
            description = "Step between vertices along orientation axis",
            min = 0, default = 1.0,
            update = updateNode)

    multiplier : FloatProperty(name = "Multiplier",
            description = "Edges multiplier, defines how many edges this will generate",
            min = 0.0, default = 1.0,
            update = updateNode)
    
    count : IntProperty(name = "Count",
            description = "How many vertices to generate",
            min = 1, default = 10,
            update = updateNode)

    def update_z_mode(self, context):
        self.inputs['Offset'].hide_safe = self.z_mode != 'AXIS'
        self.inputs['Step'].hide_safe = self.z_mode != 'AXIS'
        self.inputs['Count'].hide_safe = self.z_mode != 'AXIS'
        self.inputs['Curve'].hide_safe = self.z_mode == 'AXIS'
        updateNode(self, context)

    z_modes = [
            ("AXIS", "Axis", "Generate framework along X, Y, or Z axis", 0),
            ("CURVE", "Curve", "Generate framework along arbitrary curve", 1)
        ]

    z_mode : EnumProperty(name = "Mode",
            description = "Third dimension generation mode",
            default = "AXIS",
            items = z_modes,
            update = update_z_mode)

    axes = [
        ("X", "X", "X axis", 1),
        ("Y", "Y", "Y axis", 2),
        ("Z", "Z", "Z axis", 3)]

    orient_axis: EnumProperty(name = "Orientation axis",
            description = "Framework orientation axis",
            default = "Z",
            items = axes, update=updateNode)

    make_basis : BoolProperty(name = "Basis",
            description = "Always make baseline vertices (without offset)",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "z_mode", expand=True)
        if self.z_mode == 'AXIS':
            layout.prop(self, "orient_axis", expand=True)
            layout.prop(self, "make_basis", toggle=True)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvVerticesSocket', 'Curve')
        self.inputs.new('SvStringsSocket', 'Offset').prop_name = 'offset'
        self.inputs.new('SvStringsSocket', 'Step').prop_name = 'step'
        self.inputs.new('SvStringsSocket', 'Multiplier').prop_name = 'multiplier'
        self.inputs.new('SvStringsSocket', 'Count').prop_name = 'count'

        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

        self.update_z_mode(context)

    def get_orientation_vector(self):
        if self.orient_axis == 'X':
            return Vector((1, 0, 0))
        elif self.orient_axis == 'Y':
            return Vector((0, 1, 0))
        else:
            return Vector((0, 0, 1))

    def is_same(self, v1, v2):
        if self.orient_axis == 'X':
            return v1.yz == v2.yz
        elif self.orient_axis == 'Y':
            return v1.xz == v2.xz
        else:
            return v1.xy == v2.xy

    def to_2d(self, v):
        if self.orient_axis == 'X':
            return v.yz
        elif self.orient_axis == 'Y':
            return v.xz
        else:
            return v.xy

    def is_same_edge(self, v1, v2, e1, e2):
        e1 = self.to_2d(e1)
        e2 = self.to_2d(e2)
        v1 = self.to_2d(v1)
        v2 = self.to_2d(v2)
        return is_in_segment(e1, e2, v1) or is_in_segment(e1, e2, v2)

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get()
        edges_in = self.inputs['Edges'].sv_get()
        offset_in = self.inputs['Offset'].sv_get()
        step_in = self.inputs['Step'].sv_get()
        multiplier_in = self.inputs['Multiplier'].sv_get()
        count_in = self.inputs['Count'].sv_get()
        curves_in = self.inputs['Curve'].sv_get(default=[[]])

        verts_out = []
        edges_out = []
        faces_out = []
        objects = match_long_repeat([verts_in, edges_in, offset_in, step_in, multiplier_in, count_in, curves_in])
        Z = self.get_orientation_vector()
        if self.z_mode == 'AXIS':
            z_idx = 'XYZ'.index(self.orient_axis)
        else:
            z_idx = None
        for verts, edges, offsets, steps, multipliers, counts, curves in zip(*objects):
            nverts = len(verts)
            offsets = cycle_for_length(offsets, nverts)
            steps = cycle_for_length(steps, nverts)
            multipliers = cycle_for_length(multipliers, nverts)
            counts = cycle_for_length(counts, nverts)
            if curves:
                curves = cycle_for_length(curves, nverts)
            
            bm = bmesh.new()
            bm.verts.ensure_lookup_table()
            
            verts_bm = []
            for i, v in enumerate(verts):
                if self.z_mode == 'AXIS':
                    verts_line = make_verts_axis(v, Z, self.make_basis, offsets[i], steps[i], counts[i])
                else:
                    verts_line = make_verts_curve(v, curves[i])
                verts_line_bm = []
                prev_bm_vert = None
                for v in verts_line:
                    bm_vert = bm.verts.new(v)
                    verts_line_bm.append(bm_vert)
                    bm.verts.ensure_lookup_table()
                    if prev_bm_vert is not None:
                        bm.edges.new((prev_bm_vert, bm_vert))
                    prev_bm_vert = bm_vert
                verts_bm.append(verts_line_bm)
            
            for i, j in edges:
                process_edge(bm, z_idx, verts_bm[i], verts_bm[j], steps[i], steps[j], multipliers[i], multipliers[j])

            verts_new, edges_new, _ = pydata_from_bmesh(bm)
            bm.free()

            verts_new, edges_new = intersect_edges_3d(verts_new, edges_new, 1e-3)
            verts_new, edges_new, _ = remove_doubles(verts_new, edges_new, [], 1e-3)

            if self.outputs['Faces'].is_linked:
                bm = bmesh_from_pydata(verts_new, edges_new, [], normal_update=True)
                if self.z_mode == 'AXIS':
                    for i, j in edges:
                        side_edges = []
                        v_i = Vector(verts[i])
                        v_j = Vector(verts[j])
                        #self.info("Check: [%s - %s]", v_i, v_j)
                        for bm_edge in bm.edges:
                            bm_v1 = bm_edge.verts[0].co
                            bm_v2 = bm_edge.verts[1].co
                            if self.is_same_edge(bm_v1, bm_v2, v_i, v_j):
                                side_edges.append(bm_edge)
                                #self.info("Yes: [%s - %s]", bm_v1, bm_v2)
                            else:
                                pass
                                #self.info("No: [%s - %s]", bm_v1, bm_v2)

                        bmesh.ops.holes_fill(bm, edges=side_edges, sides=4)
                        bm.edges.ensure_lookup_table()
                        bm.faces.ensure_lookup_table()
                else:
                    bmesh.ops.holes_fill(bm, edges=bm.edges[:], sides=4)

                verts_new, edges_new, faces_new = pydata_from_bmesh(bm)
                bm.free()
            else:
                faces_new = []
            
            verts_out.append(verts_new)
            edges_out.append(edges_new)
            faces_out.append(faces_new)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(SvFrameworkNode)

def unregister():
    bpy.utils.unregister_class(SvFrameworkNode)

