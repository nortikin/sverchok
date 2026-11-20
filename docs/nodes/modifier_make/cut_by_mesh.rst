Cut by Mesh
===========

Functionality
-------------

**Cut by Mesh** inserts the intersection curves of surface mesh B into the
actual topology of mesh A. It reconstructs the source faces along the intersection and can disconnect
and separate the resulting pieces. Source polygons are preserved by default,
including quads and simple n-gons, when valid reconstruction is possible. The cutter
can be an open surface (for example, a plane) or a closed mesh.

This is a **surface knife**, not a Boolean volume difference: it never adds
cap faces. Mesh B is only a cutting tool, not part of the output. In Split and
Separate modes, seams are disconnected, including open slits which do not
separate the input into multiple connected components.

The geometry core is independent of ``bpy``, ``bmesh`` and ``mathutils``. It
uses NumPy, optional SciPy ``cKDTree`` for searching, and optional automatic
Numba acceleration for the triangle-pair intersection stage. The topology
reconstruction stage is implemented in Python/NumPy.

Inputs
------

* **Vertices A**: Mesh to be cut, expressed as XYZ coordinates.
* **Faces A**: Triangles, quads or simple n-gons of mesh A, using vertex indices.
* **Vertices Cutter**: Coordinates of the cutting surface.
* **Faces Cutter**: Cutting surface faces, using vertex indices.

Both meshes must use the same coordinate system. An edges-only cutter is not
supported; mesh B must contain faces.

Parameters
----------

The main node has these controls:

* **Mode / Cut** (default): Insert edges while preserving shared vertices
  across both sides of the cut (original behavior).
* **Mode / Split**: Duplicate seam vertices/edges to disconnect the cut.
  All surviving regions remain in one SV mesh object as loose parts.
* **Mode / Separate**: Each topological face-region becomes a distinct
  Sverchok mesh object in the output lists.
* **Keep / All** (default): Retain both sides of the intersection.
* **Keep / Positive, Negative**: Keep the half-space corresponding to the
  oriented normal of a **planar**, consistently oriented mesh B. Only
  available in Split and Separate modes. This is the closest equivalent to
  Bisect's inner/outer removal.
* **Keep / Inside, Outside**: Keep regions inside/outside a **closed, oriented,
  manifold** cutter B, using winding numbers. Ambiguous contact or incomplete
  cuts raise an error.
* **Keep / Largest, Smallest**: Select a region by surface area, even with
  curved or open cutting surfaces.
* **Keep / Index**: Select one region by its 0-based rank in decreasing area
  order. Index is used *before* filtering.
* **Advanced Outputs**: Toggle on the node; by default only ``Vertices``,
  ``Edges``, ``Faces`` and ``Cut Edges Mask`` are visible.

In the N-panel:

* **Search / Auto** (default): Choose SciPy if installed, otherwise NumPy BVH.
* **Search / SciPy**: Force SciPy broad-phase searching.
* **Search / NumPy**: Force the NumPy BVH.
* **Search / Brute Force**: Exhaustive AABB candidate scanning (for testing).
* **Coplanar**: Trace the per-triangle boundaries of coplanar overlapping
  regions. Complicated coplanar configurations can require local triangles.
* **Preserve Polygons** (default enabled): Merge triangles created internally
  by the cutter into valid planar faces from the original mesh. It never
  dissolves a cut edge or an original face boundary. Disable to see the
  triangle-only result for debugging. This also reconstructs polygon patches
  inside originally triangular faces (for example, an IcoSphere), removing
  unnecessary internal diagonals without crossing the original face boundaries.
* **Tolerance**: Absolute coordinate tolerance (default ``1e-6``).

Numba runs automatically when available, and can incur one-time JIT
compilation cost. It does not accelerate the Python topology reconstruction.

The **Output NumPy** option in the N-panel has separate toggles for
**Vertices** and **Edges**. By default both outputs are Python lists.
When enabled, each mesh object uses a contiguous-shaped NumPy array
of vertex coordinates (``N x 3``) or edge indices (``M x 2``).
This avoids list conversion when passing geometry between compatible nodes.
Other outputs retain their original formats.

Outputs
-------

* **Vertices**: Coordinates of the reconstructed A mesh. In Cut mode,
  original vertex indices appear first. In Split and Separate modes, vertices
  are remapped and can be duplicated at seams.
* **Edges**: Unique edges of the reconstructed mesh, including cut edges.
* **Faces**: Original polygons where possible, subdivided by intersection
  constraints. A quad bisected by a straight line can become two quads.
  Complex arrangements (holes, internal slits, degenerate geometry or
  non-planar source polygons) can retain local triangles.
  In Separate mode, each output item is a different mesh object. If filtering
  removes every region, the output object list is empty.
* **Cut Edges Mask**: One Boolean per output edge; ``True`` for an edge
  introduced or traced by a cutter-surface intersection (not for ordinary
  supporting triangulation edges).

When **Advanced Outputs** is enabled:

* **Cut Vertices Mask**: One Boolean per output vertex. Includes cut edge
  endpoints and newly inserted vertices.
* **Face Origins**: For each output face, the original A-face index.
* **Intersection Vertices**: Intersection-only coordinates from the shared
  intersection core; these are **not** indexed into the main ``Vertices``.
