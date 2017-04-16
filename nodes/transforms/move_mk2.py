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
from mathutils import Vector
from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode, StringsSocket, VerticesSocket
from sverchok.data_structure import updateNode, Vector_generate, match_long_repeat


class SvMoveNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Move vectors MK2 '''
    bl_idname = 'SvMoveNodeMK2'
    bl_label = 'Move'
    bl_icon = 'MAN_TRANS'

    mult_ = FloatProperty(name='multiplier',
                          default=1.0,
                          options={'ANIMATABLE'}, update=updateNode)

    separate = BoolProperty(name='separate', description='Separate UV coords',
                            default=False,
                            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'separate')

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', "vertices", "vertices")
        self.inputs.new('VerticesSocket', "vectors", "vectors")
        self.inputs.new('StringsSocket', "multiplier", "multiplier").prop_name = 'mult_'
        self.outputs.new('VerticesSocket', "vertices", "vertices")

    def process(self):
        # inputs
        vers = self.inputs['vertices'].sv_get()
        vecs = self.inputs['vectors'].sv_get()
        mult = self.inputs['multiplier'].sv_get()

        if self.outputs[0].is_linked:
            parameters = match_long_repeat([vers,vecs,mult])
            mov = [self.moved(vr, vc, mu) for vr, vc, mu in zip(*parameters)]
            self.outputs['vertices'].sv_set(mov)

    def moving(self, v, c, m):
        return (Vector(v) + Vector(c)*m)[:]

    def moved(self, vers, vecs, mult):
        moved = []
        params = match_long_repeat([vecs,mult])
        for c, m in zip(*params):
            moved_ = []
            for v in vers:
                moved_.append(self.moving(v, c, m))
            if self.separate:
                moved.append(moved_)
            else:
                moved.extend(moved_)
        return moved


        #old code for move.
        #rewriting implemented with needs of unification
        '''
        r = len(vers) - len(vecs)
        rm = len(vers) - len(mult)
        moved = []
        if r > 0:
            vecs.extend([vecs[-1] for a in range(r)])
        if rm > 0:
            mult.extend([mult[-1] for a in range(rm)])
        for i, ob in enumerate(vers):       # object
            d = len(ob) - len(vecs[i])
            dm = len(ob) - len(mult[i])
            if d > 0:
                vecs[i].extend([vecs[i][-1] for a in range(d)])
            if dm > 0:
                mult[i].extend([mult[i][-1] for a in range(dm)])
            temp = []
            for k, vr in enumerate(ob):     # vectors
                v = ((vr + vecs[i][k]*mult[i][k]))[:]
                temp.append(v)   # [0]*mult[0], v[1]*mult[0], v[2]*mult[0]))
            moved.append(temp)
        return moved
        '''


def register():
    bpy.utils.register_class(SvMoveNodeMK2)

def unregister():
    bpy.utils.unregister_class(SvMoveNodeMK2)
