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
        self.outputs.new('VerticesSocket', "Plane NormalsXYZ")

    def process(self):
        Inloc = self.inputs[0]
        if not Inloc.is_linked:
            return
        Loc, NormSingle, NormAll = self.outputs
        Locl, Nors, Norl = [], [], []

        for VList in Inloc.sv_get():
            points = np.array(VList)
            pmean = points.mean(axis=0)

            if Loc.is_linked:
                Locl.append(pmean.tolist())

            if NormSingle.is_linked:
                x = points - pmean
                eigenvalues, eigenvectors = np.linalg.eig(np.cov(x.T))
                Nors.append(eigenvectors[:, eigenvalues.argmin()].tolist())

            if NormAll.is_linked:
                x = points - pmean
                eigenvalues, eigenvectors = np.linalg.eig(np.cov(x.T))
                Norl.append(eigenvectors.tolist())

        Loc.sv_set([Locl])
        NormSingle.sv_set([Nors])
        NormAll.sv_set(Norl)


def register():
    bpy.utils.register_class(SvPlaneFit)


def unregister():
    bpy.utils.unregister_class(SvPlaneFit)