* **Intersection Edges**: Indices into **Intersection Vertices**.

Algorithm
---------

#. Triangulate the input meshes internally, keeping the original A-face IDs.
#. Intersect triangle pairs using spatial broad-phase filtering and exact
   triangle-pair tests within the configured floating-point tolerance.
#. Clip the resulting segments to each triangle of A, intersect segments
   locally in 2D and propagate boundary split points to adjacent A triangles.
#. Rebuild triangle faces by adding points and recovering the cut constraints
   through edge flips. Weld shared generated vertices across A triangles.
#. If Preserve Polygons is enabled, dissolve temporary triangle edges
   inside the same planar original polygon, respecting intersection constraints
   and original face boundaries. Simplify redundant collinear cut vertices
   without creating T-junctions.
#. Mark recovered intersection edges; in Split/Separate, disconnect the seam
   using per-vertex face fans and identify regions via non-cut face adjacency.
#. Apply Keep filtering and return a single loose-parts mesh or separate meshes.

Limitations
-----------

* Isolated point-only tangencies do not modify the cut mesh; use Mesh
  Intersection to inspect those contacts. Real intersection segments remain
  in the recovered mesh topology.
* This is a first implementation of a topological cutter, **not** a robust
  exact-predicate Boolean engine. Nearly coincident or degenerate surfaces,
  non-manifold meshes and self-intersecting n-gons can trigger an explicit
  exception rather than silently creating an invalid mesh.
* For non-planar n-gons, triangulation defines the piecewise planar surface.
* Some complex cuts retain local triangles: for example a closed intersection
  loop that creates a hole inside a single original polygon cannot be stored
  as one ordinary Sverchok face. Original n-gons with non-planar vertices
  are not forcibly dissolved after cutting.
* It does not create cap faces. Open cuts, including partially embedded
  slits, do not necessarily produce multiple connected regions.
* Positive/Negative is **only** defined for a planar cutter with consistent
  orientation; for arbitrary curved/open cutters use Largest/Smallest/Index.
* Inside/Outside requires a watertight, consistently oriented cutter B.
  Its winding-number checks classify all remaining face centers and can
  therefore cost more than the other Keep modes on large closed cutters.
* Topologically disconnected components are sorted by decreasing surface
  area, not by spatial side. If pieces have equal area, their index may change
  when the input triangulation changes.
* Classification of a single region that straddles the cutter is ambiguous
  and raises instead of quietly discarding incorrect geometry.
* A coplanar overlap is traced along the per-triangle intersection rims;
  local triangles can remain visible where simple polygon recovery fails.
* All computations use floating point and require a scale-appropriate
  tolerance. Meshes with duplicate vertices or severe degeneracies deserve
  careful checking before 3D printing.

Examples
--------

.. sverchok-illustrated-examples:start

This example uses an IcoSphere to cut a large planar face. The plane is
mesh A, while the IcoSphere is connected to **Vertices Cutter** and
**Faces Cutter**. Unlike Mesh Intersection, **Cut by Mesh** reconstructs
the topology of the plane along the closed intersection loop.

.. image:: https://github.com/user-attachments/assets/cc1c52c0-76cb-4c17-89bd-f5ac80f2be65
   :target: https://github.com/user-attachments/assets/cc1c52c0-76cb-4c17-89bd-f5ac80f2be65
   :alt: Cut by Mesh using a large plane and an IcoSphere, with Separate and Keep Largest showing a planar mesh with a hole.

In the screenshot, the centered plane measures **10 x 10**, and the
IcoSphere has radius ``2.38`` and subdivision level ``1``. The node uses
**Mode: Separate** and **Keep: Largest**: it separates the pieces along
the intersection and retains the one with the greatest surface area. In
this setup, that is the outer part of the plane, leaving a hole bounded
by the sphere-plane intersection. The IcoSphere is visible through a
separate **Viewer Draw** for reference, but is not included in the cut
output.

**Preserve Polygons** retains source faces where possible. However, a
single ordinary Sverchok polygon cannot contain an interior hole, so
this result necessarily uses multiple faces and may include supporting
triangles extending from the opening to the outer boundary. These are
part of the planar mesh topology, not additional cut surfaces.

**Keep: Largest** selects by surface area, not by the concepts of
inside/outside. For a closed, consistently oriented cutter, the
**Inside** and **Outside** options are more appropriate when those regions
must be selected explicitly. The node does not create cap faces.

The introductory example ``Mesh_Intersection_and_Cut_by_Mesh.json`` in
``json_examples/Introduction/`` provides another comparison of the two
nodes.

.. sverchok-illustrated-examples:end

See also
--------

* :doc:`Mesh Intersection </nodes/modifier_make/mesh_intersection>`
* :doc:`Bisect </nodes/modifier_make/bisect>`
* :doc:`Cut Object by Surface </nodes/modifier_make/cut_object_by_surface>`

Known case: a planar cutter passing exactly through existing mesh A edges
(e.g. a plane tilted 45 degrees through opposite cube corners) is handled
without adding spurious diagonals. Those already-existing edges are included
in ``Cut Edges Mask`` and Split / Keep side classification.

Near-coincident cuts may still produce degenerate constrained triangulations;
very small deviations from an exact corner crossing can need further work.
