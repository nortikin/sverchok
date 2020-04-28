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
import mathutils

# from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.sv_animatable_nodes import SvAnimatableNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_extended_curve_utils import get_points_bezier, get_points_nurbs, offset
from sverchok.utils.modules.range_utils import frange_count

point_attrs = {'NURBS': 'points', 'BEZIER': 'bezier_points'}


def get_sections(knots, cyclic):
    sections = []
    if not cyclic:
        if len(knots) == 2:
            sections.append((0, 0, 1, 1))
        else:
            for i in range(len(knots)-1):
                if i == 0:
                    indices = i, i, i+1, i+2
                elif i == len(knots)-2:
                    indices = i-1, i, i+1, i+1
                else:
                    indices = i-1, i, i+1, i+2
                sections.append(indices)
    else:
        if len(knots) == 2:
            sections.append((1, 0, 1, 0))
        else:
            last_idx = len(knots)-1
            for i in range(len(knots)):
                if i == 0:
                    indices = last_idx, 0, 1, 2
                elif i == last_idx:
                    indices = last_idx-1, last_idx, 0, 1
                else:
                    indices = i-1, i, i+1, (i+2) % len(knots)
                sections.append(indices)

    return sections


def interpolate_catmul(knots, cyclic, num_segments):
    """
    from https://www.mvps.org/directx/articles/catmull/

    q(t) = 0.5 *( (2 * P1) +
                (-P0 + P2) * t +
                (2*P0 - 5*P1 + 4*P2 - P3) * t2 +
                (-P0 + 3*P1- 3*P2 + P3) * t3)
    """

    radii = []
    radii_add = radii.append

    sections = get_sections(knots, cyclic)
    theta = 1 / num_segments

    for idx, (p0, p1, p2, p3) in enumerate(sections):

        appendix = -1 if (cyclic or (idx < (len(sections) - 1))) else 0

        P0, P1, P2, P3 = knots[p0], knots[p1], knots[p2], knots[p3]
        for xt in range(num_segments + 1 + appendix):
            t = theta * xt
            t2 = t*t
            t3 = t2*t
            radt = 0.5*((2*P1)+(-P0+P2)*t+(2*P0-5*P1+4*P2-P3)*t2+(-P0+3*P1-3*P2+P3)*t3)
            radii_add(radt)

    return radii


def interpolate_linear(points, cyclic, num_segments):

    if cyclic:
        points.append(points[0])

    radii = []
    num_points = len(points)
    single_segment = num_points == 2

    for idx in range(num_points-1):
        params = points[idx], points[idx+1], num_segments+1
        rads = list(frange_count(*params))

        secondlast_point_of_non_cyclic = (idx == (num_points-2))
        keep_tail = single_segment or secondlast_point_of_non_cyclic

        if not keep_tail:
            rads.pop()

        radii.extend(rads)

    if cyclic:
        radii.pop()

    return radii


def interpolate_radii(spline, segments, interpolation_type='LINEAR'):
    """ get spline data into a format that is easily processed by interpolators"""

    cyclic = spline.use_cyclic_u
    point_attr = point_attrs.get(spline.type, 'points')
    points = [p.radius for p in getattr(spline, point_attr)]

    if interpolation_type == 'LINEAR':
        radii = interpolate_linear(points, cyclic, segments)

    elif interpolation_type == 'CATMUL':
        radii = interpolate_catmul(points, cyclic, segments)

    return radii


class SvCurveInputNode(bpy.types.Node, SverchCustomTreeNode, SvAnimatableNode):
    ''' Curve data in '''
    bl_idname = 'SvCurveInputNode'
    bl_label = 'Curve Input'
    bl_icon = 'ROOTCURVE'

    object_names: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    mode_options = [(k, k, '', i) for i, k in enumerate(["LINEAR", "CATMUL"])]

    selected_mode: bpy.props.EnumProperty(
        items=mode_options, description="offers....", default="LINEAR", update=updateNode
    )

    def sv_init(self, context):
        new_i_put = self.inputs.new
        new_o_put = self.outputs.new

        new_i_put("SvObjectSocket", "objects")
        new_o_put("SvVerticesSocket", "verts")
        new_o_put("SvStringsSocket", "edges")
        new_o_put("SvStringsSocket", "faces").hide_safe = True
        new_o_put("SvStringsSocket", "radii")
        new_o_put("SvMatrixSocket", "matrices")

    def draw_buttons(self, context, layout):
        self.animatable_buttons(layout, icon_only=True)
        layout.prop(self, 'selected_mode', expand=True)

    def get_objects(self):
        _in = self.inputs[0]

        objects = _in.sv_get()
        if _in.is_linked or objects:
            pass
        else:
            objects = [bpy.data.objects[obj.name] for obj in self.object_names]

        filtered_objects = [obj for obj in objects if obj.type == 'CURVE']
        if len(filtered_objects) < len(objects):
            print('one object in selection is not a curve, remove it and try again')
            return []

        return filtered_objects


    def process(self):
        _out = self.outputs
        objects = self.get_objects()

        calc_radii = _out['radii'].is_linked
        edges_out, verts_out, faces_out, radii_out, mtrx_out = [], [], [], [], []

        for obj in objects:

            ## collect all data we can get from the subcurve(s)

            mtrx_out.append(obj.matrix_world)
            verts, edges, faces, radii = [], [], [], []
            curve = obj.data
            resolution = curve.render_resolution_u or curve.resolution_u
            # ('POLY', 'BEZIER', 'BSPLINE', 'CARDINAL', 'NURBS')
            for spline in curve.splines:

                if spline.type == 'BEZIER':
                    verts_part, edges_part, radii = get_points_bezier(spline, calc_radii=calc_radii)
                elif spline.type == 'NURBS':
                    verts_part, edges_part, radii = get_points_nurbs(spline, resolution, calc_radii=calc_radii)
                else:
                    # maybe later?
                    continue

                # empty means we don't offset the index
                edges.extend(offset(edges_part, len(verts)) if verts else edges_part)
                verts.extend(verts_part)
                # faces.extend(faces_part)
                if _out['radii'].is_linked:
                    radii_part = interpolate_radii(spline, resolution, interpolation_type=self.selected_mode)
                    radii.extend(radii_part)

            ## pass all resulting subcurve data

            verts_out.append(verts)
            edges_out.append(edges)
            # faces_out.append(faces)
            radii_out.append(radii)


        _out['matrices'].sv_set(mtrx_out)
        _out['verts'].sv_set(verts_out)
        _out['edges'].sv_set(edges_out)
        _out['radii'].sv_set(radii_out)


def register():
    bpy.utils.register_class(SvCurveInputNode)


def unregister():
    bpy.utils.unregister_class(SvCurveInputNode)
