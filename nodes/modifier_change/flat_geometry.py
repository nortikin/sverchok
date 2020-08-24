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

from mathutils import Vector
import bpy
from bpy.props import  FloatVectorProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat as mlr, enum_item_4


def ortho_proyection(verts_in, plane_in):
    verts_out = []
    z_coord_out = []
    for verts, plane in zip(*mlr([verts_in, plane_in])):
        inverted_matrix = plane.inverted()
        vs = []
        zs = []
        for v in verts:
            new_v = Vector(v) @ inverted_matrix
            z_c = new_v[2]
            vs.append([new_v[0], new_v[1], 0])
            zs.append(z_c)
        verts_out.append(vs)
        z_coord_out.append(zs)

    return verts_out, z_coord_out

def perspective_proyection(verts_in, plane_in, distance):
    verts_out = []
    z_coord_out = []
    for verts, plane in zip(*mlr([verts_in, plane_in])):
        origin = plane.decompose()[0]
        normal = ((plane @ Vector((0, 0, 1))) - origin).normalized()
        plane_point = origin
        focal_point = origin + normal * distance
        inverted_matrix = plane.inverted()

        vs = []
        zs = []
        for v in verts:
            v_v = Vector(v)
            ray = v_v - focal_point
            line_dir = ray.normalized()
            normal_dot_line_dir = normal.dot(line_dir)
            if normal_dot_line_dir == 0:
                new_v = v
            else:
                t = (normal.dot(plane_point) - normal.dot(v)) / normal_dot_line_dir
                new_v = v_v + (line_dir * t)

            point_2d = inverted_matrix @ new_v
            vs.append([point_2d[0], point_2d[1], 0])

            zs.append(ray.length)
        verts_out.append(vs)
        z_coord_out.append(zs)

    return verts_out, z_coord_out


class SvFlatGeometryNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 3D to 2D
    Tooltip: Proyection of 3d vertices into defined plane
    """
    bl_idname = 'SvFlatGeometryNode'
    bl_label = 'Flat Geometry'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_FLAT_GEOMETRY'

    projection_mode: EnumProperty(
        name='Mode',
        description='Projection mode',
        items=enum_item_4(["Orthogrphic", 'Perspective']),
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvMatrixSocket', 'Plane Matrix')


        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Z coord')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'projection_mode')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return
        if self.inputs['Vertices'].is_linked:
            verts_in = self.inputs['Vertices'].sv_get()
            plane_in = self.inputs['Plane Matrix'].sv_get()
            if self.projection_mode == 'Orthogrphic':
                verts_out, z_coord_out = ortho_proyection(verts_in, plane_in)
            else:
                verts_out, z_coord_out = perspective_proyection(verts_in, plane_in, 2)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Z coord'].sv_set(z_coord_out)



def register():
    bpy.utils.register_class(SvFlatGeometryNode)


def unregister():
    bpy.utils.unregister_class(SvFlatGeometryNode)
