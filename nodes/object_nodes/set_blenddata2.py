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

from textwrap import dedent

import bpy
from mathutils import Matrix
from bpy.props import StringProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)

# pylint: disable=w0122
# pylint: disable=w0123
# pylint: disable=w0613


class SvSetDataObjectNodeMK2(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNodeMK2'
    bl_label = 'Object ID Set'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_OBJECT_ID_SET'

    formula: StringProperty(name='formula', default='delta_location', update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula", text="")

    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('SvStringsSocket', 'values')
        self.outputs.new('SvStringsSocket', 'outvalues')
        self.outputs.new('SvObjectSocket', 'Objects')

    def process(self):
        O, V = self.inputs
        Ov, Oo = self.outputs
        Prop = self.formula
        objs = O.sv_get()
        if isinstance(objs[0], list):

            if V.is_linked:

                # ensure correct V nesting.
                v = V.sv_get()
                if "matrix" in Prop:
                    v = safc(objs, [v])
                else:
                    v = safc(objs, v) if isinstance(v[0], list) else safc(objs, [v])

                # execute
                for OBL, VALL in zip(objs, v):
                    VALL = safc(OBL, VALL)
                    exec(dedent(f"""\
                    for i, i2 in zip(OBL, VALL):
                        i.{Prop} = i2"""))                        

            elif Ov.is_linked:
                Ov.sv_set(eval(f"[[i.{Prop} for i in OBL] for OBL in objs]"))
            else:
                exec(dedent(f"""\
                for OL in objs:
                    for i in OL:
                        i.{Prop}"""))

        else:

            if V.is_linked:
                
                # ensure correct V nesting.
                v = V.sv_get()
                if "matrix" in Prop:
                    v = safc(objs, v)
                else:
                    if isinstance(v[0], list):
                        v = v[0]
                    v = safc(objs, v)

                # execute                    
                exec(dedent(f"""\
                for i, i2 in zip(objs, v):
                    i.{Prop} = i2"""))

            elif Ov.is_linked:
                Ov.sv_set(eval(f"[i.{Prop} for i in objs]"))
            else:
                exec(dedent(f"""\
                for i in objs:
                    i.{Prop}"""))
        
        if Oo.is_linked:
            Oo.sv_set(objs)


def register():
    bpy.utils.register_class(SvSetDataObjectNodeMK2)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNodeMK2)
