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
from mathutils import Vector
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket, MatrixSocket
from sverchok.data_structure import (updateNode, Vector_generate, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Scene '''
    bl_idname = 'SvRayCastSceneNode'
    bl_label = 'scene_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'start').use_prop = True
        self.inputs.new('VerticesSocket', 'end').use_prop = True
        self.outputs.new('VerticesSocket', "HitP")
        self.outputs.new('VerticesSocket', "HitNorm")
        self.outputs.new('StringsSocket', "Succes")
        self.outputs.new("SvObjectSocket", "data.object")
        self.outputs.new("MatrixSocket", "hited object matrix")

    def process(self):

        outputs = self.outputs
        OutLoc = []
        OutNorm = []
        Succ = []
        ObjectID = []
        OutMatrix = []
        st = Vector_generate(self.inputs['start'].sv_get())
        en = Vector_generate(self.inputs['end'].sv_get())
        start = [Vector(x) for x in st[0]]
        end = [Vector(x) for x in en[0]]
        if len(start) != len(end):
            temp = match_long_repeat([start, end])
            start, end = temp[0], temp[1]

        for i, last in enumerate(end):
            src = bpy.context.scene.ray_cast(start[i], last)
            OutLoc.append(src[3][:])
            OutNorm.append(src[4][:])
            Succ.append(src[0])
            OutMatrix.append(src[2][:])
            OutMatrix = [[a[:], b[:], c[:], d[:]] for a, b, c, d in OutMatrix]
            ObjectID.append(src[1])

        outputs['HitP'].sv_set([OutLoc])
        outputs['HitNorm'].sv_set([OutNorm])
        outputs['Succes'].sv_set([Succ])
        outputs['data.object'].sv_set(ObjectID)
        outputs['hited object matrix'].sv_set(OutMatrix)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
