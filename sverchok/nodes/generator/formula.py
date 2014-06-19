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
    tt = FloatProperty(name='tt', description='pistol tt', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # sphere
    pp = FloatProperty(name='pp', description='ppoe', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    # additional
    additional = FloatProperty(name='additional', description='additional', default=1,
                    options={'ANIMATABLE'},
                    update=updateNode)
    
    # formula for usual case
    list_formula = [    '(0,0,0)',
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
                        '(cos(tt) * cos(pp),  sin(tt) * sin(pp),  (i/100))',
                        '(log(exp(sin(tt)) *  exp(cos(pp))), log(exp(sin(tt)) * exp(sin(pp))), (exp(cos(tt))))',
                        #sphere
                        '(sin(tt) * cos(pp), sin(tt) * sin(pp), cos(tt))',
                        '(sin(tt) * cos(pp), sin(tt) * sin(pp)+i/500, cos(tt))',
                        '(sin(tt) * cos(pp),  sin(tt) * sin(pp),  exp(cos(tt)))', #tt = 0.2*pi*i
                        '(sin(tt) * atan(pp), sin(tt) * sin(pp),  exp(cos(tt)))', ##pp = 3/pi*i || pp = tt/4 || tt = 58/pi*i  pp = 2*pi*i
                        '(tan(tt) * atan(pp), sin(tt) * sin(pp),  cos(tt))',
                        '(sin(tt) * cos(pp),  sin(tt) * sin(pp),  cos(tt))', #pp = tt/4 || pp = 3/pi*i ||pp = tt*5
                        '(sin(tt) * cos(pp) * log(pp, 2)/10, sin(pp) * sin(pp) * cos(tt), cos(tt))', ##sp16+16
                        '(sin(tt) * cos(pp) * sin(pp),  sin(pp) * sin(pp) * cos(tt),  cos(tt))',
                        '(sin(pp) * cos(pp) * sin(pp),  sin(pp) * sin(pp) * sin(tt),  cos(pp))',
                        '(sin(pp) * cos(pp) * sin(pp),  sin(pp) * sin(pp) * sin(tt),  cos(tt))',
                        '(sin(tt) * cos(pp),  sin(tt) * sin(pp),  cos(tt) * sin(2*tt))',
                        '(sin(tt) * cos(pp),  sin(tt) * sin(pp),  cos(tt) * sin(pp))',
                        '(sin(tt) * cos(pp),  sin(tt) * sin(pp) * sin(pp),  cos(tt) * sin(pp))',    #sp15
                        '(sin(tt) * cos(pp) * cos(pp),  sin(tt) * sin(pp) * sin(pp),  cos(tt)*sin(pp))',   #sp1, sp11, sp21, sp22
                        '(sin(tt) * cos(pp) * cos(tt),  sin(tt) * sin(pp) * sin(pp),  cos(tt)*sin(pp))',   #sp14, sp15
                        '(sin(pp) * cos(pp) * cos(tt),  sin(tt) * sin(pp) * sin(pp),  cos(tt)*sin(pp))',   #sp14, sp15
                        '(sin(pp) * cos(pp) * cos(tt),  sin(tt) * sin(pp) * sin(pp),  cos(tt))', ]         #sp4, sp3
                        
    formula_enum = [(i, 'formula1 {0}'.format(k), i, k) for k, i in enumerate(list_formula)]
    formula = EnumProperty(items=formula_enum, name='formula1')
    
    list_tt_pp = [  '',
                    'i, i',
                    'pi*i , i/pi',
                    'tan(i) , 1/tan(i)',
                    'sin(i) , tan(i)',
                    'cos(aa*pi*i), aa/pi*i',
                    'cos(aa*pi*i), sin(aa/pi*i)',
                    'aa*pi*i, log(pi*i)+aa',
                    'aa*pi*i, aa/pi*i',
                    'i*2*pi, i',
                    'i/5*pi, i',
                    '2/pi*i, aa*pi*i',
                    '2/pi*i, aa*pi*i',
                    '2/pi*i, aa*pi*i',
                    'aa*pi*i, aa/pi*i',
                    '2*pi*log(i)*aa, 12/pi*log(i)*aa',
                    'aa*pi*i, sin(tan(tt))*15',
                    '12*pi*i, tan(tt)*18',
                    '3*pi*i, tan(tt)*10',
                    'aa*pi*i, log(i*1)/tan(tt)*aa',
                    'i, i*pi/aa',
                    'i*pi/2, i*2/pi',
                    'i*pi/2, i*2',
                    '14*pi*i, i',
                    'pi*6*i, i',
                    'i*pi*aa, pi/i*aa*10',
                    'i, i/2',
                    'i/2, i/2',
                    'pi*i, i/pi*6',
                    '500/i, i*3',
                    'i/2, 1/i*500',
                    'cos(i), i/3',
                    'i*pi*3, i*pi/4',
                    'i*i*pi, 1/i/pi', ]
    
    tt_pp_enum = [(i, 'formula1 {0}'.format(k), i, k) for k, i in enumerate(list_tt_pp)]
    tt_pp = EnumProperty(items=tt_pp_enum, name='tt_pp')
    
    list_i = [      '',
                    'i*1.5+1',
                    'i+aa',
                    'i*1.5+1',
                    'i*0.5000+218', ]
    
    i_enum = [(i, i, 'i override {0}'.format(k), k) for k, i in enumerate(list_i)]
    i_override = EnumProperty(items=i_enum, name='i_override')
    
    # end veriables enumerate
    
    def makeverts(self,vert,f,tt,pp,aa,formula,tt_pp,i_over):
        ''' main function '''
        out=[]
        for n in range(vert):
            i = n*f
            if i_over:
                i = eval(i_over)
            if tt_pp:
                tt, pp = eval(tt_pp)
            out.append(eval(formula))
        return [out]

    def init(self, context):
        self.inputs.new('StringsSocket', "Count").prop_name = 'number'
        self.inputs.new('StringsSocket', "Scale").prop_name = 'scale'
        self.inputs.new('StringsSocket', "SP1").prop_name = 'tt'
        self.inputs.new('StringsSocket', "SP2").prop_name = 'pp'
        self.inputs.new('StringsSocket', "SP3").prop_name = 'additional'
        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self,context,layout):
        row = layout.column(align=True)
        row.prop(self, 'formula', text='Exp')
        row.prop(self, 'tt_pp', text='tt_pp')
        row.prop(self, 'i_override', text='i')
    
    def update(self):
        # inputs
        Count = self.inputs['Count'].sv_get()[0][0]
        Scale = self.inputs['Scale'].sv_get()[0][0]
        SP1 = self.inputs['SP1'].sv_get()[0][0]
        SP2 = self.inputs['SP2'].sv_get()[0][0]
        SP3 = self.inputs['SP3'].sv_get()[0][0]
        #print(self.formula, self.tt_pp, self.i_override)
        # outputs
        if self.outputs['Verts'].is_linked:

            out = self.makeverts(Count, Scale, SP1, SP2, SP3, self.formula, 
                                self.tt_pp, self.i_override)
            
            SvSetSocketAnyType(self, 'Verts', out)

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
#    pp = 1/i*500
#    X = ( (sin(tt), sin(pp), cos(tt)) )
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


