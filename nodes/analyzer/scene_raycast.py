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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Scene '''
    bl_idname = 'SvRayCastSceneNode'
    bl_label = 'scene_raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def sv_init(self, context):
        sin = self.inputs.new
        so = self.outputs.new
        sin('VerticesSocket', 'start').use_prop = True
        sin('VerticesSocket', 'end').use_prop = True
        so('VerticesSocket', "HitP")
        so('VerticesSocket', "HitNorm")
        so('StringsSocket', "Succes")
        so("StringsSocket", "Objects")
        so("MatrixSocket", "hited object matrix")

    def process(self):
        so = self.outputs
        OutLoc = []
        OutNorm = []
        Succ = []
        ObjectID = []
        OutMatrix = []
        st = self.inputs['start'].sv_get()[0]
        en = self.inputs['end'].sv_get()[0]
        st, en = match_long_repeat([st, en])

        for i, last in enumerate(en):
            rc = bpy.context.scene.ray_cast(st[i], last)
            OutLoc.append(rc[3][:])
            OutNorm.append(rc[4][:])
            Succ.append(rc[0])
            ObjectID.append(rc[1])
            if so['hited object matrix'].is_linked:
                OutMatrix.append([[a[:], b[:], c[:], d[:]] for a, b, c, d in [rc[2][:]]])

        so['HitP'].sv_set([OutLoc])
        so['HitNorm'].sv_set([OutNorm])
        so['Succes'].sv_set([Succ])
        so['Objects'].sv_set(ObjectID)
        so['hited object matrix'].sv_set(OutMatrix)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
