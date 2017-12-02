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
import math

import bpy
from bpy.props import EnumProperty, FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, dataCorrect, repeat_last

# spline function modifed from
# from looptools 4.5.2 done by Bart Crouch

class Spline(object):
    @classmethod
    def create_knots(cls, pts, metric="DISTANCE"):
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


class CubicSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):
        """    locs is and np.array with shape (n,3) and tknots has shape (n-1,)
        creates a cubic spline thorugh the locations given in locs

        """

        if is_cyclic:

            locs = np.array(vertices[-4:] + vertices + vertices[:4])
            if tknots is None:
                if metric is None:
                    raise Exception("CubicSpline: either tknots or metric must be specified")
                tknots = Spline.create_knots(locs, metric)
                scale = 1 / (tknots[-4] - tknots[4])
                base = tknots[4]
                tknots -= base
                tknots *= scale
        else:
            locs = np.array(vertices)
            if tknots is None:
                if metric is None:
                    raise Exception("CubicSpline: either tknots or metric must be specified")
                tknots = Spline.create_knots(locs, metric)

        self.tknots = tknots
        self.is_cyclic = is_cyclic

        n = len(locs)
        if n < 2:
            return

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
        
        self.splines = splines

    def eval(self, t_in, tknots = None):
        """
        Evaluate the spline at the points in t_in, which must be an array
        with values in [0,1]
        returns and np array with the corresponding points
        """

        if tknots is None:
            tknots = self.tknots

        index = tknots.searchsorted(t_in, side='left') - 1
        index = index.clip(0, len(self.splines) - 1)
        to_calc = self.splines[index]
        ax, bx, cx, dx, tx = np.swapaxes(to_calc, 0, 1)
        t_r = t_in[:, np.newaxis] - tx
        out = ax + t_r * (bx + t_r * (cx + t_r * dx))
        return out

    def calc_tangent(self, t_in, h, tknots=None):
        """
        Calc numerical tangents for spline at t_in
        """

        if tknots is None:
            tknots = self.tknots

        t_ph = t_in + h
        t_mh = t_in - h
        t_less_than_0 = t_mh < 0.0
        t_great_than_1 = t_ph > 1.0
        t_mh[t_less_than_0] += h
        t_ph[t_great_than_1] -= h
        tanget_ph = self.eval(t_ph)
        tanget_mh = self.eval(t_mh)
        tanget = tanget_ph - tanget_mh
        tanget[t_less_than_0 | t_great_than_1] *= 2
        return tanget

class LinearSpline(Spline):
    def __init__(self, vertices, tknots = None, metric = None, is_cyclic = False):

        if is_cyclic:
            pts = np.array(vertices + [vertices[0]])
        else:
            pts = np.array(vertices)

        if tknots is None:
            if metric is None:
                raise Exception("LinearSpline: either tknots or metric must be specified")
            tknots = Spline.create_knots(pts, metric)

        self.pts = pts
        self.tknots = tknots
        self.is_cyclic = is_cyclic

    def eval(self, t_in, tknots = None):
        """
        Eval the liner spline f(t) = x,y,z through the points
        in pts given the knots in tknots at the point in t_in
        """

        if tknots is None:
            tknots = self.tknots
            
        ptsT = self.pts.T
        out = np.zeros((3, len(t_in)))
        for i in range(3):
            out[i] = np.interp(t_in, tknots, ptsT[i])
        return out.T

    def calc_tangent(self, t_in, tknots = None):
        if tknots is None:
            tknots = self.tknots

        lookup_segments = GenerateLookup(self.is_cyclic, self.pts.tolist())
        return [lookup_segments.find_bucket(f) for f in t_in]

class GenerateLookup():

    def __init__(self, cyclic, vlist):
        self.lookup = {}
        self.summed_lengths = []
        self.indiv_lengths = []
        self.normals = []
        self.buckets = []
        if cyclic:
            vlist = vlist + [vlist[0]]

        self.get_seq_len(vlist)
        self.acquire_lookup_table()
        self.get_buckets()
        # for idx, (k, v) in enumerate(sorted(self.lookup.items())):
        #     print(k, v)

    def find_bucket(self, factor):
        for bucket_min, bucket_max in zip(self.buckets[:-1], self.buckets[1:]):
            if bucket_min <= factor < bucket_max:
                tval = self.lookup.get(bucket_min)  # , self.lookup.get(self.buckets[-1]))

                return tval

        # return last bucket just in case
        return self.lookup.get(self.buckets[-1])

    def get_buckets(self):
        self.buckets = [(clen / self.total_length) for clen in self.summed_lengths]
    
    def acquire_lookup_table(self):
        for current_length, segment_normal in zip(self.summed_lengths, self.normals):
            self.lookup[current_length / self.total_length] = segment_normal
        
    def get_seq_len(self, vlist):
        add_len = self.indiv_lengths.append
        add_normal = self.normals.append
        add_to_sumlist = self.summed_lengths.append
        current_length = 0.0
        for idx in range(len(vlist)-1):
            v = vlist[idx][0]-vlist[idx+1][0], vlist[idx][1]-vlist[idx+1][1], vlist[idx][2]-vlist[idx+1][2]
            length = math.sqrt((v[0]*v[0]) + (v[1]*v[1]) + (v[2]*v[2]))
            add_normal(v)
            add_len(length)
            add_to_sumlist(current_length)
            current_length += length

        self.total_length = sum(self.indiv_lengths)
            



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
                    spline = LinearSpline(v, metric = self.knot_mode, is_cyclic = self.is_cyclic)
                    out = spline.eval(t_corr)
                    verts_out.append(out.tolist())

                    if calc_tanget:
                        tanget_out.append(spline.calc_tangent(t_corr))

                else:  # SPL
                    spline = CubicSpline(v, metric = self.knot_mode, is_cyclic = self.is_cyclic)
                    out = spline.eval(t_corr)
                    verts_out.append(out.tolist())
                    if calc_tanget:
                        tangent = spline.calc_tangent(t_corr, h)
                        if norm_tanget:
                            norm = np.linalg.norm(tangent, axis=1)
                            norm_tanget_out.append((tangent / norm[:, np.newaxis]).tolist())
                        tanget_out.append(tangent.tolist())

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
