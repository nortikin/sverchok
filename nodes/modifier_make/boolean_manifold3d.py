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

"""
Boolean operations using manifold3d

Requires:  pip install manifold3d
(or from Blender's Python console:
    from sverchok.utils.pip_utils import install_package
    install_package("manifold3d")
) (restart required for now)

Features
--------
* Intersect / Union / Difference
* Nested accumulate mode
* Optional n-gon reconstruction (Limited Dissolve on coplanar faces)
* Optional origin tracking:
    - Face Origins : 0 = came from mesh A, 1 = came from mesh B
    - Cut Edges    : edges that lie on the Boolean intersection

Verts A --+
Polys A --+
          +--> Manifold Boolean --> Vertices
Verts B --+                     --> Polygons
Polys B --+                     +-> Face Origins   (0 = A, 1 = B)
                                +-> Cut Edges      (intersection curves)

"""

import sys
import math
from collections import defaultdict

import numpy as np

import bpy
import bmesh
from bpy.props import EnumProperty, BoolProperty, FloatProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_cycle as mlr
from sverchok.utils.nodes_mixins.sockets_config import ModifierLiteNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

try:
    from manifold3d import Manifold, Mesh
    MANIFOLD_AVAILABLE = True
except ImportError:
    MANIFOLD_AVAILABLE = False
    Manifold = None
    Mesh = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_triangles(faces):
    """Fan-triangulate a list of polygons. Returns list of 3-tuples."""
    tris = []
    for f in faces:
        if len(f) < 3:
            continue
        if len(f) == 3:
            tris.append(tuple(f))
        else:
            v0 = f[0]
            for i in range(1, len(f) - 1):
                tris.append((v0, f[i], f[i + 1]))
    return tris


def mesh_to_manifold(verts, faces, make_original=False):
    """
    Convert Sverchok verts/faces into a manifold3d.Manifold.
    When make_original=True the manifold receives a unique OriginalID
    so that provenance can be tracked through Boolean operations.
    """
    if not verts or not faces:
        return Manifold()

    verts_np = np.asarray(verts, dtype=np.float32)
    if verts_np.ndim != 2 or verts_np.shape[1] < 3:
        raise ValueError("Vertices must be an (N, 3+) array")
    verts_np = verts_np[:, :3]

    tris = _to_triangles(faces)
    if not tris:
        return Manifold()

    faces_np = np.asarray(tris, dtype=np.uint32)
    mesh = Mesh(vert_properties=verts_np, tri_verts=faces_np)
    m = Manifold(mesh)
    if make_original:
        m = m.as_original()
    return m


def manifold_to_mesh(manifold):
    """Plain conversion (no origin data)."""
    if manifold.is_empty():
        return [], []
    out = manifold.to_mesh()
    verts = out.vert_properties[:, :3].tolist()
    faces = out.tri_verts.tolist()
    return verts, faces


def manifold_to_mesh_with_origins(manifold):
    """
    Returns verts, faces, face_origins
    face_origins[i] = OriginalID of the input mesh that produced faces[i]
    """
    if manifold.is_empty():
        return [], [], []

    out = manifold.to_mesh()
    verts = out.vert_properties[:, :3].tolist()
    faces = out.tri_verts.tolist()

    face_origins = [-1] * len(faces)
    run_ids = list(getattr(out, "run_original_id", []))
    run_index = list(getattr(out, "run_index", []))

    if run_ids and run_index:
        # Ensure run_index is one longer than run_ids
        if len(run_index) == len(run_ids):
            run_index = run_index + [len(faces) * 3]
        for i, oid in enumerate(run_ids):
            start = run_index[i] // 3
            end = run_index[i + 1] // 3
            for t in range(start, min(end, len(face_origins))):
                face_origins[t] = int(oid)

    return verts, faces, face_origins


def find_cut_edges(faces, face_origins):
    """
    An edge is a cut edge when the two faces that share it have
    different origin IDs. Returns list of [v0, v1] with v0 < v1.
    """
    edge_to_faces = defaultdict(list)

    for fi, f in enumerate(faces):
        n = len(f)
        for i in range(n):
            a, b = f[i], f[(i + 1) % n]
            edge = (min(a, b), max(a, b))
            edge_to_faces[edge].append(fi)

    cut = []
    for edge, flist in edge_to_faces.items():
        if len(flist) == 2:
            o0 = face_origins[flist[0]]
            o1 = face_origins[flist[1]]
            if o0 != o1 and o0 >= 0 and o1 >= 0:
                cut.append(list(edge))
    return cut


def dissolve_coplanar(verts, faces, angle_limit_deg=0.1):
    """Classic limited-dissolve (no origin awareness)."""
    if not faces:
        return verts, faces

    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)
    bmesh.ops.dissolve_limit(
        bm,
        angle_limit=math.radians(angle_limit_deg),
        use_dissolve_boundaries=False,
        verts=bm.verts,
        edges=bm.edges,
        delimit={"NORMAL"},
    )
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)
    new_verts, _, new_faces = pydata_from_bmesh(bm)
    bm.free()
    return new_verts, new_faces


