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
# from mathutils import Vector, Matrix
import numpy as np
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode)


class SvPlaneFit(bpy.types.Node, SverchCustomTreeNode):
    ''' Fit a plane into vertices '''
    bl_idname = 'SvPlaneFit'
    bl_label = 'Fit Plane to Verts'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "Vertex Cloud")
        self.outputs.new('VerticesSocket', "Plane Center")
        self.outputs.new('VerticesSocket', "Plane Normal")
       # self.outputs.new('MatrixSocket', "Plane Matrix")

    def process(self):
        Inloc = self.inputs[0]
        if not Inloc.is_linked:
            return
        Loc, Norm = self.outputs   # Loc, Norm, Mat = self.outputs
        Locl, Norl = [], []   # Locl, Norl, Matl = [], [], []
        for VList in Inloc.sv_get():
            points = np.array(VList)
            ctr = points.mean(axis=0)
            x = points - ctr
            M = np.cov(x.T)
            eigenvalues, eigenvectors = np.linalg.eig(M)
            normal = eigenvectors[:, eigenvalues.argmin()]
            if Loc.is_linked:
                Locl.append(ctr.tolist())
            if Norm.is_linked:
                Norl.append(normal.tolist())
          #  if Mat.is_linked:
          #      nor = Vector(normal)
          #      n = nor.to_track_quat('Z', 'Y')
          #      m = Matrix.Translation(ctr) * n.to_matrix().to_4x4()
          #      Matl.append([i[:] for i in m])
        Loc.sv_set(Locl)
        Norm.sv_set(Norl)
       # Mat.sv_set(Matl)


def register():
    bpy.utils.register_class(SvPlaneFit)


def unregister():
    bpy.utils.unregister_class(SvPlaneFit)
