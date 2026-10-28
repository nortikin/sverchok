Nearest Point on Edges
======================

Functionality
-------------

Finds the **exact** closest points on an indexed network of finite segments
(edges) for each query point. Optionally, isolated target vertices are
considered as point targets too. Three modes are available: **Nearest**,
**Nearest in Range**, and **Nearest N**.

Inputs
------

* **Points**: query positions, grouped into objects; required.
* **Target Verts**: target positions, grouped into objects; required.
* **Target Edges**: target vertex-index pairs, indexing **Target Verts**. Optional;
  when unconnected the target consists of loose vertices only.
* **Distance** (Nearest in Range): inclusive maximum distance per query point.
  A single value is used for every point; a list such as ``[[0.5, 1.0, 2.0]]``
  assigns independent limits to successive points. Default: ``1.0``.
* **Count** (Nearest N): number of nearest edges requested per query point.
  A single value is used for every point; a list such as ``[[1, 3, 0]]``
  requests 1, 3, and 0 results respectively. Default: ``3``. Values from
  linked number sockets are truncated to integers; zero gives an empty list.

Only the relevant numeric socket is displayed in each mode. Both numeric
sockets retain their links when the mode changes.

Outputs
-------

* **Distance**: non-negative distance to each matching target.
* **Closest Point**: exact location on the finite segment / loose vertex.
* **Edge Index**: index in **Target Edges**; ``-1`` for a loose vertex or no target.
* **Factor**: parameter along the matching segment (0 at the first endpoint,
  1 at the second endpoint); ``-1`` for loose vertices or no target.

**Nearest** preserves the original one-result-per-point structure. With no
targets, its result is ``inf`` distance, ``[nan, nan, nan]`` location and
``-1`` for index and factor.

**Nearest in Range** and **Nearest N** add one level per input point: each
point has its own list of zero or more matches. For example, the ``Distance``
output of a single object with two query points could be
``[[0.1, 0.3], []]`` (2 hits for the first point, none for the second).
Sverchok object nesting remains above the point level. All outputs use the
same structure; distances are sorted from nearest to farthest, breaking
numerical ties by input edge order. Each **edge** contributes at most one
result, even when multiple edges project onto the same 3D location. Loose
vertices are separate targets when enabled. Missing hits yield ``[]``, not
``inf``.

A flat output is intentionally not offered: keeping a list for each query
point makes it possible to match all four outputs correctly.

Query mode (node body)
----------------------

The mode selector is visible directly on the node, not in the sidebar:

* **Nearest** (default): the nearest point on the whole target network; no
  extra numeric input.
* **Nearest in Range**: all target edges at or below the point's **Distance**
  socket value. An inclusive radius of zero returns exact on-edge hits only.
* **Nearest N**: up to the point's **Count** nearest edges, if they exist.
  Counts of zero return empty hit lists.

**Per-point matching**: the numeric input is matched to the query points within
its object, not to target edges. With *Repeat Last* a shorter list repeats its
last value; *Cycle* wraps around; *Short* limits the number of query points to
match a multi-value list. A single scalar is broadcast to all points in any
mode. On higher nesting levels the lists of controls are matched to entire
point objects using the same *List Match* setting.

Settings (N-panel)
------------------

The sidebar (press ``N`` and select the node) holds the advanced settings:

* **Engine**: Auto, NumPy, Numba. Auto always selects Numba when installed,
  regardless of geometry size, and NumPy otherwise. Numba is optional, and
  its first execution may include a compilation cost.
* **Include Loose Vertices**: include target vertices unused by all edges.
  Connected endpoints are already included through their segments.
* **List Match**: Repeat Last / Cycle / Short, applied recursively to whole
  objects and to pointwise numeric controls. Every point is tested against all
  edges in its matched target object.
* **Output NumPy**: keep NumPy result arrays at the object level.
* **NumPy Block Pairs**: maximum number of point-segment pairs processed in one
  vectorized tile, relevant only when using NumPy.

Examples
--------

Connecting a Circle to a Plane Grid
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/b6a02aa6-b97a-4808-9b1e-6dde23eaa153
   :alt: Circle points connected to their nearest points on plane grid edges
   :align: center

A **Circle** supplies the query ``Points`` (300 vertices in the illustrated
setup). A **Plane** supplies the ``Target Verts`` and ``Target Edges`` (a
4-by-4 grid in the example). For each circle vertex,
**Nearest Point on Edges** finds the closest point **on the grid's edges**, not the closest point on
a plane face.

Other nodes used in this example:

* :doc:`Circle </nodes/generator/circle>`
* :doc:`Plane </nodes/generator/plane_mk3>`
* :doc:`Segment </nodes/generator/segment>`
* :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Connect the nodes as follows:

* ``Circle: Vertices`` -> ``Nearest Point on Edges: Points``.
* ``Plane: Vertices`` -> ``Nearest Point on Edges: Target Verts``.
* ``Plane: Edges`` -> ``Nearest Point on Edges: Target Edges``.
* ``Circle: Vertices`` -> ``Segment: A``.
* ``Nearest Point on Edges: Closest Point`` -> ``Segment: B``.
* ``Segment: Vertices / Edges`` -> a **Viewer Draw** node.

Use separate **Viewer Draw** nodes to display the circle and the plane grid.
The resulting connecting segments visualize the closest-point projection to
the *edge network*: each segment starts on the circle and terminates at its
nearest location on a grid edge. Changing the circle radius, sample count or
grid density changes the projection pattern.

Distance-based Displacement on an Icosphere
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/122eccbc-f1d8-449a-87cc-c131779bdf03
   :alt: Subdivided icosphere displaced along normals by distance to original edges
   :align: center

This example uses a low-resolution **Icosphere** as a reference edge network
and a more densely subdivided copy as the surface to deform. The distance
from each subdivided vertex to the **original** icosphere edges controls a
normal-based displacement.

Other nodes used in this example:

* :doc:`IcoSphere </nodes/generator/icosphere>`
* :doc:`Subdivide </nodes/modifier_change/subdivide_mk2>`
* :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* :doc:`Scalar Math </nodes/number/scalar_mk4>`
* :doc:`Vector Math </nodes/vector/math_mk3>` (Multiply Scalar, Add)
* :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Set up the node tree as follows:

* Connect the original **Icosphere** vertices, edges and faces to
  **Subdivide** to create the denser surface.
* Connect ``Subdivide: Vertices`` to ``Nearest Point on Edges: Points``.
* Connect the **original Icosphere** ``Vertices`` and ``Edges`` to
  ``Nearest Point on Edges: Target Verts`` and ``Target Edges`` respectively.
* Feed the **Subdivide** vertices and faces into **Component Analyzer** in
  *Vertices / Normal* mode to calculate vertex normals.
* Multiply ``Nearest Point on Edges: Distance`` by a scalar with
  **Scalar Math** (*Multiply*; 1.18 in the screenshot).
* Multiply the vertex normals by the scaled distances with **Vector Math**
  (*Multiply Scalar*).
* Add that displacement vector to ``Subdivide: Vertices`` using **Vector
  Math** (*Add*).
* Send the displaced vertices, together with the **Subdivide** edges and
  faces, to **Viewer Draw**.

The resulting surface is displaced more strongly wherever its vertices are
farther from the original icosphere's edges. Points on the reference edges
have zero distance, so they remain fixed by this displacement. This produces
a faceted, embossed relief that follows the low-resolution edge structure.
Adjust the scalar multiplier to control the intensity of the effect; a
negative value inverts the displacement direction.

Nearest in Range: Connecting Line Endpoints to Nearby Edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/2795af8f-b430-4e99-b58f-ac9b76178eec
   :alt: Two line endpoints connected to nearby icosphere edges using Nearest in Range
   :align: center

This example demonstrates how **Nearest in Range** returns *multiple closest
locations per query point*, rather than a single closest point. The two
endpoints of an elevated line are the queries, and the edges of an icosphere
are the targets. Each yellow segment joins one line endpoint to the closest
location on one target edge within the selected radius. The original line is
shown in red, and the reference icosphere in blue.

Other nodes used in this example:

* :doc:`Line </nodes/generator/line_mk4>`
* :doc:`Vector Math </nodes/vector/math_mk3>` (Add)
* :doc:`IcoSphere </nodes/generator/icosphere>`
* :doc:`List Item </nodes/list_struct/item>`
* :doc:`Segment </nodes/generator/segment>`
* :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Build the node tree as follows:

#. Create a **Line** with two vertices. Add a Z-offset with **Vector Math**
   (*Add*) to move the line above the icosphere. Pass the translated vertices
   to ``Points`` and draw the line with **Viewer Draw**.
#. Create an **IcoSphere** and connect its ``Vertices`` and ``Edges`` outputs
   to ``Target Verts`` and ``Target Edges`` respectively. Draw this reference
   mesh with a separate **Viewer Draw**.
#. Set **Nearest Point on Edges** to *Nearest in Range* and choose the
   ``Max Distance`` (about ``4.22`` in the screenshot). Every query endpoint
   receives a list containing all target-edge projections within that
   distance. The two endpoints can have different numbers of hits.
#. Connect the translated line vertices to **two List Item** nodes, both with
   ``Level = 2``. Set their ``Index`` values to ``0`` and ``1`` to isolate
   the first and second endpoint.
#. Connect ``Closest Point`` to **two more List Item** nodes, also at
   ``Level = 2``, using ``Index = 0`` and ``Index = 1``. These select the
   matching *lists of projected locations* for the corresponding endpoints.
