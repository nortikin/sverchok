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

    n = len(locs)
    if n < 2:
        return False

    result = []
    # a = locs
    h = tknots[1:]-tknots[:-1]
    h[h==0] = 1e-8
    q = np.zeros((n-1,3))
    q[1:] = 3/h[1:,np.newaxis] * (locs[2:] - locs[1:-1]) - 3/h[:-1,np.newaxis] * (locs[1:-1]-locs[:-2])

    l = np.zeros((n, 3 ))
    l[0,:] = 1.0
    u = np.zeros((n-1, 3))
    z = np.zeros((n, 3))

    for i in range(1, n-1):
        l[i] = 2*(tknots[i+1]-tknots[i-1]) - h[i-1]*u[i-1]
        tmp = l[i]
        tmp[tmp==0] = 1e-8
        u[i] = h[i] / l[i]
        z[i] = (q[i] - h[i-1] * z[i-1]) / l[i]
    l[-1,:] = 1.0
    z[-1] = 0.0

    b = np.zeros((n-1, 3))
    c = np.zeros((n, 3))
    for i in range(n-2, -1, -1):
        c[i] = z[i] - u[i]*c[i+1]
    b = (locs[1:]-locs[:-1])/h[:,np.newaxis] - h[:,np.newaxis]*(c[1:]+2*c[:-1])/3
    d = (c[1:]-c[:-1]) / (3*h[:,np.newaxis])

    splines = np.zeros((n -1, 5, 3))
    splines[:, 0] = locs[:-1]
    splines[:,1] = b
    splines[:,2] = c[:-1]
    splines[:,3] = d
    splines[:,4] = tknots[:-1,np.newaxis]
    return splines


def eval_spline(splines, tknots, t_in):

    index = tknots.searchsorted(t_in, side='left') - 1
    index = index.clip(0, len(splines) - 1)
    to_calc = splines[index]
    ax, bx, cx, dx, tx = np.swapaxes(to_calc, 0, 1)
    t_r = t_in[:,np.newaxis] - tx
    out = ax + t_r * (bx + t_r * (cx + t_r * dx))
    return out

def calc_tanget(splines, tknots, t_in, h):
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
    return tanget

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
                pts = np.array(v)
                # t is the knots
                tmp = np.linalg.norm(pts[:-1]-pts[1:], axis=1)
                t = np.insert(tmp, 0, 0).cumsum()
                t = t/t[-1]

                # the t values to evaluate
                t_corr = np.array(t_in).clip(0, 1)

                if self.mode == 'LIN':
                    pts = pts.T
                    out = np.zeros((3, len(t_corr)))
                    for i in range(3):
                        out[i] = np.interp(t_corr, t, pts[i])
                    verts_out.append(pts.T.tolist())
                else:  # SPL

                    spl = cubic_spline(pts, t)
                    out = eval_spline(spl, t, t_corr)
                    verts_out.append(out.tolist())
                    if calc_tanget:
                        tanget = calc_tanget(spl, t, t_corr, h)
                        if norm_tanget:
                            norm = np.linalg.norm(tanget, axis=1)
                            norm_tanget_out.append((tanget/norm[:,np.newaxis]).tolist())
                        tanget_out.append(tanget.tolist())

            outputs = self.outputs
            if outputs['Vertices'].is_linked:
                outputs['Vertices'].sv_set(verts_out)
            if outputs['Tanget'].is_linked:
                outputs['Tanget'].sv_set(tanget_out)
            if outputs['Norm Tanget'].is_linked:
                outputs['Norm Tanget'].sv_set(norm_tanget_out)




def register():
    bpy.utils.register_class(SvInterpolationNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvInterpolationNodeMK3)
