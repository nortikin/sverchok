Merge by Distance
=================

Functionality
-------------

Merge vertices within a distance threshold and rebuild the mesh topology.
The default **GRID** implementation is based on NumPy and does not use BMesh.
It supports separate edge and polygon inputs, masked welding, arbitrary
per-element data, and optional provenance (the indices of all source elements
that contributed to an output element).

The node is compact by default. Enable **Mesh Data** on the node to show the
attribute inputs and outputs and the origin-index outputs. Turning it off
hides *unlinked* data sockets; already linked sockets remain visible and their
links are preserved. The ``Mesh Data`` switch changes visibility, not the
welding algorithm.

For previously saved node trees, the historical BMesh implementation retains
its original node ID and is available through the legacy-node mechanism. The
new implementation uses a different node ID.

Inputs
------

The inputs appear in the following order:

#. **Vertices**: Vertex coordinates, as lists or NumPy arrays.
#. **Edges**: Optional explicit ``[start, end]`` vertex-index pairs. Supports
   loose edges and edges alongside polygons. This input is also the source
   of **EdgeData** and **Edge Init Index** mappings.
#. **Polygons**: Optional polygon vertex-index loops (triangles, quads or
   n-gons). For compatibility with the original mesh operation, edge pairs
   can be supplied here in edge-only mode, though **Edges** is recommended.
#. **Verts Mask**: Optional mask selecting vertices eligible for welding.
   With no mask, all vertices are eligible. Unselected vertices are not
   merged into selected groups. If the mask is shorter than the vertex list,
   the last mask value is repeated.
#. **Distance**: Maximum weld distance; one scalar per mesh (not one radius
   per vertex). Default: ``0.001``.
#. **VertData**: Optional arbitrary data, one item per input vertex.
#. **EdgeData**: Optional arbitrary data, one item per explicit input edge.
#. **FaceData**: Optional arbitrary data, one item per input polygon.

**VertData**, **EdgeData**, and **FaceData** are hidden initially. They become
visible when **Mesh Data** is enabled, or remain visible if already linked.
Short attribute lists yield ``None`` for output elements whose selected source
index is not present in the corresponding list.

Outputs
-------

The outputs appear in the following order:

#. **Vertices**: Surviving vertex coordinates.
#. **Edges**: Deduplicated output edges from the polygon perimeters and/or
   the explicit **Edges** input, without collapsed zero-length edges.
#. **Polygons**: Retained polygon loops after vertex remapping; collapsed
   polygons and exact duplicate loops are removed. Duplicate detection is
   independent of starting vertex and winding order.
#. **Doubles**: Coordinates of vertices removed by the weld.
#. **Mask**: Input vertex mask reduced to the surviving vertices. If no input
   mask is supplied, the output is empty.
#. **VertData**: Data from the first source vertex of each surviving group.
#. **EdgeData**: Data from the first explicitly indexed source edge that
   contributes to each output edge; ``None`` if no such source exists.
#. **FaceData**: Data from the first retained source polygon of each output
   polygon, when face data is supplied.
#. **Vert Init Index**: All original vertex indices contributing to each
   output vertex.
#. **Edge Init Index**: All original explicit edge indices contributing to
   each output edge.
#. **Face Init Index**: All original polygon indices contributing to each
   output polygon.

The last six outputs are hidden by default and shown by **Mesh Data**.
Origin-index outputs are **nested Python lists**, with one list per resulting
mesh element. They record *all* contributing source indices rather than a
single representative index.

Example: input vertices ``0``, ``2`` and ``5`` may become one output vertex
whose **Vert Init Index** entry is ``[0, 2, 5]``. If input edges ``14`` and
``24`` become one output edge, its **Edge Init Index** entry is
``[14, 24]``. For each data output, the value of the first source element is
kept: arbitrary data is not averaged or combined.

When an edge is generated only from a polygon boundary, with no matching
explicit edge in **Edges**, its **Edge Init Index** entry is ``[]`` and its
**EdgeData** value is ``None``. The node does **not** fabricate edge origins
from polygon indices. In the legacy edge-only **Polygons** mode, those edge
pairs are used as edge origins if **Edges** is not connected.

Parameters and interface
------------------------

**Node body**

* **Mesh Data** (off by default): Show or hide the optional data and
  provenance sockets. Connected sockets remain visible when switched off.