def dissolve_coplanar_same_origin(verts, faces, face_origins, angle_limit_deg=0.1):
    """
    Limited-dissolve that only merges faces sharing the same origin ID.
    Preserves a meaningful Face Origins list after n-gon creation.
    """
    if not faces:
        return verts, faces, face_origins

    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)

    # Store origin on each face
    origin_layer = bm.faces.layers.int.new("origin")
    for i, f in enumerate(bm.faces):
        f[origin_layer] = face_origins[i] if i < len(face_origins) else -1

    # Collect edges that can be dissolved (same origin + nearly coplanar)
    edges_to_dissolve = []
    angle_limit = math.radians(angle_limit_deg)
    for e in bm.edges:
        if e.is_manifold and len(e.link_faces) == 2:
            f0, f1 = e.link_faces
            if (f0[origin_layer] == f1[origin_layer] and
                    f0[origin_layer] >= 0 and
                    f0.normal.angle(f1.normal) < angle_limit):
                edges_to_dissolve.append(e)

    if edges_to_dissolve:
        bmesh.ops.dissolve_edges(bm, edges=edges_to_dissolve, use_verts=True)

    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)

    new_verts, _, new_faces = pydata_from_bmesh(bm)
    new_origins = [f[origin_layer] for f in bm.faces]
    bm.free()
    return new_verts, new_faces, new_origins


# ---------------------------------------------------------------------------
# Boolean entry point
# ---------------------------------------------------------------------------

