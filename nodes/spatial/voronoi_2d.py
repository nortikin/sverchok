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
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat
from sverchok.utils.voronoi import voronoi_bounded


class Voronoi2DNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi vr
    Tooltip: Generate 2D Voronoi diagram for a set of vertices.
    """
    bl_idname = 'Voronoi2DNode'
    bl_label = 'Voronoi 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    clip: FloatProperty(
        name='clip', description='Clipping Distance',
        default=1.0, min=0, update=updateNode)

    bound_modes = [
            ('BOX', 'Bounding Box', "Bounding Box", 0),
            ('CIRCLE', 'Bounding Circle', "Bounding Circle", 1)
        ]

    bound_mode: EnumProperty(
        name = 'Bounds Mode',
        description = "Bounding mode",
        items = bound_modes,
        default = 'BOX',
        update = updateNode)

    draw_bounds: BoolProperty(
        name = "Draw Bounds",
        description = "Draw bounding edges",
        default = True,
        update = updateNode)

    draw_hangs: BoolProperty(
        name = "Draw Tails",
        description = "Draw lines that end outside of clipping area",
        default = True,
        update = updateNode)

    def update_sockets(self, context):
        if 'Faces' in self.outputs:
            self.outputs['Faces'].hide_safe = not self.make_faces
        if 'MaxSides' in self.inputs:
            self.inputs['MaxSides'].hide_safe = not self.make_faces
        updateNode(self, context)

    make_faces: BoolProperty(
        name = "Make faces",
        description = "Use `fill holes` function to make Voronoi polygons",
        default = False,
        update = update_sockets)

    ordered_faces : BoolProperty(
        name = "Ordered faces",
        description = "Make sure that faces are generated in the same order as corresponding input vertices",
        default = False,
        update = updateNode)

    max_sides: IntProperty(
        name='Sides',
        description='Maximum number of polygon sides',
        default=10,
        min=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'MaxSides').prop_name = 'max_sides'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")
        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.label(text="Bounds mode:")
        layout.prop(self, "bound_mode", text='')
        layout.prop(self, "draw_bounds")
        if not self.draw_bounds:
            layout.prop(self, "draw_hangs")
        layout.prop(self, "clip", text="Clipping")
        layout.prop(self, "make_faces")

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        if self.make_faces:
            layout.prop(self, 'ordered_faces')

    def process(self):

        if not self.inputs['Vertices'].is_linked:
            return

        if not self.outputs['Vertices'].is_linked:
            return

        points_in = self.inputs['Vertices'].sv_get()
        if 'MaxSides' in self.inputs:
            max_sides_in = self.inputs['MaxSides'].sv_get()
        else:
            max_sides_in = [[10]]

        pts_out = []
        edges_out = []
        faces_out = []
        for sites, max_sides in zip_long_repeat(points_in, max_sides_in):
            if isinstance(max_sides, (list, tuple)):
                max_sides = max_sides[0]

            new_vertices, edges, new_faces = voronoi_bounded(sites,
                        bound_mode=self.bound_mode,
                        clip=self.clip,
                        draw_bounds = self.draw_bounds,
                        draw_hangs = self.draw_hangs,
                        make_faces = self.make_faces,
                        ordered_faces = self.ordered_faces,
                        max_sides = max_sides)

            pts_out.append(new_vertices)
            edges_out.append(edges)
            faces_out.append(new_faces)
            #edges_out.append(finite_edges)

        # outputs
        self.outputs['Vertices'].sv_set(pts_out)
        self.outputs['Edges'].sv_set(edges_out)
        if 'Faces' in self.outputs and self.make_faces:
            self.outputs['Faces'].sv_set(faces_out)

def register():
    bpy.utils.register_class(Voronoi2DNode)

def unregister():
    bpy.utils.unregister_class(Voronoi2DNode)

