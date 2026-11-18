# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file.
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""IcoSphere generator with BMesh, NumPy and optional Numba backends.

NumPy/Numba refine an indexed triangle/edge mesh without BMesh, sorting,
np.unique, or hash tables. Subdivisions 0 and 1 both produce an icosahedron,
matching the geometric subdivision levels of Blender's IcoSphere operation.

With caching enabled, the complete unit-radius mesh is generated once per
(subdivisions, backend), independent of which output sockets are connected.
This trades a small one-time final-level topology cost for immediate reuse when
connecting additional outputs. Uncached evaluations still omit unused outputs.
Cached arrays are read-only; node outputs always receive independent data.
"""

from functools import lru_cache
from math import pi, sqrt

import bpy
import bmesh
import numpy as np
from bpy.props import BoolProperty, BoolVectorProperty, EnumProperty, FloatProperty, IntProperty

from sverchok.data_structure import updateNode
from sverchok.dependencies import numba
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.utils.math import from_cylindrical
from sverchok.utils.nodes_mixins.recursive_nodes import SvRecursiveNode
from sverchok.utils.sv_bmesh_utils import numpy_data_from_bmesh


# Older Blender releases used "diameter" rather than "radius".
_OLD_ICOSPHERE = "diameter=" in bmesh.ops.create_icosphere.__doc__
_SIZE_PARAM = "diameter" if _OLD_ICOSPHERE else "radius"


def icosahedron_cylindrical(radius):
    """Original level-zero topology and ordering, for compatibility."""
    d = 2.0 / sqrt(5.0)
    vertices = [(0, 0, radius)]
    vertices += [(d * radius, pi / 5 + i * 2 * pi / 5, 0.5 * d * radius)
                 for i in range(5)]
    vertices += [(d * radius, i * 2 * pi / 5, -0.5 * d * radius)
                 for i in range(5)]
    vertices.append((0, 0, -radius))

    edges = [(0, i) for i in range(1, 6)]
    edges += [(i, i + 1) for i in range(1, 5)] + [(1, 5)]
    edges += [(i, i + 5) for i in range(1, 6)]
    edges += [(i, i + 6) for i in range(1, 5)] + [(5, 6)]
    edges += [(i, i + 1) for i in range(6, 10)] + [(6, 10)]
    edges += [(i, 11) for i in range(6, 11)]

    faces = [[0, i, i + 1] for i in range(1, 5)] + [[0, 5, 1]]
    faces += [[i, i + 6, i + 1] for i in range(1, 5)] + [[1, 5, 6]]
    faces += [[i, i + 5, i + 6] for i in range(1, 5)] + [[5, 10, 6]]
    faces += [[i + 1, i, 11] for i in range(6, 10)] + [[6, 10, 11]]
    return vertices, edges, faces


def icosahedron(radius):
    """Public helper preserved for scripts using the original node."""
    cylindrical, edges, faces = icosahedron_cylindrical(radius)
    verts = [from_cylindrical(rho, phi, z, 'radians')
             for rho, phi, z in cylindrical]
    return verts, edges, faces


@lru_cache(maxsize=1)
def _base_icosahedron():
    """Unit mesh and face->edge indices. Created once; never mutated."""
    cylindrical, edges, faces = icosahedron_cylindrical(1.0)
    coords = np.asarray(cylindrical, dtype=np.float64)
    angles = coords[:, 1]
    verts = np.column_stack((coords[:, 0] * np.cos(angles),
                             coords[:, 0] * np.sin(angles), coords[:, 2]))
    edges = np.asarray(edges, dtype=np.int32)
    faces = np.asarray(faces, dtype=np.int32)

    # Only 30 edges and 20 faces: do this lookup once, not per subdivision.
    lookup = {tuple(sorted((int(a), int(b)))): i
              for i, (a, b) in enumerate(edges)}
    face_edges = np.empty_like(faces)
    for i, (a, b, c) in enumerate(faces):
        face_edges[i, 0] = lookup[min(a, b), max(a, b)]
        face_edges[i, 1] = lookup[min(b, c), max(b, c)]
        face_edges[i, 2] = lookup[min(c, a), max(c, a)]
    # Shared base arrays must never be changed by an output or a refinement.
    for array in (verts, edges, faces, face_edges):
        array.flags.writeable = False
    return verts, edges, faces, face_edges


def _refine_np(verts, edges, faces, face_edges,
               build_edges=True, build_faces=True, build_face_edges=True):
    """Refine an indexed triangle mesh in O(V + E + F), without deduplication.

    Each parent edge e creates one new vertex (V + e) and two child edges
    (2*e, 2*e+1), one per endpoint. Each parent face creates three internal
    edges and four child faces. Face->edge incidence is propagated exactly.
    The last level can omit unused outputs and all face->edge bookkeeping.
    """
    nv, ne, nf = len(verts), len(edges), len(faces)
    out_verts = np.empty((nv + ne, 3), dtype=np.float64)
    out_verts[:nv] = verts
    mid = out_verts[nv:]
    np.add(verts[edges[:, 0]], verts[edges[:, 1]], out=mid)
    mid /= np.linalg.norm(mid, axis=1)[:, None]

    out_edges = None
    out_faces = None
    out_face_edges = None
    if not (build_edges or build_faces or build_face_edges):
        return out_verts, out_edges, out_faces, out_face_edges

    if build_edges:
        out_edges = np.empty((2 * ne + 3 * nf, 2), dtype=np.int32)
        out_edges[:2 * ne:2, 0] = edges[:, 0]
        out_edges[1:2 * ne:2, 0] = edges[:, 1]
        new_ids = nv + np.arange(ne, dtype=np.int32)
        out_edges[:2 * ne:2, 1] = new_ids
        out_edges[1:2 * ne:2, 1] = new_ids

    # Midpoint indices of each face's three edges.
    ab, bc, ca = (face_edges + nv).T
    if build_faces:
        a, b, c = faces.T
        out_faces = np.empty((4 * nf, 3), dtype=np.int32)
        out_faces[::4, 0], out_faces[::4, 1], out_faces[::4, 2] = a, ab, ca
        out_faces[1::4, 0], out_faces[1::4, 1], out_faces[1::4, 2] = b, bc, ab
        out_faces[2::4, 0], out_faces[2::4, 1], out_faces[2::4, 2] = c, ca, bc
        out_faces[3::4, 0], out_faces[3::4, 1], out_faces[3::4, 2] = ab, bc, ca

    if build_edges:
        out_edges[2 * ne::3, 0], out_edges[2 * ne::3, 1] = ab, bc
        out_edges[2 * ne + 1::3, 0], out_edges[2 * ne + 1::3, 1] = bc, ca
        out_edges[2 * ne + 2::3, 0], out_edges[2 * ne + 2::3, 1] = ca, ab

    if build_face_edges:
        a, b, c = faces.T
        ea, eb, ec = face_edges.T
        ia, ib, ic = 2 * ea, 2 * eb, 2 * ec
        inner = 2 * ne + 3 * np.arange(nf, dtype=np.int32)
        out_face_edges = np.empty((4 * nf, 3), dtype=np.int32)
        out_face_edges[::4, 0] = ia + (edges[ea, 0] != a)
        out_face_edges[::4, 1] = inner + 2
        out_face_edges[::4, 2] = ic + (edges[ec, 0] != a)
        out_face_edges[1::4, 0] = ib + (edges[eb, 0] != b)
        out_face_edges[1::4, 1] = inner
        out_face_edges[1::4, 2] = ia + (edges[ea, 0] != b)
        out_face_edges[2::4, 0] = ic + (edges[ec, 0] != c)
        out_face_edges[2::4, 1] = inner + 1
        out_face_edges[2::4, 2] = ib + (edges[eb, 0] != c)
        out_face_edges[3::4, 0] = inner
        out_face_edges[3::4, 1] = inner + 1
        out_face_edges[3::4, 2] = inner + 2

    return out_verts, out_edges, out_faces, out_face_edges


if numba is not None:
    @numba.njit(cache=True)
    def _refine_nb(verts, edges, faces, face_edges,
                   build_edges=True, build_faces=True, build_face_edges=True):
        """Numba implementation of the same edge-indexed O(V + E + F) pass."""
        nv, ne, nf = verts.shape[0], edges.shape[0], faces.shape[0]
        out_verts = np.empty((nv + ne, 3), dtype=np.float64)
        out_verts[:nv] = verts
        if build_edges:
            out_edges = np.empty((2 * ne + 3 * nf, 2), dtype=np.int32)
        else:
            out_edges = np.empty((0, 2), dtype=np.int32)
        if build_faces:
            out_faces = np.empty((4 * nf, 3), dtype=np.int32)
        else:
            out_faces = np.empty((0, 3), dtype=np.int32)
        if build_face_edges:
            out_face_edges = np.empty((4 * nf, 3), dtype=np.int32)
        else:
            out_face_edges = np.empty((0, 3), dtype=np.int32)

        for i in range(ne):
            a, b = edges[i, 0], edges[i, 1]
            m = nv + i
            x = verts[a, 0] + verts[b, 0]
            y = verts[a, 1] + verts[b, 1]
            z = verts[a, 2] + verts[b, 2]
            inv = 1.0 / sqrt(x * x + y * y + z * z)
            out_verts[m, 0] = x * inv
            out_verts[m, 1] = y * inv
            out_verts[m, 2] = z * inv
            if build_edges:
                out_edges[2 * i, 0], out_edges[2 * i, 1] = a, m
                out_edges[2 * i + 1, 0], out_edges[2 * i + 1, 1] = b, m

        if build_edges or build_faces or build_face_edges:
            for i in range(nf):
                a, b, c = faces[i, 0], faces[i, 1], faces[i, 2]
                ea, eb, ec = face_edges[i, 0], face_edges[i, 1], face_edges[i, 2]
                ab, bc, ca = nv + ea, nv + eb, nv + ec
                q = 4 * i
                r = 2 * ne + 3 * i
                if build_faces:
                    out_faces[q, 0], out_faces[q, 1], out_faces[q, 2] = a, ab, ca
                    out_faces[q+1, 0], out_faces[q+1, 1], out_faces[q+1, 2] = b, bc, ab
                    out_faces[q+2, 0], out_faces[q+2, 1], out_faces[q+2, 2] = c, ca, bc
                    out_faces[q+3, 0], out_faces[q+3, 1], out_faces[q+3, 2] = ab, bc, ca
                if build_edges:
                    out_edges[r, 0], out_edges[r, 1] = ab, bc
                    out_edges[r+1, 0], out_edges[r+1, 1] = bc, ca
                    out_edges[r+2, 0], out_edges[r+2, 1] = ca, ab
                if build_face_edges:
                    out_face_edges[q, 0] = 2 * ea + (edges[ea, 0] != a)
                    out_face_edges[q, 1] = r + 2
                    out_face_edges[q, 2] = 2 * ec + (edges[ec, 0] != a)
                    out_face_edges[q+1, 0] = 2 * eb + (edges[eb, 0] != b)
                    out_face_edges[q+1, 1] = r
                    out_face_edges[q+1, 2] = 2 * ea + (edges[ea, 0] != b)
                    out_face_edges[q+2, 0] = 2 * ec + (edges[ec, 0] != c)
                    out_face_edges[q+2, 1] = r + 1
                    out_face_edges[q+2, 2] = 2 * eb + (edges[eb, 0] != c)
                    out_face_edges[q+3, 0] = r
                    out_face_edges[q+3, 1] = r + 1
                    out_face_edges[q+3, 2] = r + 2

        return out_verts, out_edges, out_faces, out_face_edges


def _generate_unit_icosphere(subdivisions, use_numba=False,
                              need_edges=True, need_faces=True):
    """Generate unit arrays. The returned arrays must not be mutated."""
    verts, edges, faces, face_edges = _base_icosahedron()
    if subdivisions <= 1:
        return verts, edges if need_edges else None, faces if need_faces else None

    refine = _refine_nb if use_numba and numba is not None else _refine_np
    for level in range(1, subdivisions):
        is_last = level == subdivisions - 1
        # Final face->edge incidence is not output. When no edges or faces
        # sockets are linked, skip building those last-level arrays as well.
        verts, edges, faces, face_edges = refine(
            verts, edges, faces, face_edges,
            build_edges=(not is_last or need_edges),
            build_faces=(not is_last or need_faces),
            build_face_edges=not is_last)
    return verts, edges if need_edges else None, faces if need_faces else None


@lru_cache(maxsize=6)
def _cached_unit_icosphere(subdivisions, use_numba):
    """Share one complete unit mesh across any output-socket combinations.

    ``need_edges``/``need_faces`` deliberately are NOT part of the key:
    connecting an additional socket must not cause a second subdivision.
    """
    mesh = _generate_unit_icosphere(subdivisions, use_numba)
    for array in mesh:
        array.flags.writeable = False
    return mesh


def _unit_icosphere(subdivisions, use_numba, need_edges, need_faces, cache):
    # An LRU entry contains all outputs for the subdivision level. Computing
    # the last-level edges/faces just once is generally cheaper than retaining
    # a partial mesh and regenerating data when the user links another socket.
    # Do not cache very high subdivision levels: their arrays can be enormous.
    if cache and subdivisions <= 8:
        verts, edges, faces = _cached_unit_icosphere(subdivisions, use_numba)
        return verts, edges if need_edges else None, faces if need_faces else None

    # When caching is off (or too large), still avoid unused final arrays.
    return _generate_unit_icosphere(subdivisions, use_numba, need_edges, need_faces)


class SvIcosphereNodeMk2(SverchCustomTreeNode, bpy.types.Node, SvRecursiveNode):
    """IcoSphere MK2. [default]
    Subdivisions, min (0): [2]
    Radius, min (0): [1.0]
    """

    bl_idname = 'SvIcosphereNodeMk2'
    bl_label = 'IcoSphere'
    bl_icon = 'MESH_ICOSPHERE'
    replacement_nodes = [('SphereNode', None, dict(Faces='Polygons'))]

    def set_subdivisions(self, value):
        self['subdivisions'] = min(value, self.subdivisions_max)

    def get_subdivisions(self):
        return self['subdivisions']

    subdivisions: IntProperty(
        name="Subdivisions", description="Recursion level (0 and 1: base icosahedron)",
        default=2, min=0, set=set_subdivisions, get=get_subdivisions,
        update=updateNode)

    subdivisions_max: IntProperty(
        name="Max. Subdivisions", description="Maximum subdivision level available",
        default=5, min=2, update=updateNode)

    radius: FloatProperty(
        name="Radius", default=1.0, min=0.0,
        update=updateNode, description="Sphere radius")

    implementation: EnumProperty(
        name="Implementation",
        description="Mesh generation backend",
        items=[
            ('BMESH', 'BMesh', 'Original Blender BMesh generator'),
            ('NUMPY', 'NumPy', 'Vectorized NumPy midpoint subdivision'),
            ('NUMBA', 'NumPy + Numba', 'Numba-compiled direct topology generation'),
        ],
        default='NUMBA' if numba is not None else 'NUMPY', update=updateNode)

    cache_topology: BoolProperty(
        name="Cache Topology",
        description="Cache a complete unit mesh per level and backend; reuse when outputs or radius change",
        default=True, update=updateNode)

    out_np: BoolVectorProperty(
        name="Output Numpy",
        description="Output NumPy arrays instead of nested Python lists",
        default=(False, False, False), size=3, update=updateNode)

    def sv_init(self, context):
        self['subdivisions'] = 2
        self.inputs.new('SvStringsSocket', 'Subdivisions').prop_name = 'subdivisions'
        self.inputs.new('SvStringsSocket', 'Radius').prop_name = 'radius'
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Edges')
        self.outputs.new('SvStringsSocket', 'Faces')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'implementation')
        if self.implementation == 'NUMBA' and numba is None:
            layout.label(text='Numba unavailable: using NumPy', icon='INFO')
        layout.prop(self, 'subdivisions_max')
        layout.prop(self, 'list_match')
        if self.implementation != 'BMESH':
            layout.prop(self, 'cache_topology')
        layout.label(text='Output Numpy:')
        row = layout.row(align=True)
        for i in range(3):
            row.prop(self, 'out_np', index=i, text=self.outputs[i].name,
                     toggle=True)

    def pre_setup(self):
        for socket in self.inputs:
            socket.nesting_level = 1
            socket.pre_processing = 'ONE_ITEM'

    def process_data(self, params):
        out_verts, out_edges, out_faces = [], [], []
        use_bmesh = self.implementation == 'BMESH'
        use_numba = self.implementation == 'NUMBA' and numba is not None
        want_verts, want_edges, want_faces = (s.is_linked for s in self.outputs)

        for subdivisions, radius in zip(*params):
            subdivisions = max(0, min(int(subdivisions), self.subdivisions_max))
            radius = float(radius)

            if use_bmesh:
                if subdivisions == 0:
                    verts, edges, faces = icosahedron(radius)
                    if self.out_np[0]:
                        verts = np.asarray(verts, dtype=np.float64)
                    if self.out_np[1]:
                        edges = np.asarray(edges, dtype=np.int32)
                    if self.out_np[2]:
                        faces = np.asarray(faces, dtype=np.int32)
                else:
                    bm = bmesh.new()
                    try:
                        bmesh.ops.create_icosphere(
                            bm, **{_SIZE_PARAM: radius,
                                   'subdivisions': subdivisions})
                        verts, edges, faces, _ = numpy_data_from_bmesh(bm, self.out_np)
                    finally:
                        bm.free()
            else:
                unit_verts, unit_edges, unit_faces = _unit_icosphere(
                    subdivisions, use_numba, want_edges, want_faces,
                    self.cache_topology)
                if want_verts:
                    if radius == 1.0:
                        # tolist() already copies: avoid an unnecessary array
                        # allocation for Sverchok's default Python-list output.
                        verts = (unit_verts.copy() if self.out_np[0]
                                 else unit_verts.tolist())
                    else:
                        scaled = unit_verts * radius
                        verts = scaled if self.out_np[0] else scaled.tolist()
                else:
                    verts = None
                # Cached arrays must not escape: downstream nodes may mutate.
                edges = ((unit_edges.copy() if self.out_np[1] else unit_edges.tolist())
                         if want_edges else None)
                faces = ((unit_faces.copy() if self.out_np[2] else unit_faces.tolist())
                         if want_faces else None)

            out_verts.append(verts)
            out_edges.append(edges)
            out_faces.append(faces)

        return out_verts, out_edges, out_faces


def register():
    bpy.utils.register_class(SvIcosphereNodeMk2)


def unregister():
    bpy.utils.unregister_class(SvIcosphereNodeMk2)