def boolean_manifold(VA, PA, VB, PB, operation,
                     allow_ngons=False, angle_limit=0.1,
                     track_origins=False):
    """
    Returns
    -------
    When track_origins is False:
        (verts, faces, None, None)
    When track_origins is True:
        (verts, faces, face_origins, cut_edges)
        face_origins : list[int]  0 = mesh A, 1 = mesh B
        cut_edges    : list[[v0, v1]]
    """
    if not MANIFOLD_AVAILABLE:
        raise RuntimeError(
            "manifold3d is not installed.\n"
            "In Blender's Python console run:\n"
            ">>> from sverchok.utils.pip_utils import install_package\n"
            ">>> install_package(\"manifold3d\")"
        )

    a = mesh_to_manifold(VA, PA, make_original=track_origins)
    b = mesh_to_manifold(VB, PB, make_original=track_origins)

    id_a = a.original_id() if track_origins else -1
    id_b = b.original_id() if track_origins else -1

    if operation == "ITX":
        result = a ^ b
    elif operation == "JOIN":
        result = a + b
    elif operation == "DIFF":
        result = a - b
    else:
        raise ValueError(f"Unknown operation: {operation}")

    if not track_origins:
        verts, faces = manifold_to_mesh(result)
        if allow_ngons and faces:
            verts, faces = dissolve_coplanar(verts, faces, angle_limit_deg=angle_limit)
        return verts, faces, None, None

    # --- with origin tracking ---
    verts, faces, face_origins = manifold_to_mesh_with_origins(result)

    # Map real OriginalIDs → convenient 0 / 1
    origin_map = {id_a: 0, id_b: 1}
    face_origins = [origin_map.get(oid, -1) for oid in face_origins]

    if allow_ngons and faces:
        verts, faces, face_origins = dissolve_coplanar_same_origin(
            verts, faces, face_origins, angle_limit_deg=angle_limit
        )

    cut_edges = find_cut_edges(faces, face_origins)
    return verts, faces, face_origins, cut_edges


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class SvManifoldBooleanNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    """Boolean node powered by the manifold3d library"""
    bl_idname = "SvManifoldBooleanNode"
    bl_label = "Manifold Boolean"
    bl_icon = "MOD_BOOLEAN"

    mode_options = [
        ("ITX", "Intersect", "", 0),
        ("JOIN", "Union", "", 1),
        ("DIFF", "Difference", "", 2),
    ]

    selected_mode: EnumProperty(
        items=mode_options,
        description="Boolean operation",
        default="ITX",
        update=updateNode,
    )

    allow_ngons: BoolProperty(
        name="Allow Ngons",
        description="After the boolean, merge adjacent coplanar faces into n-gons",
        default=True,
        update=updateNode,
    )

    angle_limit: FloatProperty(
        name="Angle Limit",
        description="Maximum angle (degrees) between face normals still considered coplanar",
        default=0.1,
        min=0.0,
        max=5.0,
        precision=3,
        update=updateNode,
    )

    track_origins: BoolProperty(
        name="Track Origins",
        description="Output which input each face came from (0=A, 1=B) and the cut edges",
        default=False,
        update=updateNode,
    )

    def update_mode(self, context):
        self.inputs["Verts A"].hide_safe = self.nest_objs
        self.inputs["Polys A"].hide_safe = self.nest_objs
        self.inputs["Verts B"].hide_safe = self.nest_objs
        self.inputs["Polys B"].hide_safe = self.nest_objs
        self.inputs["Verts Nested"].hide_safe = not self.nest_objs
        self.inputs["Polys Nested"].hide_safe = not self.nest_objs
        updateNode(self, context)

    nest_objs: BoolProperty(
        name="Accumulate Nested",
        description="Boolean the first two objects, then apply subsequent booleans to the result one by one",
        default=False,
        update=update_mode,
    )

    out_last: BoolProperty(
        name="Only Final Result",
        description="Output only the final iteration result",
        default=True,
        update=update_mode,
    )

    def sv_init(self, context):
        self.inputs.new("SvVerticesSocket", "Verts A")
        self.inputs.new("SvStringsSocket", "Polys A")
        self.inputs.new("SvVerticesSocket", "Verts B")
        self.inputs.new("SvStringsSocket", "Polys B")
        self.inputs.new("SvVerticesSocket", "Verts Nested").hide_safe = True
        self.inputs.new("SvStringsSocket", "Polys Nested").hide_safe = True

        self.outputs.new("SvVerticesSocket", "Vertices")
        self.outputs.new("SvStringsSocket", "Polygons")
        self.outputs.new("SvStringsSocket", "Face Origins")
        self.outputs.new("SvStringsSocket", "Cut Edges")

    @property
    def sv_internal_links(self):
        if self.nest_objs:
            return [
                (self.inputs["Verts Nested"], self.outputs[0]),
                (self.inputs["Polys Nested"], self.outputs[1]),
            ]
        return super().sv_internal_links

    def draw_buttons(self, context, layout):
        if not MANIFOLD_AVAILABLE:
            layout.label(text="manifold3d not found!", icon="ERROR")
            layout.label(text="pip install manifold3d")
            return

        row = layout.row()
        row.prop(self, "selected_mode", expand=True)

        col = layout.column(align=True)
        col.prop(self, "nest_objs", toggle=True)
        if self.nest_objs:
            col.prop(self, "out_last", toggle=True)

        col.separator()
        col.prop(self, "allow_ngons", toggle=True)
        if self.allow_ngons:
            col.prop(self, "angle_limit")

        col.separator()
        col.prop(self, "track_origins", toggle=True)

    def process(self):
        OutV = self.outputs["Vertices"]
        OutP = self.outputs["Polygons"]
        OutOrig = self.outputs["Face Origins"]
        OutCut = self.outputs["Cut Edges"]

        if not OutV.is_linked:
            return

        if not MANIFOLD_AVAILABLE:
            OutV.sv_set([])
            if OutP.is_linked:
                OutP.sv_set([])
            if OutOrig.is_linked:
                OutOrig.sv_set([])
            if OutCut.is_linked:
                OutCut.sv_set([])
            return

        VertA, PolA, VertB, PolB, VertN, PolN = self.inputs
        SMode = self.selected_mode
        allow_ngons = self.allow_ngons
        angle_limit = self.angle_limit
        track = self.track_origins
        out = []

        recursionlimit = sys.getrecursionlimit()
        sys.setrecursionlimit(10000)

        try:
            if not self.nest_objs:
                for v1, p1, v2, p2 in zip(*mlr([
                    VertA.sv_get(default=[[]]),
                    PolA.sv_get(default=[[]]),
                    VertB.sv_get(default=[[]]),
                    PolB.sv_get(default=[[]]),
                ])):
                    out.append(boolean_manifold(
                        v1, p1, v2, p2, SMode,
                        allow_ngons=allow_ngons,
                        angle_limit=angle_limit,
                        track_origins=track,
                    ))
            else:
                vnest = VertN.sv_get(default=[[]])
                pnest = PolN.sv_get(default=[[]])
                if len(vnest) < 2:
                    OutV.sv_set([])
                    if OutP.is_linked:
                        OutP.sv_set([])
                    if OutOrig.is_linked:
                        OutOrig.sv_set([])
                    if OutCut.is_linked:
                        OutCut.sv_set([])
                    return

                First = boolean_manifold(
                    vnest[0], pnest[0], vnest[1], pnest[1], SMode,
                    allow_ngons=allow_ngons,
                    angle_limit=angle_limit,
                    track_origins=track,
                )
                if not self.out_last:
                    out.append(First)
                    for i in range(2, len(vnest)):
                        out.append(boolean_manifold(
                            First[0], First[1], vnest[i], pnest[i], SMode,
                            allow_ngons=allow_ngons,
                            angle_limit=angle_limit,
                            track_origins=track,
                        ))
                        First = out[-1]
                else:
                    for i in range(2, len(vnest)):
                        First = boolean_manifold(
                            First[0], First[1], vnest[i], pnest[i], SMode,
                            allow_ngons=allow_ngons,
                            angle_limit=angle_limit,
                            track_origins=track,
                        )
                    out.append(First)
        finally:
            sys.setrecursionlimit(recursionlimit)

        OutV.sv_set([i[0] for i in out])
        if OutP.is_linked:
            OutP.sv_set([i[1] for i in out])
        if OutOrig.is_linked:
            OutOrig.sv_set([i[2] if i[2] is not None else [] for i in out])
        if OutCut.is_linked:
            OutCut.sv_set([i[3] if i[3] is not None else [] for i in out])


def register():
    bpy.utils.register_class(SvManifoldBooleanNode)


def unregister():
    bpy.utils.unregister_class(SvManifoldBooleanNode)