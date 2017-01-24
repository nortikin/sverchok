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

import numpy as np

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, dataCorrect, repeat_last

# spline function modifed from
# from looptools 4.5.2 done by Bart Crouch


# calculates natural cubic splines through all given knots
def cubic_spline(locs, tknots):
    """    locs is and np.array with shape (n,3) and tknots has shape (n-1,)
    creates a cubic spline thorugh the locations given in locs

    """
    n = len(locs)
    if n < 2:
        return False

    # a = locs
    h = tknots[1:] - tknots[:-1]
    h[h == 0] = 1e-8
    q = np.zeros((n - 1, 3))
    q[1:] = 3 / h[1:, np.newaxis] * (locs[2:] - locs[1:-1]) - 3 / \
        h[:-1, np.newaxis] * (locs[1:-1] - locs[:-2])

    l = np.zeros((n, 3))
    l[0, :] = 1.0
    u = np.zeros((n - 1, 3))
    z = np.zeros((n, 3))

    for i in range(1, n - 1):
        l[i] = 2 * (tknots[i + 1] - tknots[i - 1]) - h[i - 1] * u[i - 1]
        l[i, l[i] == 0] = 1e-8
        u[i] = h[i] / l[i]
        z[i] = (q[i] - h[i - 1] * z[i - 1]) / l[i]
    l[-1, :] = 1.0
    z[-1] = 0.0

    b = np.zeros((n - 1, 3))
    c = np.zeros((n, 3))

    for i in range(n - 2, -1, -1):
        c[i] = z[i] - u[i] * c[i + 1]
    b = (locs[1:] - locs[:-1]) / h[:, np.newaxis] - h[:, np.newaxis] * (c[1:] + 2 * c[:-1]) / 3
    d = (c[1:] - c[:-1]) / (3 * h[:, np.newaxis])

    splines = np.zeros((n - 1, 5, 3))
    splines[:, 0] = locs[:-1]
    splines[:, 1] = b
    splines[:, 2] = c[:-1]
    splines[:, 3] = d
    splines[:, 4] = tknots[:-1, np.newaxis]
    return splines


def eval_spline(splines, tknots, t_in):
    """
    Evaluate the spline at the points in t_in, which must be an array
    with values in [0,1]
    returns and np array with the corresponding points
    """
    index = tknots.searchsorted(t_in, side='left') - 1
    index = index.clip(0, len(splines) - 1)
    to_calc = splines[index]
    ax, bx, cx, dx, tx = np.swapaxes(to_calc, 0, 1)
    t_r = t_in[:, np.newaxis] - tx
    out = ax + t_r * (bx + t_r * (cx + t_r * dx))
    return out


def calc_spline_tanget(spline, tknots, t_in, h):
    """
    Calc numerical tangents for spline at t_in
    """
    t_ph = t_in + h
    t_mh = t_in - h
    t_less_than_0 = t_mh < 0.0
    t_great_than_1 = t_ph > 1.0
    t_mh[t_less_than_0] += h
    t_ph[t_great_than_1] -= h
    tanget_ph = eval_spline(spline, tknots, t_ph)
    tanget_mh = eval_spline(spline, tknots, t_mh)
    tanget = tanget_ph - tanget_mh
    tanget[t_less_than_0 | t_great_than_1] *= 2
    return tanget


def create_knots(pts, metric="DISTANCE"):
    if metric == "DISTANCE":
        tmp = np.linalg.norm(pts[:-1] - pts[1:], axis=1)
        tknots = np.insert(tmp, 0, 0).cumsum()
        tknots = tknots / tknots[-1]
    elif metric == "MANHATTAN":
        tmp = np.sum(np.absolute(pts[:-1] - pts[1:]), 1)
        tknots = np.insert(tmp, 0, 0).cumsum()
        tknots = tknots / tknots[-1]
    elif metric == "POINTS":
        tknots = np.linspace(0, 1, len(pts))
    elif metric == "CHEBYSHEV":
        tknots = np.max(np.absolute(pts[1:] - pts[:-1]), 1)
        tmp = np.insert(tmp, 0, 0).cumsum()
        tknots = tknots / tknots[-1]

    return tknots


