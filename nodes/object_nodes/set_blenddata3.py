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

import sys

import bpy
from mathutils import Matrix
from bpy.props import StringProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, second_as_first_cycle as safc)

# pylint: disable=w0122
# pylint: disable=w0123
# pylint: disable=w0613

def mod_exec(self, context, objs):

    O, V = self.inputs
    Ov, Oo = self.outputs
    Prop = self.formula

    if isinstance(objs[0], list):
        if V.is_linked:
            v = V.sv_get()
            if "matrix" in Prop:
                v = [Matrix(i) for i in v]
                v = safc(objs, [v])
                for OBL, VALL in zip(objs, v):
                    VALL = safc(OBL, VALL)
                    exec("for i, i2 in zip(OBL, VALL):\n    i."+Prop+"= i2")
            else:
                if isinstance(v[0], list):
                    v = safc(objs, v)
                else:
                    v = safc(objs, [v])
                for OBL, VALL in zip(objs, v):
                    VALL = safc(OBL, VALL)
                    exec("for i, i2 in zip(OBL, VALL):\n    i."+Prop+"= i2")
        elif Ov.is_linked:
            Ov.sv_set(eval("[[i."+Prop+" for i in OBL] for OBL in objs]"))
        else:
            exec("for OL in objs:\n    for i in OL:\n        i."+Prop)
    else:
        if V.is_linked:
            v = V.sv_get()
            if "matrix" in Prop:
                v = [Matrix(i) for i in v]
                v = safc(objs, v)
                exec("for i, i2 in zip(objs, v):\n    i."+Prop+"= i2")
            else:
                if isinstance(v[0], list):
                    v = v[0]
                v = safc(objs, v)
                exec("for i, i2 in zip(objs, v):\n    i."+Prop+"= i2")
        elif Ov.is_linked:
            Ov.sv_set(eval("[i."+Prop+" for i in objs]"))
        else:
            exec("for i in objs:\n    i."+Prop)


def enumerate_props(data=None, filter_options=None):
    for i in data:
        if i.is_readonly:
            continue
        yield i.identifier

class SvSetDataObjectNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    ''' Set Object Props '''
    bl_idname = 'SvSetDataObjectNodeMK3'
    bl_label = 'Object ID Set MK3'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode_options = [(k, k, '', i) for i, k in enumerate(["Manual", "Auto"])]
    selected_mode = bpy.props.EnumProperty(
        items=mode_options, description="offers....", default="Manual", update=updateNode
    )

    data_mode = BoolProperty(default=True, update=updateNode)
    formula = StringProperty(name='formula', default='', update=updateNode)
    collection_name = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

    def pre_updateNode(self, context):
        ''' must rebuild for each update'''
        self.collection_name.clear()

        listed_props = []
        objs = self.inputs[0].sv_get()
        if objs:
            if isinstance(objs, list):
                if isinstance(objs[0], bpy.types.Object):
                    if self.data_mode:
                        names = enumerate_props(data=objs[0].data.bl_rna.properties)
                        listed_props = [("data."+name, name, "", idx) for idx, name in enumerate(names)]
                    else:
                        names = enumerate_props(data=objs[0].bl_rna.properties)
                        listed_props = [(name, name, "", idx) for idx, name in enumerate(names)]                    

        if listed_props:
            for prop_name in listed_props:
                self.collection_name.add().name = prop_name[0]

        # updateNode(self, context)

    def updateNode2(self, context):
        if self.formula != self.prop:
            self.formula = self.prop

    prop = StringProperty(name='formula_prop', default='', update=updateNode2)

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, "selected_mode", expand=True)
        
        row = layout.row()
        if self.selected_mode == 'Auto':
            # this mode lets you pick from auto generated RNA_properties for the data being inputted.
            row.prop_search(self, 'prop', self, 'collection_name', icon='OBJECT_DATA', text='')
            row.prop(self, "data_mode", text="", icon="SETTINGS")
        else:
            # this mode assumes you know what you're doing
            row.prop(self, "formula", text="prop")


    def sv_init(self, context):
        self.inputs.new('SvObjectSocket', 'Objects')
        self.inputs.new('StringsSocket', 'values')
        self.outputs.new('StringsSocket', 'outvalues')
        self.outputs.new('SvObjectSocket', 'Objects')

    def process(self):
        O, V = self.inputs
        Ov, Oo = self.outputs
        Prop = self.formula
        objs = O.sv_get()

        self.pre_updateNode(bpy.context)

        try:
            mod_exec(self, bpy.context, objs)
        except Exception as err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            print(sys.exc_info()[-1].tb_frame.f_code)
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno))

        if Oo.is_linked:
            Oo.sv_set(objs)


def register():
    bpy.utils.register_class(SvSetDataObjectNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvSetDataObjectNodeMK3)
