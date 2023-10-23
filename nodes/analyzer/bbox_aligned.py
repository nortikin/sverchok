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

from itertools import product
import numpy as np
import bpy
from bpy.props import BoolVectorProperty, EnumProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode

from sverchok.data_structure import dataCorrect, updateNode
from sverchok.utils.geom import bounding_box_aligned

class SvAlignedBBoxNode(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: Bbox 2D or 3D
    Tooltip: Get vertices bounding box (vertices, sizes, center)
    """
    bl_idname = 'SvAlignedBBoxNode'
    bl_label = 'Aligned Bounding Box'
    bl_icon = 'SHADING_BBOX'
    sv_icon = 'SV_BOUNDING_BOX'

    def update_sockets(self, context):
        updateNode(self, context)


    def draw_buttons(self, context, layout):
        pass

    def sv_init(self, context):
        son = self.outputs.new

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvStringsSocket', 'Faces')

        self.update_sockets(context)

    def process(self):
        inputs = self.inputs
        Vertices = inputs["Vertices"].sv_get(default=None)

        outputs = self.outputs
        if not outputs['Vertices'].is_linked or not all([Vertices,]):
            return
        
        lst_bba_vertices = []
        lst_bba_edges = []
        lst_bba_faces = []
        for verts in Vertices:
            bba = bounding_box_aligned(verts)
            lst_bba_vertices.append( bba[0].tolist() )
            lst_bba_edges.append( [[0,1], [1,2], [2,3], [3,0], [0,4], [1,5], [2,6], [3,7], [4,5], [5,6], [6,7], [7,4]])
            lst_bba_faces.append( [[0,3,2,1], [0,1,5,4], [1,2,6,5], [2,3,7,6], [3,0,4,7], [4,5,6,7]])

        outputs['Vertices'].sv_set(lst_bba_vertices)
        outputs['Edges'].sv_set(lst_bba_edges)
        outputs['Faces'].sv_set(lst_bba_faces)



def register():
    bpy.utils.register_class(SvAlignedBBoxNode)


def unregister():
    bpy.utils.unregister_class(SvAlignedBBoxNode)
