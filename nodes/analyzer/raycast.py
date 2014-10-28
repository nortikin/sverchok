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
import parser
import mathutils
from mathutils import Vector
from bpy.props import StringProperty, BoolProperty, EnumProperty
from sv_node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket, \
    MatrixSocket
from sv_data_structure import (updateNode, Vector_generate, SvSetSocketAnyType,
                            SvGetSocketAnyType, match_short, match_long_repeat)


class SvRayCastNode(bpy.types.Node, SverchCustomTreeNode):
    ''' RayCast Object '''
    bl_idname = 'SvRayCastNode'
    bl_label = 'raycast'
    bl_icon = 'OUTLINER_OB_EMPTY'

    modes = [
        ("Object",   "object_space",   "", 1),
        ("World",   "world_space",   "", 2),
    ]

    Itermodes = [
        ("match_short",   "match_short",   "", 1),
        ("match_long_repeat",   "match_long_repeat",  "", 2),
    ]

    Modes = EnumProperty(name="Raycast modes", description="Raycast modes",
                         default="Object", items=modes, update=updateNode)
    Iteration = EnumProperty(name="iteration modes",
                             description="Iteration modes",
                             default="match_short", items=Itermodes,
                             update=updateNode)
    formula = StringProperty(name='formula',
                             description='name of object to operate on \
                             ("object_space" mode only)', default='Cube',
                             update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="")
        row = layout.row(align=True)
        layout.prop(self, "Modes", "Raycast modes")
        layout.prop(self, "Iteration", "Iteration modes")

    def init(self, context):
        self.inputs.new('VerticesSocket', 'start', 'start')
        self.inputs.new('VerticesSocket', 'end', 'end')
        self.outputs.new('VerticesSocket', "HitP", "HitP")
        self.outputs.new('VerticesSocket', "HitNorm", "HitNorm")
        self.outputs.new('StringsSocket', "INDEX/Succes", "INDEX/Succes")

    def update(self):

        if not ('INDEX/Succes' in self.outputs):
            return

        start_links = self.inputs['start'].links
        if not (start_links and (type(start_links[0].from_socket) ==
                VerticesSocket)):
            return

        end_links = self.inputs['end'].links
        if not (end_links and (type(end_links[0].from_socket) ==
                VerticesSocket)):
            return

        self.process()

    def process(self):

        SSSAT = SvSetSocketAnyType
        bcsrc = bpy.context.scene.ray_cast
        outputs = self.outputs
        out = []
        OutLoc = []
        OutNorm = []
        INDSucc = []
        OutMatrix = []
        ObjectID = []

        st = Vector_generate(SvGetSocketAnyType(self, self.inputs['start']))
        en = Vector_generate(SvGetSocketAnyType(self, self.inputs['end']))
        start = [Vector(x) for x in st[0]]
        end = [Vector(x) for x in en[0]]
        if self.Iteration == 'match_short':
            temp = match_short([start, end])
            start, end = temp[0], temp[1]
        if self.Iteration == 'match_long_repeat':
            temp = match_long_repeat([start, end])
            start, end = temp[0], temp[1]

        if self.Modes == 'Object' and (self.formula in bpy.data.objects):

            if 'data.object' in outputs:
                outputs.remove(outputs['data.object'])

            if 'hited object matrix' in outputs:
                outputs.remove(outputs['hited object matrix'])

            obj = bpy.data.objects[self.formula]
            i = 0
            while i < len(end):
                out.append(obj.ray_cast(start[i], end[i]))
                i = i+1
            for i in out:
                OutNorm.append(i[1][:])
                INDSucc.append(i[2])
                OutLoc.append(i[0][:])

        if self.Modes == 'World':

            if 'data.object' not in outputs:
                outputs.new("VerticesSocket", "data.object")
            if 'hited object matrix' not in outputs:
                outputs.new("MatrixSocket", "hited object matrix")

            for i, last in enumerate(end):
                src = bcsrc(start[i], last)
                OutLoc.append(src[3][:])
                OutNorm.append(src[4][:])
                INDSucc.append(src[0])
                OutMatrix.append(src[2][:])
                OutMatrix = [[a[:], b[:], c[:], d[:]] for a, b, c, d in
                             OutMatrix]
                ObjectID.append(src[1])

        if outputs['HitP'].links:
            SSSAT(self, 'HitP', [OutLoc])
        if outputs['HitNorm'].links:
            SSSAT(self, 'HitNorm', [OutNorm])
        if outputs['INDEX/Succes'].links:
            SSSAT(self, 'INDEX/Succes', [INDSucc])
        if 'hited object matrix' in outputs:
                if outputs['hited object matrix'].links:
                    SSSAT(self, 'hited object matrix', OutMatrix)
        if 'data.object' in outputs:
                if outputs['data.object'].links:
                    SSSAT(self, 'data.object', [ObjectID])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvRayCastNode)


def unregister():
    bpy.utils.unregister_class(SvRayCastNode)
