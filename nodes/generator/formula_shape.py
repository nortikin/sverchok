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

import math, cmath
import ast
from math import (
    acos, acosh, asin, asinh, atan, atan2,
    atanh,ceil,copysign,cos,cosh,degrees,e,
    erf,erfc,exp,expm1,fabs,factorial,floor,
    fmod,frexp,fsum,gamma,hypot,isfinite,isinf,
    isnan,ldexp,lgamma,log,log10,log1p,log2,modf,
    pi,pow,radians,sin,sinh,sqrt,tan,tanh,trunc)

import bpy
from bpy.props import IntProperty, FloatProperty, EnumProperty
import mathutils

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

from sverchok.utils.modules.formula_shape_utils import (
    list_formulaX, list_formulaY, list_formulaZ,
    list_X_X, list_Y_Y, list_Z_Z,
    sv_no_ve, sv_no_ed)

def fix(s):
    return s.replace(' ', '')


class SvFormulaShapeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Formula shape '''
    bl_idname = 'SvFormulaShapeNode'
    bl_label = 'Formula shape'
    bl_icon = 'NONE'
    sv_icon = 'SV_FORMULA_SHAPE'

    # property setup
    formulaX_enum = [(fix(i), i, f'formulaX {k}', k) for k, i in enumerate(list_formulaX)]
    formulaY_enum = [(fix(i), i, f'formulaY {k}', k) for k, i in enumerate(list_formulaY)]
    formulaZ_enum = [(fix(i), i, f'formulaZ {k}', k) for k, i in enumerate(list_formulaZ)]
    X_X_enum = [(fix(i), i, i, k) for k, i in enumerate(list_X_X)]
    Y_Y_enum = [(fix(i), i, i, k) for k, i in enumerate(list_Y_Y)]
    Z_Z_enum = [(fix(i), i, i, k) for k, i in enumerate(list_Z_Z)]
    list_i = ['n*f', 'n*f*ZZ', 'n*f*YY', 'n*f*XX', 'n*f*ZZ*XX*YY']
    i_enum = [(i, i, f'i override {k}', k) for k, i in enumerate(list_i)]
    
    # property definitions
    number: IntProperty(name='number', description='vertex number', default=100,update=updateNode)
    scale: FloatProperty(name='scale', description='scale', default=1, update=updateNode)
    i_override: EnumProperty(items=i_enum, name='i_override', update=updateNode)
    ## sphere
    XX: FloatProperty(name='XX', description='XX factor', default=1, update=updateNode)
    YY: FloatProperty(name='YY', description='YY factor', default=1, update=updateNode)
    ZZ: FloatProperty(name='ZZ', description='ZZ factor', default=1, update=updateNode)
    formulaX: EnumProperty(items=formulaX_enum, name='formulaX', update=updateNode)
    formulaY: EnumProperty(items=formulaY_enum, name='formulaY', update=updateNode)
    formulaZ: EnumProperty(items=formulaZ_enum, name='formulaZ', update=updateNode)
    X_X: EnumProperty(items=X_X_enum, name='X_X', update=updateNode)
    Y_Y: EnumProperty(items=Y_Y_enum, name='Y_Y', update=updateNode)
    Z_Z: EnumProperty(items=Z_Z_enum, name='Z_Z', update=updateNode)
    
    
    def makeverts(self, vert, f, XX, YY, ZZ, fx,fy,fz, X_X, Y_Y, Z_Z, i_over):
        ''' main function '''
        out=[]
        for n in range(vert):
            i = eval(i_over)
            XX = eval(X_X)
            YY = eval(Y_Y)
            ZZ = eval(Z_Z)
            X = eval(fx)
            Y = eval(fy)
            Z = eval(fz)
            out.append((X,Y,Z))
        return [out]

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Count").prop_name = 'number'
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('SvStringsSocket', "XX").prop_name = 'XX'
        self.inputs.new('SvStringsSocket', "YY").prop_name = 'YY'
        self.inputs.new('SvStringsSocket', "ZZ").prop_name = 'ZZ'
        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")
        self.width = 400
    
    def draw_buttons(self,context,layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, 'formulaX', text='')
        row.prop(self, 'formulaY', text='')
        row.prop(self, 'formulaZ', text='')
        row = col.row(align=True)
        row.prop(self, 'X_X', text='')
        row.prop(self, 'Y_Y', text='')
        row.prop(self, 'Z_Z', text='')
        col.prop(self, 'i_override', text='i')
    
    def process(self):
        # inputs
        Count = self.inputs['Count'].sv_get()[0][0]
        Scale = self.inputs['Scale'].sv_get()[0][0]
        SP1 = self.inputs['XX'].sv_get()[0][0]
        SP2 = self.inputs['YY'].sv_get()[0][0]
        SP3 = self.inputs['ZZ'].sv_get()[0][0]

        #print(self.formula, self.XX_YY, self.i_override)
        # outputs
        if self.outputs['Verts'].is_linked:
            try:
                out = self.makeverts(Count, Scale, SP1, SP2, SP3, 
                                self.formulaX, self.formulaY, self.formulaZ, 
                                self.X_X, self.Y_Y, self.Z_Z, self.i_override)
                self.outputs['Verts'].sv_set(out)
            except:
                print('Cannot calculate, formula generator')
                self.outputs['Verts'].sv_set(sv_no_ve)
                self.outputs['Edges'].sv_set(sv_no_ed)
                return

        if self.outputs['Edges'].is_linked:
            edg = [[[i-1, i] for i in range(1, Count)]]
            self.outputs['Edges'].sv_set(edg)


def register():
    bpy.utils.register_class(SvFormulaShapeNode)


def unregister():
    bpy.utils.unregister_class(SvFormulaShapeNode)
    