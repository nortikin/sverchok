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

'''
None of this file is in a working condition. skip this file.

purpose of this file is to store the convenience functions which can be used for regular nodes
or as part of recipes for script nodes. These functions will be optimized only for speed, never
for aesthetics or line count or cleverness.

or maybe it makes sense to turn this into a giant class

'''
import math

import bpy
import bmesh
import mathutils
from mathutils import Matrix

from sverchok.utils import sv_mesh_utils  # mesh_join
from sverchok.utils import sv_bmesh_utils

from sv_bmesh_utils import bmesh_from_pydata
from sv_bmesh_utils import pydata_from_bmesh
from sv_bmesh_utils import with_bmesh  # a decorator

identity_matrix = Matrix()

# constants
PI = math.pi
HALF_PI = PI / 2
QUARTER_PI = PI / 4
TAU = PI * 2
TWO_PI = TAU
N = identity_matrix


def generic_output_handler(_bm, output, kind, merge):
    ''' 
    This function is not working yet, don't try it.

    I elect to compartmentalize this function, a bit of repeat code but easier to reason about for now.

    switches:
        : output, kind, merge
            - will effect the entirity of the output of this function.
            - :output can be 'v', 've', 'vep', 'vp'
            - :merge will produce a topological mesh join of all geometry lists
            - :kind gives opportunity to output bmesh, np, or pydata (default)
               -- np: means it would output a numpy array instead of lists, will return vectors as n*4
               -- bm would output a bm object
               -- pydata would output [n*[[verts],[edges],[faces]], ... ]

    '''

    # ignore v, ve, vp, vep
    if kind == 'bm':
        return _bm if not merge else bm_merger(_bm)


    if kind in {'pydata', 'np'}:
        _verts = []
        _edges = []
        _polygons = []
        for bm in _bm:
            verts, edges, polygons = pydata_from_bmesh(bm)
            _verts.append(verts)
            if 'e' in output:
                _edges.append(edges)
            if 'p' in output:
                _polygons.append(polygons)
        for bm in reversed(_bm):
            bm.free()
        
        generated_geom = _verts, _edges, _polygons
        
        NP = (kind == 'np')

        if merge:
            return sv_mesh_utils.mesh_join_extended(output, generated_geom, np=NP)
        else:
            if NP:
                return sv_mesh_utils.as_np(output, generated_geom)
            else:
                return [g for g in generated_geom if g]



def circle(radius=(1,), phase=(0,), angle=(TAU,), verts=(20,), matrix=(N,), output='vep', kind='pydata', merge=False):
    '''
    variables: 
        : radius, phase, angle, verts, matrix
            will be wrapped to a tuple if the input was an int, 
            shorter tuples will repeat to match length of longest input

    '''
    ...

def rect(w=(1,), h=(1.654,), dim=None, matrix=(N,), radius=0.0, radius_segs=6, edge_segs=1, output='vep', kind='pydata', merge=False):
    '''
    if dim, then uniform, 
    if w, h then 
    '''
    ...

# shapes 3d

def uv_sphere(u=(5,), v=(4,), radius=(0.5,), output='vep', kind='pydata', merge=False):
    '''
    using the bmesh.ops we can quikly create some primtives
    - todo deal with minimum maximum vals before passing. 
    '''

    matching = (len(u) == len(v) == len(radius))
    if not matching:
        return

    _bm = []
    for _u, _v, _radius in zip((u, v, radius)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=_u, v_segments=_v, diameter=_radius*2)
        _bm.append(bm)

    return generic_output_handler(_bm, outputs, kind, merge)

