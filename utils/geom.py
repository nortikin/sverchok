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

Eventual purpose of this file is to store the convenience functions which
can be used for regular nodes or as part of recipes for script nodes. These
functions will initially be sub optimal quick implementations, then optimized
only for speed, never for aesthetics or line count or cleverness.

'''

import math

import bpy
import bmesh
import mathutils
from mathutils import Matrix

from sverchok.utils import sv_mesh_utils
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


def as_np(output, generated_geom):
    ...

def mesh_join_extended(output, generated_geom, np):
    '''Given list of meshes represented by lists of vertices, edges and faces,
    produce one joined mesh. -- partial lift from portnov's mesh_utils'''

    vertices_s, edges_s, faces_s = generated_geom

    offset = 0
    
    result_vertices = []
    result_edges = []
    result_faces = []

    if len(edges_s) == 0:
        edges_s = [[]] * len(faces_s)
    
    for vertices, edges, faces in zip(vertices_s, edges_s, faces_s):
        result_vertices.extend(vertices)
        if 'e' in output:
            new_edges = [tuple(i + offset for i in edge) for edge in edges]
        if 'p' in output:
            new_faces = [[i + offset for i in face] for face in faces]
        result_edges.extend(new_edges)
        result_faces.extend(new_faces)
        offset += len(vertices)
    
    generated_geom = result_vertices, result_edges, result_faces
    generated_geom = [g for g in generated_geom if g]

    if np:
        generated_geom = as_np(generated_geom)
    
    return generated_geom


def bm_merger(_bm):
    ...


def switches(kwargs):
    output = kwargs.get('output', 'vep')
    kind = kwargs.get('kind', 'pydata')
    merge = kwargs.get('merge', False)
    return output, kind, merge


def generic_output_handler(_bm, kwargs):
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
    output, kind, merge = switches(kwargs)

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
            return mesh_join_extended(output, generated_geom, np=NP)
        else:
            if NP:
                return as_np(output, generated_geom)
            else:
                return [g for g in generated_geom if g]



def circle(radius=(1,), phase=(0,), angle=(TAU,), verts=(20,), matrix=(N,), **kwargs):
    '''
    variables: 
        : radius, phase, angle, verts, matrix
            will be wrapped to a tuple if the input was an int, 
            shorter tuples will repeat to match length of longest input

    '''
    
    ...

def rect(w=(1,), h=(1.654,), dim=None, matrix=(N,), radius=0.0, radius_segs=6, edge_segs=1, **kwargs):
    '''
    if dim, then uniform, 
    if w, h then 
    '''
    
    ...
    

# shapes 3d

def uv_sphere(u=(5,), v=(4,), radius=(0.5,), matrix=(N,), **kwargs):
    '''
    using the bmesh.ops we can quikly create some primtives
    - todo deal with minimum maximum vals before passing. 
    '''
    matching = (len(u) == len(v) == len(radius))
    if not matching:
        # currently a dumb function.
        return

    _bm = []
    for _u, _v, _radius in zip((u, v, radius)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=_u, v_segments=_v, diameter=_radius*2)
        _bm.append(bm)

    return generic_output_handler(_bm, kwargs)

