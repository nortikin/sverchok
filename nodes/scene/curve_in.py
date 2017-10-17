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
from mathutils import Vector
from mathutils.geometry import interpolate_bezier

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def offset(edgekeys, amount):
    return [[edge[0] + amount, edge[1] + amount] for edge in edgekeys]

def get_points_bezier(spline, clean=True):

    knots = spline.bezier_points
    if len(knots) < 2:
        return

    radii = []

    # verts per segment
    r = spline.resolution_u + 1

    # segments in spline
    segments = len(knots)

    if not spline.use_cyclic_u:
        segments -= 1

    master_point_list = []
    for i in range(segments):
        inext = (i + 1) % len(knots)

        knot1 = knots[i].co
        handle1 = knots[i].handle_right
        handle2 = knots[inext].handle_left
        knot2 = knots[inext].co

        bezier = knot1, handle1, handle2, knot2, r
        points = interpolate_bezier(*bezier)
        master_point_list.extend(points)

    # some clean up to remove consecutive doubles, this could be smarter...
    if clean:
        old = master_point_list
        good = [v for i, v in enumerate(old[:-1]) if not old[i] == old[i + 1]]
        good.append(old[-1])
        return good

    # makes edge keys, ensure cyclic
    Edges = [[i, i + 1] for i in range(n_verts - 1)]
    if spline.use_cyclic_u:
        Edges.append([i, 0])

    return master_point_list, Edges, radii



class SvCurveInputNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Curve data in '''
    bl_idname = 'SvCurveInputNode'
    bl_label = 'Curve Input'
    bl_icon = 'CURVE'

    def sv_init(self, context):
        new_i_put = self.inputs.new
        new_o_put = self.outputs.new

        new_i_put("SvObjectsSocket", "objects")
        new_o_put("VerticesSocket", "verts")
        new_o_put("VerticesSocket", "edges")
        new_o_put("VerticesSocket", "faces")
        new_o_put("VerticesSocket", "radii")
        new_o_put("VerticesSocket", "matrices")

    def draw_buttons(self, context, layout):
        ...

    def get_objects(self):
        _in = self.inputs[0]
        if _in.is_linked:
            objects = _in.sv_get()
        else:
            objects = [bpy.data.objects[obj.name] or obj in self.selected_objects]

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

            mtrx_out.append(obj.matrix_world[:])
            verts, edges, faces, radii = [], [], [], []

            # ('POLY', 'BEZIER', 'BSPLINE', 'CARDINAL', 'NURBS')
            for spline in obj.data.splines:

                if spline.type == 'BEZIER':
                    verts_part, edges_part, radii = get_points_bezier(spline, clean=True, calc_radii=calc_radii)

                elif spline.type == 'NURBS'
                    ...

                # empty means we don't offset the index
                edges.extend(offset(edges_part, len(verts)) if verts else edges_part)
                verts.extend(verts_part)
                # faces.extend(faces_part)
                # radii.extend(radii_part)

            ## pass all resulting subcurve data

            verts_out.append(verts)
            edges_out.append(edges)
            # faces_out.append(faces) 
            # radii_out.append(radii)
 

        _out['matrices'].sv_set(mtrx_out)


def register():
    bpy.utils.register_class(SvCurveInputNode)


def unregister():
    bpy.utils.unregister_class(SvCurveInputNode)
