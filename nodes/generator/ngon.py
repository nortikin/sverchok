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

from math import sin, cos, pi, degrees, radians
import random

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty, EnumProperty
import numpy as np

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, rotate_list, list_match_modes, list_match_func)

def make_verts(nsides, radius, rand_r, rand_phi, rand_seed, divs):
    if rand_r or rand_phi:
        random.seed(rand_seed)
    dphi = (2*pi)/nsides

    _phi = np.arange(nsides)*dphi
    if rand_phi:
        np.random.seed( int(rand_seed*1000) )
        _phi = _phi + np.array( np.random.uniform(-rand_phi, +rand_phi, nsides) )

    _rr = np.ones( nsides )*radius
    if rand_r:
        np.random.seed( int(rand_seed*1000) )
        _rr = _rr + np.array( np.random.uniform(-rand_r, +rand_r, nsides) )

    _x     = _rr*np.cos(_phi)
    _y     = _rr*np.sin(_phi)

    if divs>1:
        # divs stright lines, not arcs
        _x0 = _x
        _y0 = _y
        _x1 = np.roll(_x0, -1)
        _y1 = np.roll(_y0, -1)
        _dx = (_x1-_x0)/divs
        _dy = (_y1-_y0)/divs
        _x_divs = np.repeat( _x0, divs)
        _y_divs = np.repeat( _y0, divs)
        _dx     = np.repeat( _dx, divs)
        _dy     = np.repeat( _dy, divs)
        _id = np.meshgrid( np.arange(divs), np.arange(nsides), indexing = 'xy')[0].flatten()
        _xd = _x_divs+_id*_dx
        _yd = _y_divs+_id*_dy
        _verts = np.column_stack( (_xd, _yd, np.zeros_like(_xd) ) )
        pass
    else:
        _verts = np.column_stack( (_x, _y, np.zeros_like(_x) ))
    
    _list_verts = _verts.tolist()
    return _list_verts

def make_edges(nsides, shift, divs):

    _n = np.arange(nsides*divs)
    _edges = np.column_stack( (_n, np.roll(_n, -1-shift )) )
    _list_edges  = _edges.tolist()
    return _list_edges

def make_faces(nsides, shift, divs, r, dr, dphi):
    # for now, do not return faces if star factor
    # is not zero - the face obviously would be degraded.
    # This actual for random phi too and some cases of random r
    # to the future version of node
    #   if not shift or dphi or dr and (r-dr)<0:
    if shift:
        return []
    _faces = np.arange(nsides*divs)
    _list_faces = _faces.tolist()
    return [_list_faces]

class SvNGonNode(SverchCustomTreeNode, bpy.types.Node):
    ''' NGon. [default]
    Radius: [1.]
    N Sides, min=3: [5]
    Divisions, min=1: [1]
    Random Radius, min=0.0: [0.]
    Random Phi, range: 0-pi: [0.]
    Seed: [0.0]
    Shift (Star Factor), min=0: [0]
'''
    bl_idname = 'SvNGonNode'
    bl_label = 'NGon'
    bl_icon = 'RNDCURVE'
    sv_icon = 'SV_NGON'

    rad_: FloatProperty(name='Radius', description='Radius',
                         default=1.0,
                         update=updateNode)
    sides_: IntProperty(name='N Sides', description='Number of polygon sides',
                        default=5, min=3,
                        update=updateNode)
    divisions : IntProperty(name='Divisions', description = "Number of divisions to divide each side to (lines not arcs)",
                        default=1, min=1,
                        update=updateNode)
    rand_seed_: FloatProperty(name='Seed', description='Random seed',
                        default=0.0,
                        update=updateNode)
    rand_r_: FloatProperty(name='RandomR', description='Radius randomization amplitude',
                        default=0.0, min=0.0,
                        update=updateNode)
    rand_phi_: FloatProperty(name='RandomPhi', description='Angle randomization amplitude (radians)',
                        default=0.0, min=0.0, max=pi,
                        update=updateNode)
    shift_: IntProperty(name='Shift', description='Edges bind shift (star factor)',
                        default=0, min=0,
                        update=updateNode)
    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths, object level",
        items=list_match_modes, default="REPEAT",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('SvStringsSocket', "N Sides").prop_name = 'sides_'
        self.inputs.new('SvStringsSocket', "Divisions").prop_name = 'divisions'
        self.inputs.new('SvStringsSocket', "RandomR").prop_name = 'rand_r_'
        self.inputs.new('SvStringsSocket', "RandomPhi").prop_name = 'rand_phi_'
        self.inputs.new('SvStringsSocket', "RandomSeed").prop_name = 'rand_seed_'
        self.inputs.new('SvStringsSocket', "Shift").prop_name = 'shift_'

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Polygons")

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "list_match")

    def process(self):
        # inputs
        radius = self.inputs['Radius'].sv_get()[0]

        nsides = self.inputs['N Sides'].sv_get()[0]
        nsides = list(map(lambda x: max(3, int(x)), nsides))

        seed = self.inputs['RandomSeed'].sv_get()[0]

        rand_r   = self.inputs['RandomR'].sv_get()[0]
        rand_phi = self.inputs['RandomPhi'].sv_get()[0]

        shift = self.inputs['Shift'].sv_get()[0]

        if 'Divisions' in self.inputs:
            divisions = self.inputs['Divisions'].sv_get()[0]
        else:
            divisions = [1]

        parameters = list_match_func[self.list_match]([radius, nsides, seed, rand_r, rand_phi, shift, divisions])

        # outputs
        if self.outputs['Vertices'].is_linked:
            vertices = [make_verts(n, r, dr, dphi, s, divs) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Vertices'].sv_set(vertices)

        if self.outputs['Edges'].is_linked:
            edges = [make_edges(n, shift, divs) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Edges'].sv_set(edges)

        if self.outputs['Polygons'].is_linked:
            faces = [make_faces(n, shift, divs, r, dr, dphi) for r, n, s, dr, dphi, shift, divs in zip(*parameters)]
            self.outputs['Polygons'].sv_set(faces)


def register():
    bpy.utils.register_class(SvNGonNode)


def unregister():
    bpy.utils.unregister_class(SvNGonNode)
