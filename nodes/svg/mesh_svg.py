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

from math import sin, cos, pi, degrees, radians
from mathutils import Vector, Matrix
import bpy
from bpy.props import EnumProperty, BoolProperty, IntProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (fullList, match_long_repeat, updateNode)
from sverchok.data_structure import match_long_repeat as mlr, enum_item_4

z_func_dict = {
    "MIN": min,
    "MAX": max,
    "AVR": lambda x: sum(x)/len(x),
    "SUM": sum
}
z_sort_mode_items = [
    ("MIN",         "Z Minimum",        "", 1),
    ("MAX",         "Z Maximum",        "", 2),
    ("AVR",         "Z Average",        "", 3),
    ("SUM",         "Z Sum",            "", 4)
    #("ACC",         "Accumulate",     "", 5),
]
def verts_pol(polygon, verts):
    return [verts[c] for c in polygon]

def draw_pols(verts, polygons, attributes, document):
    svg = ''
    scale = document.scale
    height = document.height
    func = draw_edge if len(polygons[0]) < 3 else draw_pol
    for p, atts in zip(*mlr([polygons, attributes])):
        svg += func(verts_pol(p, verts), scale, height)

        if atts:
            svg += atts.draw(document)
        svg += '/>'

    return svg

def draw_pol(p, scale, height):
    svg = '<polygon points="'
    for c in p:
        svg += f' {c[0]* scale} {height- c[1] * scale}'

    svg += ' "\n'
    return svg

def draw_edge(p, scale, height):
    svg = '<line '
    svg += f'x1="{p[0][0]* scale}" y1="{height- p[0][1]* scale}" '
    svg += f'x2="{p[1][0]* scale}" y2="{height- p[1][1]* scale}" '
    return svg

def draw_sorted_pols(verts, polygons, attributes, document, z_func):
    v_pols = []
    z_key = []
    svg = ''

    for p in polygons:
        v_pol = []
        z_c = []
        for c in p:
            v_pol.append(verts[c])
            z_c.append(verts[c][2])
        v_pols.append(v_pol)
        # z_key.append(sum(z_c)/len(z_c))
        z_key.append(z_func(z_c))
    sorted_v_pols = [x for _, x in sorted(zip(z_key, v_pols))]


    func = draw_edge if len(polygons[0]) < 3 else draw_pol
    scale = document.scale
    height = document.height
    for p, atts in zip(*mlr([sorted_v_pols, attributes])):
        svg += func(p, scale, height)

        if atts:
            svg += atts.draw(document)
        svg += '/>\n'
    return svg


class SvgMesh():
    def __repr__(self):
        return "<SVG Mesh>"
    def __init__(self, verts, polygons, attributes, node):
        self.verts = verts
        self.polygons = polygons
        self.attributes = attributes
        self.node = node


    def draw(self, document):

        verts = self.verts
        svg = '<g>\n'
        if self.node.elements_sort:
            z_func = z_func_dict[self.node.sort_mode]
            if self.node.invert_sort:
                z_func_sort = lambda x: -1 * z_func(x)
            else:
                z_func_sort = z_func
            svg += draw_sorted_pols(verts, self.polygons, self.attributes, document, z_func_sort)
        else:
            svg += draw_pols(verts, self.polygons, self.attributes, document)
        svg += '</g>'
        return svg

def user_ortho_projection(verts, plane, offset):
    inverted_matrix = plane.inverted()
    vs = []
    for v in verts:
        vs.append(offset @ inverted_matrix @ Vector(v))
    return vs

ortho_projection_func_dict = {
    'XY': lambda vs, plane, offset: [offset @ Vector(v)  for v in vs],
    'XZ': lambda vs, plane, offset: [offset @ Vector([v[0], v[2], v[1]])  for v in vs],
    'YZ': lambda vs, plane, offset: [offset @ Vector([v[1], v[2], v[0]]) for v in vs],
    'User': user_ortho_projection
}

