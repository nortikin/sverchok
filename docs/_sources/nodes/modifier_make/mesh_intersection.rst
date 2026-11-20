Mesh Intersection
=================

Functionality
-------------

**Mesh Intersection** computes the geometrical intersections of two surface
meshes, without modifying either input mesh. It can be used to build section
curves, measure contact geometry, and provide intersection lines for subsequent
modelling operations. Unlike :doc:`Cut by Mesh </nodes/modifier_make/cut_by_mesh>`,
it does **not** insert edges into the source mesh.

Both open and closed surface meshes are accepted. Triangle, quad and simple
n-gon faces are triangulated internally. Coplanar contacts and overlapping
areas are also detected.

The numerical kernel uses NumPy. SciPy accelerates candidate searching when
available and Numba is used automatically when installed. It does not import
``bmesh``, ``mathutils`` or ``bpy``. The node UI uses Blender as usual.

Inputs
------

* **Vertices A**: Coordinates of the first mesh.
* **Faces A**: Face vertex-index lists of the first mesh.
* **Vertices Cutter**: Coordinates of the second mesh.
* **Faces Cutter**: Face vertex-index lists of the second mesh.

Inputs are paired by Sverchok's repeat-last list matching. Mesh objects should
be expressed in the same coordinate system.

Parameters
----------

The node displays **Advanced Outputs** as a toggle. When it is off, only
``Vertices`` and ``Edges`` are shown. Linked advanced sockets are kept by
Sverchok's ``hide_safe`` behavior.

In the node's N-panel:

* **Search / Auto** (default): SciPy ``cKDTree`` if available, otherwise the
  built-in NumPy BVH.
* **Search / SciPy**: Force the SciPy search; requires SciPy installed.
* **Search / NumPy**: Force the NumPy AABB BVH.
* **Search / Brute Force**: Exhaustive AABB candidate filtering for comparison
  and diagnosis, not recommended for large meshes.
* **Coplanar**: Include coplanar overlap polygons and coplanar contacts.
* **Tolerance**: Absolute tolerance in scene coordinate units (default
  ``1e-6``). Set this to match your mesh scale.

Numba automatically accelerates the triangle-pair narrow-phase when installed.
Its first invocation may include JIT compilation time.

The **Output NumPy** option in the N-panel has separate toggles for
**Vertices** and **Edges**. By default both outputs are Python lists.
When enabled, each mesh object uses a contiguous-shaped NumPy array
of vertex coordinates (``N x 3``) or edge indices (``M x 2``).
This avoids list conversion when passing geometry between compatible nodes.
Other outputs retain their original formats.

Outputs
-------

* **Vertices**: Shared coordinates of intersection vertices.
* **Edges**: Pairs of indices into **Vertices** defining intersection segments.

When **Advanced Outputs** is enabled:

* **Point Indices**: Indices into **Vertices** for isolated point contacts.
* **Coplanar Polygons**: Vertex-index loops of overlapping coplanar triangles;
  multiple polygons can correspond to one original n-gon.
* **Edge Face Pairs**: ``[face_a, face_b]`` for each **Edges** segment.
* **Point Face Pairs**: Source face pairs for isolated point contacts.
* **Coplanar Face Pairs**: Source face pairs for coplanar overlap polygons.

Face indices refer to the original (pre-triangulation) faces. Duplicated
intersection segments are welded; in that case the first source face pair is
retained. Intersection edges are not necessarily ordered as a polyline.

Examples
--------

.. sverchok-illustrated-examples:start

The following example intersects a deformed plane with an IcoSphere.
The plane (mesh A) is generated on a grid, rotated with **Matrix In**, and
perturbed by **Randomize** in the Z direction. The IcoSphere is supplied as
the cutter mesh. In this example, **Mesh Intersection** returns only the
intersection **Vertices** and **Edges**; neither input mesh is altered.

.. image:: https://github.com/user-attachments/assets/4ea9ed9b-3fef-4712-9904-54b5feebd33e
   :target: https://github.com/user-attachments/assets/4ea9ed9b-3fef-4712-9904-54b5feebd33e
   :alt: Mesh Intersection node tree with a randomized, rotated plane, an IcoSphere and the intersection curves in the 3D viewport.

The screenshot uses a centered **4 x 4** plane with **6 x 6** vertices,
``Randomize`` with Z amplitude ``0.36``, and an IcoSphere with radius ``1``
and subdivision level ``3``. The highlighted curves mark where the two
surfaces cross. Viewing both input meshes alongside the intersection lines
makes the contact geometry easier to understand.

A change in the plane's orientation or displacement changes the extracted
curves without modifying the geometry of either mesh. The returned edges
are not guaranteed to form one ordered or closed polyline; for continuous
paths, apply a suitable edge-to-path operation afterwards.

A separate introductory tree, ``Mesh_Intersection_and_Cut_by_Mesh.json``,
is provided under ``json_examples/Introduction/`` and compares this node
with :doc:`Cut by Mesh </nodes/modifier_make/cut_by_mesh>`.

.. sverchok-illustrated-examples:end

See also
--------

* :doc:`Cut by Mesh </nodes/modifier_make/cut_by_mesh>`
* :doc:`Bisect </nodes/modifier_make/bisect>`
* :doc:`Cut Object by Surface </nodes/modifier_make/cut_object_by_surface>`
