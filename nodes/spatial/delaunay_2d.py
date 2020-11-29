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
from bpy.props import FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.voronoi import Site, computeVoronoiDiagram, computeDelaunayTriangulation

# computeDelaunayTriangulation
class DelaunayTriangulation2DNode(bpy.types.Node, SverchCustomTreeNode):
    '''dea Verts. Triangulation '''
    bl_idname = 'DelaunayTriangulation2DNode'
    bl_label = 'Delaunay 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_DELAUNAY'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Polygons")

    def process(self):

        if not self.inputs['Vertices'].is_linked:
            return
        if not self.outputs['Polygons'].is_linked:
            return

        tris_out = []
        points_in = []
        points_in = self.inputs['Vertices'].sv_get()

        for obj in points_in:
            pt_list = [Site(pt[0], pt[1]) for pt in obj]
            res = computeDelaunayTriangulation(pt_list)
            tris_out.append([tri for tri in res if -1 not in tri])


        self.outputs['Polygons'].sv_set(tris_out)

def register():
    bpy.utils.register_class(DelaunayTriangulation2DNode)


def unregister():
    bpy.utils.unregister_class(DelaunayTriangulation2DNode)

