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
Requires:  pip install manifold3d

Notes
-----
* Manifold expects *manifold* (watertight, correctly oriented) triangle
  meshes.  Non-manifold, open or self-intersecting geometry will usually
  produce an empty result or raise.
* Input polygons are triangulated with a simple fan when they have more
  than three vertices.  For better triangulation of concave / non-planar
  faces feed already-triangulated meshes.
* When "Allow Ngons" is enabled the triangulated result is post-processed
  with bmesh.ops.dissolve_limit so that coplanar adjacent faces are merged
  back into n-gons.
"""

import sys
import math
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


def _to_triangles(faces):
    """Fan-triangulate a list of polygons.  Returns list of 3-tuples."""
    tris = []
    for f in faces:
        if len(f) < 3:
            continue
        if len(f) == 3:
            tris.append(tuple(f))
        else:
            # simple fan – works for convex faces
            v0 = f[0]
            for i in range(1, len(f) - 1):
                tris.append((v0, f[i], f[i + 1]))
    return tris


def mesh_to_manifold(verts, faces):
    """
    Convert Sverchok verts / faces (lists) into a manifold3d.Manifold.
    Faces are triangulated if necessary.
    """
    if not verts or not faces:
        return Manifold()

    verts_np = np.asarray(verts, dtype=np.float32)
    if verts_np.ndim != 2 or verts_np.shape[1] < 3:
        raise ValueError("Vertices must be an (N, 3+) array")

    # Keep only xyz
    verts_np = verts_np[:, :3]

    tris = _to_triangles(faces)
    if not tris:
        return Manifold()

    faces_np = np.asarray(tris, dtype=np.uint32)

    mesh = Mesh(
        vert_properties=verts_np,
        tri_verts=faces_np,
    )
    return Manifold(mesh)


def manifold_to_mesh(manifold):
    """
    Convert a manifold3d.Manifold back to Sverchok-style lists
    (verts list-of-lists, faces list-of-lists).
    """
    if manifold.is_empty():
        return [], []

    out = manifold.to_mesh()
    # vert_properties may contain extra channels; take only xyz
    verts = out.vert_properties[:, :3].tolist()
    faces = out.tri_verts.tolist()
    return verts, faces


def dissolve_coplanar(verts, faces, angle_limit_deg=0.1):
    """
    Merge adjacent coplanar faces into n-gons using bmesh limited dissolve.
    angle_limit_deg : maximum angle (in degrees) between face normals that
                      are still considered coplanar.
    """
    if not faces:
        return verts, faces

    bm = bmesh_from_pydata(verts, [], faces, normal_update=True)

    # Limited Dissolve – merges coplanar faces and cleans collinear edges
    bmesh.ops.dissolve_limit(
        bm,
        angle_limit=math.radians(angle_limit_deg),
        use_dissolve_boundaries=False,
        verts=bm.verts,
        edges=bm.edges,
        delimit={'NORMAL'},          # only dissolve when normals match
    )

    # Optional: also remove any remaining degenerate geometry
    bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=bm.edges)

    new_verts, _, new_faces = pydata_from_bmesh(bm)
    bm.free()
    return new_verts, new_faces


def boolean_manifold(VA, PA, VB, PB, operation, allow_ngons=False, angle_limit=0.1):
    """
    Perform a single Boolean operation with manifold3d.

    Parameters
    ----------
    VA, PA : verts / polys of mesh A
    VB, PB : verts / polys of mesh B
    operation : 'ITX' | 'JOIN' | 'DIFF'
    allow_ngons : if True, post-process with limited dissolve
    angle_limit : angle threshold in degrees for coplanar test

    Returns
    -------
    (verts, faces) of the resulting mesh
    """
    if not MANIFOLD_AVAILABLE:
        raise RuntimeError(
            "manifold3d is not installed. In BlenderPython console run:\n"
            ">>> from sverchok.utils.pip_utils import install_package\n"
            ">>> install_package(\"manifold3d\")\n"
        )

    a = mesh_to_manifold(VA, PA)
    b = mesh_to_manifold(VB, PB)

    if operation == 'ITX':
        result = a ^ b          # intersection
    elif operation == 'JOIN':
        result = a + b          # union
    elif operation == 'DIFF':
        result = a - b          # difference
    else:
        raise ValueError(f"Unknown operation: {operation}")

    verts, faces = manifold_to_mesh(result)

    if allow_ngons and faces:
        verts, faces = dissolve_coplanar(verts, faces, angle_limit_deg=angle_limit)

    return verts, faces


class SvManifoldBooleanNode(ModifierLiteNode, SverchCustomTreeNode, bpy.types.Node):
    """Boolean node powered by the manifold3d library"""
    bl_idname = 'SvManifoldBooleanNode'
    bl_label = 'Manifold Boolean'
    bl_icon = 'MOD_BOOLEAN'

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
        description="After the boolean, merge adjacent coplanar faces into n-gons (Limited Dissolve)",
        default=True,
        update=updateNode,
    )

    angle_limit: FloatProperty(
        name="Angle Limit",
        description="Maximum angle (degrees) between face normals that are still considered coplanar",
        default=0.1,
        min=0.0,
        max=5.0,
        precision=3,
        update=updateNode,
    )

    def update_mode(self, context):
        self.inputs['Verts A'].hide_safe = self.nest_objs
        self.inputs['Polys A'].hide_safe = self.nest_objs
        self.inputs['Verts B'].hide_safe = self.nest_objs
        self.inputs['Polys B'].hide_safe = self.nest_objs
        self.inputs['Verts Nested'].hide_safe = not self.nest_objs
        self.inputs['Polys Nested'].hide_safe = not self.nest_objs
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
        self.inputs.new('SvVerticesSocket', 'Verts A')
        self.inputs.new('SvStringsSocket',  'Polys A')
        self.inputs.new('SvVerticesSocket', 'Verts B')
        self.inputs.new('SvStringsSocket',  'Polys B')
        self.inputs.new('SvVerticesSocket', 'Verts Nested').hide_safe = True
        self.inputs.new('SvStringsSocket',  'Polys Nested').hide_safe = True
        self.outputs.new('SvVerticesSocket', 'Vertices')
        self.outputs.new('SvStringsSocket', 'Polygons')

    @property
    def sv_internal_links(self):
        if self.nest_objs:
            return [
                (self.inputs['Verts Nested'], self.outputs[0]),
                (self.inputs['Polys Nested'], self.outputs[1]),
            ]
        return super().sv_internal_links

    def draw_buttons(self, context, layout):
        if not MANIFOLD_AVAILABLE:
            layout.label(text="manifold3d not found!", icon='ERROR')
            layout.label(text="pip install manifold3d")
            return

        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)

        col = layout.column(align=True)
        col.prop(self, "nest_objs", toggle=True)
        if self.nest_objs:
            col.prop(self, "out_last", toggle=True)

        col.separator()
        col.prop(self, "allow_ngons", toggle=True)
        if self.allow_ngons:
            col.prop(self, "angle_limit")

    def process(self):
        OutV, OutP = self.outputs
        if not OutV.is_linked:
            return

        if not MANIFOLD_AVAILABLE:
            # keep sockets empty rather than crash the tree
            OutV.sv_set([])
            if OutP.is_linked:
                OutP.sv_set([])
            return

        VertA, PolA, VertB, PolB, VertN, PolN = self.inputs
        SMode = self.selected_mode
        allow_ngons = self.allow_ngons
        angle_limit = self.angle_limit
        out = []

        # Raise recursion limit only while we are chaining many nested ops
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
                    ))
            else:
                vnest = VertN.sv_get(default=[[]])
                pnest = PolN.sv_get(default=[[]])
                if len(vnest) < 2:
                    OutV.sv_set([])
                    if OutP.is_linked:
                        OutP.sv_set([])
                    return

                First = boolean_manifold(
                    vnest[0], pnest[0], vnest[1], pnest[1], SMode,
                    allow_ngons=allow_ngons,
                    angle_limit=angle_limit,
                )
                if not self.out_last:
                    out.append(First)
                    for i in range(2, len(vnest)):
                        out.append(boolean_manifold(
                            First[0], First[1], vnest[i], pnest[i], SMode,
                            allow_ngons=allow_ngons,
                            angle_limit=angle_limit,
                        ))
                        First = out[-1]
                else:
                    for i in range(2, len(vnest)):
                        First = boolean_manifold(
                            First[0], First[1], vnest[i], pnest[i], SMode,
                            allow_ngons=allow_ngons,
                            angle_limit=angle_limit,
                        )
                    out.append(First)
        finally:
            sys.setrecursionlimit(recursionlimit)

        OutV.sv_set([i[0] for i in out])
        if OutP.is_linked:
            OutP.sv_set([i[1] for i in out])


def register():
    bpy.utils.register_class(SvManifoldBooleanNode)


def unregister():
    bpy.utils.unregister_class(SvManifoldBooleanNode)