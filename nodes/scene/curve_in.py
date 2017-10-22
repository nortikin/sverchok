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
from sverchok.data_structure import updateNode
from sverchok.utils.sv_extended_curve_utils import get_points_bezier, get_points_nurbs, offset
from sverchok.nodes.number.range_float import frange_count

point_attrs = {'NURBS': 'points', 'BEZIER': 'bezier_points'}

def interpolate_radii(spline, segments, interpolation_type='LINEAR'):

    radii = []
    point_attr = point_attrs.get(spline.type, 'points')
    points = [p.radius for p in getattr(spline, point_attr)]

    if spline.use_cyclic_u:
        points.append(points[0])

    for idx in range(len(points)-1):
        params = points[idx], points[idx+1], segments+1
        if len(points) == 2 or (idx == (len(points)-2)):
            radii.extend(list(frange_count(*params)))
        else:
            radii.extend(list(frange_count(*params))[:-1])

    return radii


class SvCurveInputNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Curve data in '''
    bl_idname = 'SvCurveInputNode'
    bl_label = 'Curve Input'
    bl_icon = 'ROOTCURVE'

    object_names = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def sv_init(self, context):
        new_i_put = self.inputs.new
        new_o_put = self.outputs.new

        new_i_put("SvObjectSocket", "objects")
        new_o_put("VerticesSocket", "verts")
        new_o_put("StringsSocket", "edges")
        new_o_put("StringsSocket", "faces").hide_safe = True
        new_o_put("StringsSocket", "radii")
        new_o_put("MatrixSocket", "matrices")

    def draw_buttons(self, context, layout):
        ...

    def get_objects(self):
        _in = self.inputs[0]

        objects = _in.sv_get()
        if _in.is_linked or objects:
            pass
        else:
            objects = [bpy.data.objects[obj.name] or obj in self.object_names]

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

            mtrx_out.append([list(m) for m in obj.matrix_world])
            verts, edges, faces, radii = [], [], [], []
            curve = obj.data
            resolution = curve.render_resolution_u or curve.resolution_u
            # ('POLY', 'BEZIER', 'BSPLINE', 'CARDINAL', 'NURBS')
            for spline in obj.data.splines:
                
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
                    radii_part = interpolate_radii(spline, resolution, interpolation_type='LINEAR')
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