**N-panel and right-click menu**

* **Implementation**: **GRID** (default, portable) or **BMesh (Legacy)**
  (original Blender-based algorithm).
* **List Match**: **Repeat Last** (default), **Cycle**, or **Short** for
  matching collections of meshes and per-mesh inputs. Arbitrarily nested
  groups of meshes are supported.
* **Mesh Data**: The same visibility control as on the node body.
* **NumPy outputs**: Seven independent switches, in output order:
  **Vertices**, **Edges**, **Doubles**, **Mask**, **VertData**,
  **EdgeData**, and **FaceData**. All are off by default.

**Polygons** and the three **Init Index** outputs remain Python lists, even
when NumPy outputs are enabled. For irregular attribute payloads, the NumPy
conversion may produce an object array.

BMesh (Legacy) in the new node supports the original polygon/edge input
behavior, vertex mask, distance, and face data. The separate **Edges** input,
**VertData**, **EdgeData**, and multiple origin-index outputs require **GRID**.
The node reports an error if unsupported features are requested in legacy
mode; it does not invent index mappings.

Notes and limitations
---------------------

* The GRID implementation prioritizes speed and deterministic grouping. It
  is not guaranteed to produce the same vertex representative, indices or
  topology ordering as BMesh for all inputs.
* A very large **Distance** can collapse or distort faces. Although the node
  removes exact duplicate and degenerate topological loops, it is **not** a
  general geometric-overlap or self-intersection repair tool. Some partially
  overlapping faces may remain.
* Distance and vertex coordinates must be finite; distance cannot be
  negative. Topology indices must refer to existing vertices.
* Data and origin tracking are calculated on demand when their outputs are
  used. Leaving these outputs unlinked avoids their extra processing cost.
* GRID does not require an installed SciPy or Numba accelerator: a portable
  fallback is available. Optional accelerators may improve performance on
  larger datasets.

Examples of usage
-----------------

**Weld duplicates and inspect where they came from.** Connect the input
vertices to **Vertices**, the face loops to **Polygons**, and optionally
explicit edges to **Edges**. Enable **Mesh Data** and inspect **Vert Init
Index** to see which source vertices collapsed into each output vertex.
Connect **VertData**, **EdgeData**, or **FaceData** when attribute propagation
is needed.

**Join adjacent panels.** Concatenate panel geometry, then pass the combined
mesh through Merge by Distance. The resulting shared boundary vertices are
welded. If attributes are provided, the first source element supplies the
retained data, and the **Init Index** outputs record the other contributors.

**Selective weld.** Supply a **Verts Mask** to weld only eligible vertices;
other vertices remain independent. Multiple meshes and corresponding
per-mesh distances can be supplied as nested lists using **List Match**.

The following illustrations were made with an earlier version of the node.
They remain examples of the welding operation, but the **current socket
names and ordering are those documented above**.

.. image:: https://user-images.githubusercontent.com/14288520/199113153-05fa7f2d-8ddb-4308-9a9b-ebb20e16f980.png
   :target: https://user-images.githubusercontent.com/14288520/199113153-05fa7f2d-8ddb-4308-9a9b-ebb20e16f980.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199118735-68850597-cf13-439a-a0fa-221d104ce55a.png
   :target: https://user-images.githubusercontent.com/14288520/199118735-68850597-cf13-439a-a0fa-221d104ce55a.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199118461-f9ce665f-e012-4b72-ba1d-e5c0af6bc165.png
   :target: https://user-images.githubusercontent.com/14288520/199118461-f9ce665f-e012-4b72-ba1d-e5c0af6bc165.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199121377-5085556a-483f-422a-87ed-dea854ac8ec6.png
   :target: https://user-images.githubusercontent.com/14288520/199121377-5085556a-483f-422a-87ed-dea854ac8ec6.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Analyzers-> :doc:`Proportional Edit Falloff </nodes/analyzer/proportional>`
* Modifiers->Modifier Change-> :doc:`Smooth Vertices </nodes/modifier_change/smooth>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Lerp </nodes/vector/lerp>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/199122167-9458221d-5946-443b-9801-095806253764.gif
   :target: https://user-images.githubusercontent.com/14288520/199122167-9458221d-5946-443b-9801-095806253764.gif