def eval_linear_spline(pts, tknots, t_in):
    """
    Eval the liner spline f(t) = x,y,z through the points
    in pts given the knots in tknots at the point in t_in
    """
    ptsT = pts.T
    out = np.zeros((3, len(t_in)))
    for i in range(3):
        out[i] = np.interp(t_in, tknots, ptsT[i])
    return out.T


class SvInterpolationNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    '''Vector Interpolate'''
    bl_idname = 'SvInterpolationNodeMK3'
    bl_label = 'Vector Interpolation mk3'
    bl_icon = 'OUTLINER_OB_EMPTY'

    t_in = FloatProperty(name="t",
                         default=.5, min=0, max=1, precision=5,
                         update=updateNode)

    h = FloatProperty(default=.001, precision=5, update=updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]
    mode = EnumProperty(name='Mode',
                        default="LIN", items=modes,
                        update=updateNode)

    knot_modes = [('MANHATTAN', 'Manhattan', "Manhattan distance metric", 0),
                  ('DISTANCE', 'Euclidan', "Eudlcian distance metric", 1),
                  ('POINTS', 'Points', "Points based", 2),
                  ('CHEBYSHEV', 'Chebyshev', "Chebyshev distance", 3)]

    knot_mode = EnumProperty(name='Knot Mode',
                             default="DISTANCE", items=knot_modes,
                             update=updateNode)

    is_cyclic = BoolProperty(name="Is Cyclic", default=False, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices')
        self.inputs.new('StringsSocket', 'Interval').prop_name = 't_in'
        self.outputs.new('VerticesSocket', 'Vertices')
        self.outputs.new('VerticesSocket', 'Tanget')
        self.outputs.new('VerticesSocket', 'Unit Tanget')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode', expand=True)
        layout.prop(self, 'is_cyclic')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'h')
        layout.prop(self, 'knot_mode')

    def process(self):
        if 'Unit Tanget' not in self.outputs:
            return
        if not any((s.is_linked for s in self.outputs)):
            return

        calc_tanget = self.outputs['Tanget'].is_linked or self.outputs['Unit Tanget'].is_linked

        norm_tanget = self.outputs['Unit Tanget'].is_linked

        h = self.h

        if self.inputs['Vertices'].is_linked:
            verts = self.inputs['Vertices'].sv_get()
            verts = dataCorrect(verts)
            t_ins = self.inputs['Interval'].sv_get()
            verts_out = []
            tanget_out = []
            norm_tanget_out = []
            for v, t_in in zip(verts, repeat_last(t_ins)):

                t_corr = np.array(t_in).clip(0, 1)

                if self.mode == 'LIN':
                    if self.is_cyclic:
                        pts = np.array(v + [v[0]])
                    else:
                        pts = np.array(v)
                    tknots = create_knots(pts, metric=self.knot_mode)
                    out = eval_linear_spline(pts, tknots, t_corr)
                    verts_out.append(out.tolist())
                else:  # SPL
                    if self.is_cyclic:

                        pts = np.array(v[-4:] + v + v[:4])
                        tknots = create_knots(pts, metric=self.knot_mode)
                        scale = 1 / (tknots[-4] - tknots[4])
                        base = tknots[4]
                        tknots -= base
                        tknots *= scale
                    else:
                        pts = np.array(v)
                        tknots = create_knots(pts, metric=self.knot_mode)

                    spl = cubic_spline(pts, tknots)
                    out = eval_spline(spl, tknots, t_corr)
                    verts_out.append(out.tolist())
                    if calc_tanget:
                        tanget = calc_spline_tanget(spl, tknots, t_corr, h)
                        if norm_tanget:
                            norm = np.linalg.norm(tanget, axis=1)
                            norm_tanget_out.append((tanget / norm[:, np.newaxis]).tolist())
                        tanget_out.append(tanget.tolist())

            outputs = self.outputs
            if outputs['Vertices'].is_linked:
                outputs['Vertices'].sv_set(verts_out)
            if outputs['Tanget'].is_linked:
                outputs['Tanget'].sv_set(tanget_out)
            if outputs['Unit Tanget'].is_linked:
                outputs['Unit Tanget'].sv_set(norm_tanget_out)


def register():
    bpy.utils.register_class(SvInterpolationNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvInterpolationNodeMK3)
