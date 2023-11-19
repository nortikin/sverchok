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
from bpy.props import BoolVectorProperty, EnumProperty, BoolProperty, FloatProperty
from mathutils import Matrix

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_mesh_utils import mesh_join
from sverchok.utils.modules.matrix_utils import matrix_apply_np

from sverchok.data_structure import dataCorrect, updateNode, zip_long_repeat
from sverchok.utils.geom import bounding_box_aligned

class SvAlignedBBoxNode(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """
    Triggers: Bbox 2D or 3D
    Tooltip: Get vertices bounding box (vertices, sizes, center)
    """
    bl_idname = 'SvAlignedBBoxNode'
    bl_label = 'Aligned Bounding Box (Alpha)'
    bl_icon = 'SHADING_BBOX'
    sv_icon = 'SV_BOUNDING_BOX'

    mesh_join : BoolProperty(
        name = "merge",
        description = "If checked then join multiple mesh elements into one object",
        default = False,
        update = updateNode)
    
    factor : FloatProperty(
                name = "Factor",
                description = "Matrix interpolation to automatic calculated bounding box",
                default = 1.0,
                min=0.0, max=1.0, 
                update = updateNode)


    def update_sockets(self, context):
        updateNode(self, context)


    def draw_buttons(self, context, layout):
        layout.row().prop(self, 'mesh_join')
        pass

    def sv_init(self, context):
        son = self.outputs.new
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvMatrixSocket', 'Matrix')
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = 'factor'

        son('SvVerticesSocket', 'Vertices')
        son('SvStringsSocket', 'Edges')
        son('SvStringsSocket', 'Faces')
        son('SvMatrixSocket', "Matrix")

        son('SvStringsSocket', 'Length')
        son('SvStringsSocket', 'Width')
        son('SvStringsSocket', 'Height')
        

        self.update_sockets(context)

    def process(self):
        inputs = self.inputs
        Vertices = inputs["Vertices"].sv_get(default=None)
        Matrixes = inputs["Matrix"].sv_get(default=-1)
        if Matrixes==-1:
            Matrixes = [None]
        Factors  = inputs["Factor"].sv_get()

        outputs = self.outputs
        if not any( [o.is_linked for o in outputs]):
            return
        
        lst_bba_vertices = []
        lst_bba_edges = []
        lst_bba_faces = []
        lst_bba_matrix = []
        lst_bba_Length = []
        lst_bba_Width = []
        lst_bba_Height = []
        for verts, matrix, factor in zip_long_repeat(Vertices, Matrixes, Factors[0]):
            np_verts = np.array(verts)
            bba, mat, bbox_size = bounding_box_aligned(np_verts, evec_external=matrix, factor=factor)
            lst_bba_vertices.append( bba.tolist() )
            lst_bba_edges .append( [[0,1], [1,2], [2,3], [3,0], [0,4], [1,5], [2,6], [3,7], [4,5], [5,6], [6,7], [7,4]])
            lst_bba_faces .append( [[0,3,2,1], [0,1,5,4], [1,2,6,5], [2,3,7,6], [3,0,4,7], [4,5,6,7]])
            lst_bba_matrix.append( mat )
            lst_bba_Length.append( bbox_size[0] )
            lst_bba_Width .append( bbox_size[1] )
            lst_bba_Height.append( bbox_size[2] )

        if self.mesh_join:
            lst_bba_vertices, lst_bba_edges, lst_bba_faces = mesh_join(lst_bba_vertices, lst_bba_edges, lst_bba_faces)
            lst_bba_vertices, lst_bba_edges, lst_bba_faces = [lst_bba_vertices], [lst_bba_edges], [lst_bba_faces]
            # do not recalc length, width, height
            pass

        outputs['Vertices'].sv_set(lst_bba_vertices)
        outputs['Edges'].sv_set(lst_bba_edges)
        outputs['Faces'].sv_set(lst_bba_faces)
        outputs['Matrix'].sv_set(lst_bba_matrix)
        outputs['Length'].sv_set(lst_bba_Length)
        outputs['Width'].sv_set(lst_bba_Width)
        outputs['Height'].sv_set(lst_bba_Height)



def register():
    bpy.utils.register_class(SvAlignedBBoxNode)


def unregister():
    bpy.utils.unregister_class(SvAlignedBBoxNode)
