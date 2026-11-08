Offset Line Shapely
===================

Functionality
-------------

Offset line using shapely library (GEOS-based). Unlike the native
Offset Line 2D Lite node, this node performs a "true" offset with
self-intersection removal via ``buffer``, producing clean results on
complex topology: collapsing appendices, splitting into components,
holes, self-intersecting input.

Requires **shapely** installed in Blender's Python:

Use developer mode of sverchok and in properties install shapely in bottom

If shapely is not installed, the node is not active


Inputs
------

This node has the following inputs:

- **Verts** - Vertices of objects. Expects an ordered vertices list.
  Only X and Y are used; Z is ignored (2D offset). Accepts a list of
  contours (one path per element).

- **Offset** - Offset distance. For ``Polygon`` end type: positive
  grows the area, negative shrinks it. For ``ClosedLine`` and ``Open*``
  types the sign flips the side of the "capsule".

- **Miter_limit** - Ratio ``miter_length / |offset|``. Used only when
  ``Join Type = Miter``. If the real miter spike is longer than
  ``miter_limit * |offset|``, the corner is clipped (effectively to a
  bevel). Default ``2.0`` (same as Clipper). Clamped to ``1.0`` minimum.

- **Quad_segs** - Segments per quarter circle (90°), controls arc
  smoothness. If ``> 0`` — used directly, ``Arc_tol`` is ignored.
  If ``<= 0`` — computed from ``Arc_tol``. Default ``8`` (shapely
  default, coarse); ``16–32`` gives smooth arcs; ``> 64`` is visually
  indistinguishable from a perfect arc.

- **Arc_tol** - Absolute arc tolerance (in scene units). Used **only**
  when ``Quad_segs <= 0``. Converted to ``quad_segs`` via the sagitta
  formula: ``theta = 2 * acos(1 - arc_tol / |offset|)``,
  ``quad_segs = ceil(pi / theta)``, clamped to ``[1, 512]``.

All parameters except ``Verts`` are optional: if a socket is not
connected, the value comes from the node's property. If connected,
a list is supported (one value per contour; if shorter, ``[0]`` is
reused).


Options
-------

**Join Type** - controls how corners between segments are handled:

- **Miter** - Sharp corners; the miter spike is limited by
  ``Miter_limit``. Shapely ``join_style = 2`` (mitre).

- **Round** - Rounded corners; arcs are tessellated with
  ``Quad_segs`` segments per quadrant. Shapely ``join_style = 1``
  (round).

- **Bevel** - Flat cut of the corner. Shapely ``join_style = 3``
  (bevel).

  .. note::
     ``Bevel`` is **not** an equivalent of Clipper's ``JT_SQUARE``.
     Clipper's ``JT_SQUARE`` produces a 45° cut ("square" corner);
     Shapely's ``bevel`` produces a flat cut. There is no direct
     analogue of ``JT_SQUARE`` in Shapely — ``Bevel`` is the closest
     visually.

**End Type** - controls the topology of the offset result:

- **Polygon** - Offset of an **area**. ``Polygon.buffer(d)``:
  ``d > 0`` grows outward, ``d < 0`` shrinks inward. Output: **all**
  rings (exterior + holes), each **closed**.

- **ClosedLine** - "Capsule" around a **closed** line:
  ``LineString(ring).buffer(d, cap_style=round)``. Output: **all**
  rings of the capsule polygon, **closed**.

- **OpenButt** - "Thick" line with flat caps:
  ``LineString(pts).buffer(d, cap_style=flat)``. Output: a **closed**
  capsule (exterior ring + possible holes).

- **OpenSquare** - Same, square caps (protruding by ``d``):
  ``cap_style=square``.

- **OpenRound** - Same, round caps: ``cap_style=round``.

  .. warning::
     ``Open*`` types produce a **closed capsule**, not a single
     one-sided offset line. ``LineString.buffer`` returns a polygon
     ("thick" line); its boundary is **two** offset lines (left and
     right of the original) plus caps. This is **not** the same as
     Clipper's ``ET_OPENBUTT``, which returns **one** line (offset
     in one direction). Use ``Offset Line 2D Lite`` for a one-sided
     offset, or add a half-edge filter (heuristic by normal, not
     always reliable).


Outputs
-------

This node has the following outputs:

- **Vers** - Result vertices. Each vertex is ``[x, y, 0.0]`` (Z is
  always 0). The output is a **list of lists**: multiple rings/contours
  may be returned if shapely produced a multipolygon, a polygon with
  holes, or several components.

- **Edgs** - Result edges. For closed outputs — a cycle
  ``[i, (i+1) % n]``; for open outputs — a chain ``[i, i+1]``.
  Also a **list of lists**, matching the structure of ``Vers``.


Behaviour Notes
---------------

- **Polygon with negative offset** may produce a ``MultiPolygon`` if
  the shape splits into parts. The node handles **all** polygons:
  every ring (exterior + holes) of every polygon becomes a separate
  contour in the output. This is correct for a "clean" offset.

- **Polygon with negative offset** may produce a polygon **with holes**
  if an inner "island" does not collapse. The hole is emitted as a
  separate closed ring (its winding may be opposite — take this into
  account in downstream processing).

- **Invalid input polygon**: if ``Polygon(ring)`` is not valid
  (self-intersecting, degenerate), the node calls ``buffer(0)`` to
  repair it before applying the offset.

- **quad_segs takes priority** over ``arc_tol``. To control smoothness
  only via ``arc_tol``, set ``Quad_segs = 0``.

- The node does not crash when shapely is missing: it draws an
  ``ERROR`` indicator and returns empty outputs.


Examples of usage
-----------------

.. image:: https://github.com/user-attachments/assets/69a1cba7-c7a5-43ee-bd7f-3bd5ffee3df6