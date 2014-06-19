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
import ast
from bpy.props import IntProperty, FloatProperty, EnumProperty

from node_tree import SverchCustomTreeNode
from data_structure import (updateNode,
                            SvSetSocketAnyType, SvGetSocketAnyType)
import bpy, math, cmath, mathutils
from math import acos, acosh, asin, asinh, atan, atan2, \
                            atanh,ceil,copysign,cos,cosh,degrees,e, \
                            erf,erfc,exp,expm1,fabs,factorial,floor, \
                            fmod,frexp,fsum,gamma,hypot,isfinite,isinf, \
                            isnan,ldexp,lgamma,log,log10,log1p,log2,modf, \
                            pi,pow,radians,sin,sinh,sqrt,tan,tanh,trunc

sv_no_ve = [[(3, -1, 0),  (1, -1, 0),  (1, 2, 0),  (4, 2, 0),  (-1, -1, 0),
  (0, -1, 0),  (1, 0, 0),  (0, 2, 0),  (-1, 2, 0),  (-1, 0, 0),  (0, 0, 0),
  (3, 2, 0),  (2, 2, 0),  (3, 0, 0),  (3, 1, 0),  (7, -1, 0),  (8, -1, 0),
  (7, 2, 0),  (10, 2, 0),  (5, -1, 0),  (6, -1, 0),  (7, 0, 0),  (7, 1, 0),
  (6, 2, 0),  (5, 2, 0),  (5, 0, 0),  (5, 1, 0),  (10, 0, 0),  (10, 1, 0),
  (9, 2, 0),  (8, 2, 0),  (8, 0, 0),  (8, 1, 0),  (9, 0, 0)]]
  
sv_no_ed = [[[12, 11],  [5, 1],  [11, 3],  [5, 4],  [6, 1],  [7, 2],
  [8, 7],  [9, 8],  [10, 9],  [6, 10],  [14, 11],  [13, 0],  [14, 13],
  [30, 29],  [20, 15],  [22, 17],  [29, 18],  [28, 27],  [20, 19],
  [21, 15],  [22, 21],  [23, 17],  [24, 23],  [26, 24],  [25, 19],
  [26, 25],  [28, 18],  [32, 30],  [31, 16],  [32, 31],  [33, 31],
  [27, 33]]]

class SvFormulaShapeNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Formula shape '''
    bl_idname = 'SvFormulaShapeNode'
    bl_label = 'Formula Shape'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # vertex numers
    number = IntProperty(name='number', description='vertex number', default=100,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # scale
    scale = FloatProperty(name='scale', description='scale', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # sphere
    XX = FloatProperty(name='XX', description='XX factor', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # sphere
    YY = FloatProperty(name='YY', description='YY factor', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # sphere
    ZZ = FloatProperty(name='ZZ', description='ZZ factor', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    
    # formula for usual case
    # formulas contributed by Paul Kotelevets aka 1D
    list_formula = [    '(0,1,0)',
                        '((tan(i/10)+1), sin(i/2), sin(i/4))',
                        '(cos(i)*cos(i)*i/300, sin(i)*cos(i)*i/300, -(2*i)/(200+sin(i)))',
                        '(cos(i)*i/200, sin(i)*i/200, (-i*i)/90000)',
                        '(cos(i)*i/200, sin(i)*i/200, ((20000/(i*(1+i)-30000))))',
                        '(cos(i)*i/200, sin(i)*i/200, (200000/(i*i+50000)))',
                        '(cos(i/2)*i/200-cos(i/2), sin(i/2)*i/200-cos(i/2), -i/(300+sin(i/2)))',
                        '(cos(i/2)*i/200-cos(i/2), sin(i/2)*i/200-cos(i/2), -(1+sin(i/2)))',
                        '(cos(i/2)*i/200+cos(i/2), sin(i/2)*i/100*cos(i/2), -i/(300+i*sin(i/4)))',
                        '(cos(i/2)*i/200, sin(i/2)*i/200, -i/(3+i*sin(i)))',
                        '((i/6)*1, sin(i/6), sin(i/2))',
                        '(sin(i/2), tan(2+(i/3)), tan(2+(i/3)))',
                        '(sin(i/2), cos(i/2), tan(i/0.1))',
                        '(exp(i/200), cos(i/2),(sin(i)+cos(i))/(0+exp(i/120))',
                        '(sin(i)/(1+cos(i)), cos(i)/(1+sin(i)), tan(i/50)/exp(i/1000))',
                        '(sin(i/2), sin(i/3), sin(i/4))',
                        '(cos(i*2+i*i), cos(i/2+i*i), cos(i+i*2))',
                        '(sin(i/8+i*i), sin(i/8+i*i), cos(i))',
                        '(sin(i/9+i*i), sin(i/8+i*i), cos(i)*1.1)',
                        '(sin(i/3+i), sin(i/2+i), cos(i/6))',
                        '(sin(i/1+i), sin(i/3+i), cos(i/3))',
                        '(sin(i/2+i), sin(i/6+i), sin(i/6))',
                        '(sin(i/2-i), sin(i/6+i), cos(i/2))',
                        '(cos(i)*i/200, sin(i)*i/200, -i/200)',
                        '(cos(i/5), sin(i/5), -i/200)',
                        '(cos(i/2), sin(i/5), -i/300)',
                        '(sin(i/5-i/2), sin(i/5-i), sin(i/5))',
                        '(sin(i/5-i/2), sin(i/5-i), sin(i/8))',
                        '(sin(i/5-i/2), sin(i/5-i), sin(i/4))',
                        '(cos(i/2), sin(i/3), sin(i/2))',
                        '(cos(i/6), sin(i/4), sin(i/9))',
                        '(cos(500/i)*2, sin(500/i)*2, sin(90*i))',
                        '(pow(cos(i*2), 3), pow(sin(i*2), 3), 3*cos(sin(i*50)))',
                        '(sin(cos(i*2))*2, pow(sin(i*2), 5), 3*cos(sin(i*50)))',
                        '(sin(cos(i*2))*2, sin(sin(i*2)), 3*cos(sin(i*50)))',
                        '(tan(sin(i*2)), tan(cos(i*2)), 3*cos(sin(i*50)))',
                        '(tan(cos(i+i)), i/20, tan(cos(i+i/2)))',
                        '(tan(cos(i+i)), tan(sin(i+i)), tan(cos(i+i/2)))',
                        '(atan(cos(i+i)), atan(sin(i+i)), atan(cos(i+i/2)))',
                        '(tan(cos(i+i*4)), sin(tan(i+i*4)), tan(cos(i+i*5)))',
                        '(tan(cos(i+i*4)), tan(cos(i+i*5)), tan(cos(i+i*10)))',
                        '(tan(cos(i+i*7)), tan(cos(i+i*8)), tan(cos(i+i*16)))',
                        '(tan(cos(i+i*10)), tan(cos(i+i*2)), tan(cos(i+i*11)))',
                        '(1/log((1+ sin(i))), 1/log((1+ cos(i))), i/200)',
                        '(1/log((1+ sin(i))), cos(i), i/200)',
                        '(sin(i), -3*pi/4, sin(2*i*3.14)*sin(i*pi/2))',
                        '(sin(i), -3*pi/4, sin(2*i*3.14)*sin(i*3.14))',
                        #sphere
                        '(cos(XX) * cos(YY),  sin(XX) * sin(YY),  (i/100))',
                        '(log(exp(sin(XX)) *  exp(cos(YY))), log(exp(sin(XX)) * exp(sin(YY))), (exp(cos(XX))))',
                        '(sin(XX) * cos(YY), sin(XX) * sin(YY), cos(XX))',
                        '(sin(XX) * cos(YY), sin(XX) * sin(YY)+i/500, cos(XX))',
                        '(sin(XX) * cos(YY),  sin(XX) * sin(YY),  exp(cos(XX)))', #XX = 0.2*pi*i
                        '(sin(XX) * atan(YY), sin(XX) * sin(YY),  exp(cos(XX)))', ##YY = 3/pi*i || YY = XX/4 || XX = 58/pi*i  YY = 2*pi*i
                        '(tan(XX) * atan(YY), sin(XX) * sin(YY),  cos(XX))',
                        '(sin(XX) * cos(YY),  sin(XX) * sin(YY),  cos(XX))', #YY = XX/4 || YY = 3/pi*i ||YY = XX*5
                        '(sin(XX) * cos(YY) * log(YY, 2)/10, sin(YY) * sin(YY) * cos(XX), cos(XX))', ##sp16+16
                        '(sin(XX) * cos(YY) * sin(YY),  sin(YY) * sin(YY) * cos(XX),  cos(XX))',
                        '(sin(YY) * cos(YY) * sin(YY),  sin(YY) * sin(YY) * sin(XX),  cos(YY))',
                        '(sin(YY) * cos(YY) * sin(YY),  sin(YY) * sin(YY) * sin(XX),  cos(XX))',
                        '(sin(XX) * cos(YY),  sin(XX) * sin(YY),  cos(XX) * sin(2*XX))',
                        '(sin(XX) * cos(YY),  sin(XX) * sin(YY),  cos(XX) * sin(YY))',
                        '(sin(XX) * cos(YY),  sin(XX) * sin(YY) * sin(YY),  cos(XX) * sin(YY))',    #sp15
                        '(sin(XX) * cos(YY) * cos(YY),  sin(XX) * sin(YY) * sin(YY),  cos(XX)*sin(YY))',   #sp1, sp11, sp21, sp22
                        '(sin(XX) * cos(YY) * cos(XX),  sin(XX) * sin(YY) * sin(YY),  cos(XX)*sin(YY))',   #sp14, sp15
                        '(sin(YY) * cos(YY) * cos(XX),  sin(XX) * sin(YY) * sin(YY),  cos(XX)*sin(YY))',   #sp14, sp15
                        '(sin(YY) * cos(YY) * cos(XX),  sin(XX) * sin(YY) * sin(YY),  cos(XX))', ]         #sp4, sp3
                        
    formula_enum = [(i, 'formula1 {0}'.format(k), i, k) for k, i in enumerate(list_formula)]
    formula = EnumProperty(items=formula_enum, name='formula1')
    
    list_X_X = [    'XX',
                    'i',
                    'i**2',
                    'pi*i',
                    'i*i*pi',
                    'i/pi',
                    'pi/i',
                    'i*XX',
                    'i/XX',
                    'XX/i',
                    'XX*pi*i',
                    'XX/i/pi',
                    'XX/pi*i',
                    'i*pi/XX',
                    'i/pi*XX',
                    'pi/i*XX',
                    'i*XX/pi',
                    '1/i*XX*pi',
                    # logs
                    'log(pi*i)+XX',
                    'log(i*1)/tan(XX*i)*50',
                    '12/pi*log(i)*XX',
                    '2*pi*log(i)*XX',
                    # trigono
                    'tan(i)',
                    'sin(i)',
                    'cos(i)',
                    'sin(XX/pi*i)',
                    'sin(tan(XX*i))*50',
                    'cos(XX*pi*i)',
                    'tan(XX*i*pi)',
                    'tan(i)*XX',
                    ]
    
    X_X_enum = [(i, i, 'XX v{0}'.format(k), k) for k, i in enumerate(list_X_X)]
    X_X = EnumProperty(items=X_X_enum, name='X_X')
                    
    list_Y_Y = [    'YY',
                    'i',
                    'i**2',
                    'pi*i',
                    'i*i*pi',
                    'i/pi',
                    'pi/i',
                    'i*YY',
                    'i/YY',
                    'YY/i',
                    'YY*pi*i',
                    'YY/i/pi',
                    'YY/pi*i',
                    'i*pi/YY',
                    'i/pi*YY',
                    'pi/i*YY',
                    'i*YY/pi',
                    '1/i*YY*pi',
                    # logs
                    'log(pi*i)+YY',
                    'log(i*1)/tan(YY*i)*50',
                    '12/pi*log(i)*YY',
                    '2*pi*log(i)*YY',
                    # trigono
                    'tan(i)',
                    'sin(i)',
                    'cos(i)',
                    'sin(YY/pi*i)',
                    'sin(tan(YY*i))*50',
                    'cos(YY*pi*i)',
                    'tan(YY*i*pi)',
                    'tan(i)*YY',
                    ]
    
    Y_Y_enum = [(i, i, 'YY v{0}'.format(k), k) for k, i in enumerate(list_Y_Y)]
    Y_Y = EnumProperty(items=Y_Y_enum, name='Y_Y')
    
    list_Z_Z = [    'ZZ',
                    'i',
                    'i**2',
                    'pi*i',
                    'i*i*pi',
                    'i/pi',
                    'pi/i',
                    'i*ZZ',
                    'i/ZZ',
                    'ZZ/i',
                    'ZZ*pi*i',
                    'ZZ/i/pi',
                    'ZZ/pi*i',
                    'i*pi/ZZ',
                    'i/pi*ZZ',
                    'pi/i*ZZ',
                    'i*ZZ/pi',
                    '1/i*ZZ*pi',
                    # logs
                    'log(pi*i)+ZZ',
                    'log(i*1)/tan(ZZ*i)*50',
                    '12/pi*log(i)*ZZ',
                    '2*pi*log(i)*ZZ',
                    # trigono
                    'tan(i)',
                    'sin(i)',
                    'cos(i)',
                    'sin(ZZ/pi*i)',
                    'sin(tan(ZZ*i))*50',
                    'cos(ZZ*pi*i)',
                    'tan(ZZ*i*pi)',
                    'tan(i)*ZZ',
                    ]
    
    Z_Z_enum = [(i, i, 'ZZ v{0}'.format(k), k) for k, i in enumerate(list_Z_Z)]
    Z_Z = EnumProperty(items=Z_Z_enum, name='Z_Z')
    
    list_i = [      'n*f',
                    'n*f*ZZ',
                    'n*f*YY',
                    'n*f*XX',
                    'n*f*ZZ*XX*YY', ]
    
    i_enum = [(i, i, 'i override {0}'.format(k), k) for k, i in enumerate(list_i)]
    i_override = EnumProperty(items=i_enum, name='i_override')
    
    # end veriables enumerate
    
    def makeverts(self, vert, f, XX, YY, ZZ, formula, X_X, Y_Y, Z_Z, i_over):
        ''' main function '''
        out=[]
        for n in range(vert):
            i = eval(i_over)
            XX = eval(X_X)
            YY = eval(Y_Y)
            ZZ = eval(Z_Z)
            out.append(eval(formula))
        return [out]

    def init(self, context):
        self.inputs.new('StringsSocket', "Count").prop_name = 'number'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('StringsSocket', "XX").prop_name = 'XX'
        self.inputs.new('StringsSocket', "YY").prop_name = 'YY'
        self.inputs.new('StringsSocket', "ZZ").prop_name = 'ZZ'
        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self,context,layout):
        col = layout.column(align=True)
        col.prop(self, 'formula', text='Exp')
        row = col.row(align=True)
        row.prop(self, 'X_X', text='')
        row.prop(self, 'Y_Y', text='')
        row.prop(self, 'Z_Z', text='')
        col.prop(self, 'i_override', text='i')
    
    def update(self):
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
                out = self.makeverts(Count, Scale, SP1, SP2, SP3, self.formula, 
                                self.X_X, self.Y_Y, self.Z_Z, self.i_override)
                SvSetSocketAnyType(self, 'Verts', out)
            except:
                print('Cannot calculate, formula generator')
                out = sv_no_ve
                edg = sv_no_ed
                SvSetSocketAnyType(self, 'Verts', sv_no_ve)
                SvSetSocketAnyType(self, 'Edges', sv_no_ed)
                return

        if self.outputs['Edges'].is_linked:
                edg = [[[i-1, i] for i in range(1, Count)]]
                SvSetSocketAnyType(self, 'Edges', edg)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvFormulaShapeNode)


def unregister():
    bpy.utils.unregister_class(SvFormulaShapeNode)
if __name__ == '__main__':
    register()




### --------------------- Sphere setups: enable engine, Main sphere formula (further) and single preset to view this presets in action








#    i=i*1.2
#    tt = i*i
#    YY = 1/i*500
#    X = ( (sin(tt), sin(YY), cos(tt)) )
#    X = ( (sin(f), f/20, f/20 ))

### ------------- Over Spherical: This formulas can be used with sphericals variables presets, or this one:

#    f=1/1
#    i=i*0.5+0
#    tt = 2*pi*i #2=123456...
#    pp = log(i*3)/tan(tt)*0.1 #2=123456...

    


### ------------- Special: presets + formulas
#    i=i*0.8000+250
#    tt = 2*pi*i #2=123456...
#    pp = log(i*1)/tan(tt)*1 #2=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), exp(i/400))

#    i=i*1 # i=i*2
#    tt = 5*pi*i #2=123456... #5*pi*...
#    pp = log(i*4)/tan(tt)*1 #4=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), (i/100)+cos(tt))

#    i=i*0.5
#    tt = 6*pi*i #2=123456...
#    pp = log(i*3)/tan(tt)*1 #2=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), (i/100)+cos(tt))

#    i=i*0.5
#    tt = 8*pi*i #2=123456...
#    pp = log(i*3)/tan(tt)*2 #2=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), (i/100))

#    i=i*3 ## i-i*0.5
#    tt = 5*pi*i #2=123456...
#    pp = log(i*3)/tan(tt)*0.1 #2=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), (i/100))

#    i=i*0.5+220
#    tt = 5*pi*i #2=123456...
#    pp = log(i*3)/tan(tt)*0.1 #2=123456...
#    X = (cos(tt) * cos(pp), sin(tt)* sin(pp), (i/100))

#    i=i*1 # i=i*2
#    tt = 0.1*pi*i #2=123456... #5*pi*...
#    pp = log(i*4)/tan(tt)*1 #4=123456...
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), (i/100)+cos(tt))

#    i = i
#    tt = i*pi/2
#    pp = i*2
#    X = (sin(tt) * cos(pp), sin(tt)* sin(pp), cos(tt))

### ------------- Torus section:
#T1
#    tt = 90*3.1417*i #2
#    pp = 5/3.1417*i #25.5319
#    X = ((3+cos(pp)) * cos(tt)/2, (3+cos(pp))* sin(tt)/2, sin(pp)/2)
#T2
#    tt = 3.1417*i/3 #2
#    pp = 5/3.1417*i #25.5319
#    X = ((3+cos(pp)) * cos(tt)/2, (3+cos(pp))* sin(tt)/2, sin(pp)/2)
#T3
#    tt = i
#    pp = 12*i
#    X = ((3+cos(pp)) * cos(tt)/2, (3+cos(pp))* sin(tt)/2, sin(pp)/2)


