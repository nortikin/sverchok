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

import bisect
import numpy as np

import bpy
from bpy.props import EnumProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, dataCorrect, repeat_last,
                            SvSetSocketAnyType, SvGetSocketAnyType)

# spline function modifed from
# from looptools 4.5.2 done by Bart Crouch


# calculates natural cubic splines through all given knots
def cubic_spline(locs, tknots):
    knots = list(range(len(locs)))

    n = len(knots)
    if n < 2:
        return False
    x = tknots[:]
    result = []
    for j in range(3):
        a = []
        for i in locs:
            a.append(i[j])
        h = []
        for i in range(n-1):
            if x[i+1] - x[i] == 0:
                h.append(1e-8)
            else:
                h.append(x[i+1] - x[i])
        q = [False]
        for i in range(1, n-1):
            q.append(3/h[i]*(a[i+1]-a[i]) - 3/h[i-1]*(a[i]-a[i-1]))
        l = [1.0]
        u = [0.0]
        z = [0.0]
        for i in range(1, n-1):
            l.append(2*(x[i+1]-x[i-1]) - h[i-1]*u[i-1])
            if l[i] == 0:
                l[i] = 1e-8
            u.append(h[i] / l[i])
            z.append((q[i] - h[i-1] * z[i-1]) / l[i])
        l.append(1.0)
        z.append(0.0)
        b = [False for i in range(n-1)]
        c = [False for i in range(n)]
        d = [False for i in range(n-1)]
        c[n-1] = 0.0
        for i in range(n-2, -1, -1):
            c[i] = z[i] - u[i]*c[i+1]
            b[i] = (a[i+1]-a[i])/h[i] - h[i]*(c[i+1]+2*c[i])/3
            d[i] = (c[i+1]-c[i]) / (3*h[i])
        for i in range(n-1):
            result.append([a[i], b[i], c[i], d[i], x[i]])
    splines = []
    for i in range(len(knots)-1):
        splines.append([result[i], result[i+n-1], result[i+(n-1)*2]])
    return(splines)


def eval_spline(splines, tknots, t_in):

    index = tknots.searchsorted(t_in, side='left') - 1
    index = index.clip(0, len(splines) - 1)
    out = np.zeros((len(t_in), 3))
    for j, n in enumerate(index):
        for i in range(3):
            #print(i,j,n)
            ax, bx, cx, dx, tx = splines[n][i]
            t_r = t_in[j] - tx
            out[j,i] = ax + t_r * (bx + t_r * (cx + t_r * dx))
    return out


class SvInterpolationNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Interpolate'''
    bl_idname = 'SvInterpolationNodeMK3'
    bl_label = 'Vector Interpolation 3'
    bl_icon = 'OUTLINER_OB_EMPTY'

    t_in = FloatProperty(name="t",
                         default=.5, min=0, max=1, precision=5,
                         update=updateNode)

    h = FloatProperty(default=.0001, precision=7, update=updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]
    mode = EnumProperty(name='Mode',
                        default="LIN", items=modes,
                        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Interval').prop_name = 't_in'
        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('VerticesSocket', 'Tanget')
        self.outputs.new('VerticesSocket', 'Norm Tanget')


    def draw_buttons(self, context, layout):
        #pass

        layout.prop(self, 'mode', expand=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'h')


    def process(self):
        if 'Norm Tanget' not in self.outputs:
            return
        if not any((s.is_linked for s in self.outputs)):
            return

        calc_tanget =  self.outputs['Tanget'].is_linked or self.outputs['Norm Tanget'].is_linked


        norm_tanget = self.outputs['Norm Tanget'].is_linked

        h = self.h

        if self.inputs['Vertices'].is_linked:
            verts = SvGetSocketAnyType(self, self.inputs['Vertices'])
            verts = dataCorrect(verts)
            t_ins = self.inputs['Interval'].sv_get()
            verts_out = []
            tanget_out = []
            norm_tanget_out = []
            for v, t_in in zip(verts, repeat_last(t_ins)):
                pts = np.array(v).T
                tmp = np.apply_along_axis(np.linalg.norm, 0, pts[:, :-1]-pts[:, 1:])
                t = np.insert(tmp, 0, 0).cumsum()
                t = t/t[-1]
                t_corr = np.array(t_in).clip(0, 1)
                # this should also be numpy
                if self.mode == 'LIN':
                    out = [np.interp(t_corr, t, pts[i]) for i in range(3)]
                    verts_out.append(list(zip(*out)))
                else:  # SPL

                    spl = cubic_spline(v, t)
                    out = eval_spline(spl, t, t_corr)
                    verts_out.append(out.tolist())
                    if calc_tanget:
                        t_ph = t_corr + h
                        t_mh = t_corr - h
                        t_less_than_0 = t_mh < 0.0
                        t_great_than_1 = t_ph > 1.0
                        t_mh[t_less_than_0] = 0.0
                        t_ph[t_great_than_1] = 1.0

                        tanget_ph = eval_spline(spl, t, t_ph)
                        tanget_mh = eval_spline(spl, t, t_mh)
                        tanget = tanget_ph - tanget_mh
                        tanget[t_less_than_0 + t_great_than_1] *= 2
                        if norm_tanget:
                            norm = np.linalg.norm(tanget, axis=1)
                            norm_tanget_out.append((tanget/norm[:,np.newaxis]).tolist())
                        tanget_out.append(tanget.tolist())

            if self.outputs['Vertices'].is_linked:
                SvSetSocketAnyType(self, 'Vertices', verts_out)
            if self.outputs['Tanget'].is_linked:
                SvSetSocketAnyType(self, 'Tanget', tanget_out)
            if self.outputs['Norm Tanget'].is_linked:
                SvSetSocketAnyType(self, 'Norm Tanget', norm_tanget_out)




def register():
    bpy.utils.register_class(SvInterpolationNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvInterpolationNodeMK3)