def perspective_proyection(verts, plane, offset):
    origin = plane.decompose()[0]
    normal = ((plane @ Vector((0, 0, 1))) - origin).normalized()
    plane_point = origin
    focal_point = origin + normal
    inverted_matrix = plane.inverted()

    vs = []

    for v in verts:
        v_v = Vector(v)
        ray = v_v - focal_point
        line_dir = ray.normalized()
        normal_dot_ray_dir = normal.dot(line_dir)
        if (normal_dot_ray_dir == 0):
            new_v = v
        else:
            t = (normal.dot(plane_point) - normal.dot(v)) / normal_dot_ray_dir
            new_v = v_v + (line_dir * t)

        point_2d = offset @ inverted_matrix @ new_v
        vs.append([point_2d[0], point_2d[1], -ray.length])

    return vs

class SvSvgMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Polygons/Edges SVG
    Tooltip: Generate SVG Mesh Data
    """
    bl_idname = 'SvSvgMeshNode'
    bl_label = 'Mesh SVG'
    bl_icon = 'MESH_CIRCLE'
    sv_icon = 'SV_MESH_SVG'

    elements_sort: BoolProperty(
        name='Elements Sort',
        description='Sort Polygons / Edges according to distance',
        update=updateNode)
    sort_mode: EnumProperty(
        name="Sort mode",
        description="How polygons/ edges are sorted",
        items=z_sort_mode_items, update=updateNode)

    invert_sort: BoolProperty(name='Invert Order', update=updateNode)

    def update_sockets(self, context):
        self.inputs['Projection Plane'].hide_safe = self.projection_mode== "Orthogrphic" and self.projection_plane != 'User'
        updateNode(self, context)

    projection_mode: EnumProperty(
        name='Mode',
        description='Projection mode',
        items=enum_item_4(["Orthogrphic", 'Perspective']),
        update=update_sockets)

    projection_plane: EnumProperty(
        name='Plane',
        description='Projection plane',
        items=enum_item_4(['XY', 'XZ', 'YZ', 'User']),
        update=update_sockets)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Polygons / Edges")
        self.inputs.new('SvMatrixSocket', "Projection Plane")
        self.inputs["Projection Plane"].hide_safe = True
        self.inputs.new('SvMatrixSocket', "Offset")
        self.inputs.new('SvSvgSocket', "Fill / Stroke")

        self.outputs.new('SvSvgSocket', "SVG Objects")
        self.outputs.new('SvVerticesSocket', "Verts to project")

    def draw_buttons(self,context,layout):
        layout.prop(self, 'projection_mode')
        if self.projection_mode == 'Orthogrphic':
            layout.prop(self, 'projection_plane')
        layout.prop(self, 'elements_sort')
        if self.elements_sort:
            layout.prop(self, 'sort_mode')
            layout.prop(self, 'invert_sort')

    def process(self):

        if not self.outputs[0].is_linked:
            return

        verts_in = self.inputs['Vertices'].sv_get(deepcopy=True)
        pols_in = self.inputs['Polygons / Edges'].sv_get(deepcopy=True)
        planes_in = self.inputs['Projection Plane'].sv_get(deepcopy=True, default=[Matrix()])
        offset_in = self.inputs['Offset'].sv_get(deepcopy=True, default=[Matrix()])
        atts_in = self.inputs['Fill / Stroke'].sv_get(deepcopy=False, default=[[None]])

        shapes = []
        verts_to_project = []
        if self.projection_mode == 'Orthogrphic':
            projection_func = ortho_projection_func_dict[self.projection_plane]
        else:
            projection_func = perspective_proyection

        for verts, pols, p_plane, offset, atts in zip(*mlr([verts_in, pols_in, planes_in, offset_in, atts_in])):

            verts_p = projection_func(verts, p_plane, offset)
            verts_to_project.append(verts_p)
            shapes.append(SvgMesh(verts_p, pols, atts, self))

        self.outputs[0].sv_set(shapes)
        self.outputs[1].sv_set(verts_to_project)



def register():
    bpy.utils.register_class(SvSvgMeshNode)


def unregister():
    bpy.utils.unregister_class(SvSvgMeshNode)