#. **Enable Unwrap on the Item output socket of each List Item**, as explained
   below. Connect the selected endpoint to ``Segment: A`` and its matching
   projected locations to ``Segment: B``. Use one **Segment** per endpoint;
   send each segment node's ``Verts`` and ``Edges`` to a separate
   **Viewer Draw**.

The example illustrates that a radius search can return a different number of
results for each point: the pictured setup creates different-sized fans of
connections from the two line endpoints. No result is produced for a point
with no edges within the maximum distance.

Nearest N: Connecting Line Endpoints to a Fixed Number of Edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/b665f924-942c-4e4b-b898-3e78177ea034
   :alt: Two line endpoints connected to their 31 nearest icosphere edges using Nearest N
   :align: center

This example uses almost the same node tree as the range example, but switches
**Nearest Point on Edges** to *Nearest N* and sets ``Count = 31``. For each
query endpoint, the node returns the closest location on each of the 31
nearest **different target edges**, ordered by increasing distance. If fewer
than 31 eligible target edges exist, it returns only the available ones.

Other nodes used in this example:

* :doc:`Line </nodes/generator/line_mk4>`
* :doc:`Vector Math </nodes/vector/math_mk3>` (Add)
* :doc:`IcoSphere </nodes/generator/icosphere>`
* :doc:`List Item </nodes/list_struct/item>`
* :doc:`Segment </nodes/generator/segment>`
* :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

#. Keep the **Line**, its **Vector Math** translation and the **IcoSphere**
   connected exactly as in the preceding example.
#. Select *Nearest N* and set the ``Count`` socket to ``31``. Unlike
   *Nearest in Range*, this mode does **not** use a radius. Provided at least
   31 target edges exist, each query point has 31 results, even when the
   farthest selected edge is relatively distant.
#. Keep the four **List Item** nodes at ``Level = 2``: a pair selects the
   input endpoints at ``Index = 0`` and ``Index = 1``, and another pair
   selects those endpoints' corresponding ``Closest Point`` lists.
#. Keep **Unwrap** enabled on all four ``Item`` output sockets. Connect each
   endpoint and its closest-point list to the respective **Segment** node,
   then display both sets of segments with **Viewer Draw**.

In the illustrated setup, both endpoint fans have 31 segments because the
search requests the same count for both points. The ``Count`` input also
accepts different values per point, if different fan sizes are wanted.

Why List Item needs Unwrap
^^^^^^^^^^^^^^^^^^^^^^^^^^

In *Nearest in Range* and *Nearest N*, **Closest Point** preserves a separate
list of matches for each query point. For one object with two input points,
its structure is conceptually::

    [                            # one Sverchok object
        [                        # the two query points
            [Q00, Q01, ...],    # hits for point 0
            [Q10, Q11, ...],    # hits for point 1
        ]
    ]

Here ``Qij`` denotes an XYZ coordinate. A :doc:`List Item </nodes/list_struct/item>` at ``Level = 2`` with ``Index = 0`` isolates the
first point's matches, but it **keeps an extra surrounding list**::

    [[[Q00, Q01, ...]]]         # List Item's Item output

The output socket's **Unwrap** option removes that *single-item outer list*::

    [[Q00, Q01, ...]]           # after Unwrap: one list of target points

Likewise, selecting the first query point gives ``[[P0]]`` before Unwrap and
``[P0]`` after Unwrap. This makes the selected endpoint and its corresponding
list of target points suitable for the :doc:`Segment </nodes/generator/segment>` node, which connects the source point to every
selected target location by list matching.

**Unwrap is important because it removes the extra level introduced by the
selection, not the level that groups the matches belonging to a query point.**
Without it, the additional nesting can cause **Segment** to interpret the
selected data at the wrong object/list level and produce incorrectly grouped
connections. Do **not** use Flatten as a substitute: Flatten may merge the
matches of different query points and destroy their correspondence.

To enable it, open the output-socket options menu on the ``Item`` socket of
**each** of the four **List Item** nodes, and select **Unwrap**. It is a
**socket setting**, not the ``Level`` or ``Index`` setting of List Item.
Unwrap works here because each List Item selects one outer item. It would
not apply unchanged to an output containing multiple outer items.

Notes
-----

The algorithm always measures distance to the **finite segment**, not its
infinite supporting line. Zero-length edges are supported. Ties are resolved
in favor of the first edge in input order; loose vertices follow all edges.
Out-of-range vertex indices raise a ValueError.

Both engines use exhaustive comparisons, with O(P * E) geometric work.
For **Nearest N**, Numba allocates exactly the requested slots per point (up
to the number of available targets), rather than using the largest Count for
every point. For **Nearest in Range**, Numba uses a two-pass method to
allocate only the number of hits found. The range result's size can be large
when nearly all edges match every point. No SciPy approximation or BVH is used.
